import json
import logging
import os
import re
import threading
from contextlib import contextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool
from app.core.schema_to_prompt import build_schema_text
from app.core.prompt_builder import build_sql_prompt
from app.core.selector import TableSelector
from app.core.selector_utils import expand_with_relations
from app.core.gate import GateChecker
from app.core.visualizer import Visualizer
from app.utils.query_logger import QueryLogger
from app.database import get_db_connection, get_servers_config

logging.basicConfig(level=logging.INFO)

app = FastAPI()

_DATA_DIR = Path(__file__).parent / "data"

selector = TableSelector(
    str(_DATA_DIR / "schema_full.json"),
    str(_DATA_DIR / "schema_index.json"),
    str(_DATA_DIR / "table_embeddings.json")
)

gate_checker = GateChecker(str(_DATA_DIR / "metrics_dictionary.json"))
visualizer = Visualizer()

logger = QueryLogger()

from llm import get_llm
llm = get_llm()



@app.get("/servers")
def get_servers_api():
    servers = get_servers_config()
    return [{"id": k, "name": v.get("name", k)} for k, v in servers.items()]


def clean_sql(raw_sql: str) -> str:
    sql = re.sub(r"```sql|```", "", raw_sql, flags=re.IGNORECASE)
    sql = sql.strip()
    if not sql:
        raise ValueError("LLM returned empty SQL")
    
    if sql.count(";") >= 2:
        raise ValueError("Multiple queries detected (>= 2 semicolons)")
        
    sql = sql.split(";")[0].strip()
    if not sql:
        raise ValueError("LLM returned empty SQL")
        
    if not re.search(r'\bLIMIT\b', sql, re.IGNORECASE):
        sql += " LIMIT 100"
    
    sql += ";"
    return sql


def _strip_strings_and_comments(sql: str) -> str:
    sql = re.sub(r"'[^']*'", "''", sql)
    sql = re.sub(r'"[^"]*"', '""', sql)
    sql = re.sub(r"--[^\n]*", " ", sql)
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    return sql


def validate_sql(sql: str):
    cleaned = _strip_strings_and_comments(sql)
    stripped = cleaned.lstrip()
    if not re.match(r"SELECT\b", stripped, re.IGNORECASE):
        raise ValueError("Unsafe SQL detected: only SELECT queries are allowed")

    upper = cleaned.upper()
    forbidden = [
        r"\bDELETE\b", r"\bUPDATE\b", r"\bINSERT\b", r"\bDROP\b", r"\bTRUNCATE\b",
        r"\bALTER\b", r"\bCREATE\b", r"\bRENAME\b", r"\bREPLACE\b",
        r"\bEXEC\b", r"\bCALL\b",
        r"\bINTO\s+OUTFILE\b", r"\bINTO\s+DUMPFILE\b", r"\bLOAD\s+DATA\b",
    ]
    for pattern in forbidden:
        if re.search(pattern, upper):
            keyword = pattern.replace(r"\b", "").replace(r"\s+", " ").strip()
            raise ValueError(f"Unsafe SQL detected: {keyword}")


from app.core.session_manager import session_manager

def prepare_schema(user_query: str, session_id: str = None) -> tuple[str, list]:
    selected = selector.select(user_query)
    
    # Session fallback: If current query doesn't match any table (e.g. "show top 5"), use tables from previous turn
    if not selected and session_id:
        ctx = session_manager.get_context(session_id)
        if ctx.get("last_tables"):
            selected = ctx["last_tables"]
            
    if not selected:
        raise ValueError("No matching tables found for the given query")
    selected = expand_with_relations(selected, selector.schema_full)

    selected_names = {t["name"] for t in selected}
    filtered_relations = [
        r for r in selector.schema_full.get("relations", [])
        if r["from_table"] in selected_names and r["to_table"] in selected_names
    ]
    schema_for_llm = {
        "tables": selected,
        "relations": filtered_relations,
    }

    schema_text = build_schema_text(schema_for_llm)
    return schema_text, selected


_MAX_RESULT_ROWS = 100


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    session_id: str | None = Field(None, description="Optional session ID for multi-turn chat")
    server_id: str = Field("default", description="Server ID to run the query on")


from app.core.rule_engine import rule_engine

@app.post("/query")
def run_query(req: QueryRequest):
    # 0. Gate Check (Ambiguity & Required Params)
    gate_res = gate_checker.check_query(req.query)
    if gate_res.get("status") == "INCOMPLETE":
        raise HTTPException(status_code=400, detail={"error": gate_res.get("message", "질문이 너무 모호합니다."), "code": "INCOMPLETE_QUERY"})

    selected = []
    sql = ""
    try:
        # 1. Rule-based Engine (Early Return)
        rule_match = rule_engine.match(req.query)
        if rule_match:
            sql, selected = rule_match
            with get_db_connection(req.server_id) as conn:
                cursor = conn.cursor(dictionary=True, buffered=True)
                try:
                    cursor.execute(sql)
                    result = cursor.fetchmany(_MAX_RESULT_ROWS)
                finally:
                    cursor.close()
            
            if req.session_id:
                session_manager.update_context(req.session_id, req.query, sql, selected)
                
            logger.log(req.query, selected, sql, status="rule", result_count=len(result))
            
            columns = list(result[0].keys()) if result else []
            chart_config = visualizer.generate_chart_config(req.query, columns)
            
            return {"sql": sql, "result": result, "chart_config": chart_config}

        # 2. LLM Pipeline
        schema_text, selected = prepare_schema(req.query, req.session_id)

        ctx = session_manager.get_context(req.session_id) if req.session_id else {"history": []}
        history = ctx["history"]

        MAX_RETRIES = 2
        previous_sql = None
        last_error = None
        result = None

        for attempt in range(MAX_RETRIES + 1):
            prompt = build_sql_prompt(schema_text, req.query, previous_sql, last_error, history)
            
            try:
                raw_sql = llm.generate(prompt)
            except Exception as e:
                raise RuntimeError(f"LLM error: {e}") from e

            sql = clean_sql(raw_sql)
            
            try:
                validate_sql(sql)
            except ValueError:
                # Unsafe SQL -> Do not retry, raise immediately
                raise

            try:
                with get_db_connection(req.server_id) as conn:
                    cursor = conn.cursor(dictionary=True, buffered=True)
                    try:
                        cursor.execute(sql)
                        result = cursor.fetchmany(_MAX_RESULT_ROWS)
                    finally:
                        cursor.close()
                    break # Success!
            except mysql.connector.Error as db_err:
                last_error = str(db_err)
                previous_sql = sql
                if attempt < MAX_RETRIES:
                    logger.log(req.query, selected, sql, status="retry", error=f"Retry {attempt+1}: {last_error}")
                else:
                    raise RuntimeError(f"Failed after {MAX_RETRIES} retries. Last error: {last_error}")

        if req.session_id:
            session_manager.update_context(req.session_id, req.query, sql, selected)

        logger.log(req.query, selected, sql, status="ok", result_count=len(result))
        
        columns = list(result[0].keys()) if result else []
        chart_config = visualizer.generate_chart_config(req.query, columns)
        
        return {"sql": sql, "result": result, "chart_config": chart_config}

    except ValueError as e:
        msg = str(e)
        if "Unsafe SQL" in msg:
            code = "UNSAFE_SQL"
        elif "No matching tables" in msg:
            code = "NO_MATCHING_TABLES"
        else:
            code = "INVALID_REQUEST"
        if code != "UNSAFE_SQL":
            logger.log(req.query, selected, sql, status="error", error=msg)
        raise HTTPException(status_code=400, detail={"error": msg, "code": code})
    except RuntimeError as e:
        msg = str(e)
        logger.log(req.query, selected, sql, status="error", error=msg)
        raise HTTPException(status_code=502, detail={"error": msg, "code": "LLM_ERROR"})
    except Exception as e:
        msg = str(e)
        logger.log(req.query, selected, sql, status="error", error=msg)
        raise HTTPException(status_code=500, detail={"error": msg, "code": "INTERNAL_ERROR"})

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

@app.get("/")
def read_root():
    return FileResponse(FRONTEND_DIR / "DBot.html")

app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="static")
