import json
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DB"),
    )


# =========================
# 1. 테이블 목록
# =========================
def get_tables(cursor, db_name):
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s
    """, (db_name,))
    return [row[0] for row in cursor.fetchall()]


# =========================
# 2. 컬럼 정보
# =========================
def get_columns(cursor, db_name, table):
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
    """, (db_name, table))

    columns = []
    for name, dtype in cursor.fetchall():
        col = {
            "name": name,
            "type": dtype,
            "role": infer_role(name),
        }

        # measure면 aggregation 추가
        if col["role"] == "measure":
            col["aggregation"] = infer_aggregation(name)

        columns.append(col)

    return columns


# =========================
# 3. PK 추출 → grain
# =========================
def get_primary_keys(cursor, db_name, table):
    cursor.execute("""
        SELECT column_name
        FROM information_schema.key_column_usage
        WHERE table_schema = %s
          AND table_name = %s
          AND constraint_name = 'PRIMARY'
    """, (db_name, table))

    return [row[0] for row in cursor.fetchall()]


# =========================
# 4. FK → relations
# =========================
def get_relations(cursor, db_name):
    cursor.execute("""
        SELECT
            table_name,
            column_name,
            referenced_table_name,
            referenced_column_name
        FROM information_schema.key_column_usage
        WHERE table_schema = %s
          AND referenced_table_name IS NOT NULL
    """, (db_name,))

    relations = []

    for row in cursor.fetchall():
        from_table, from_col, to_table, to_col = row

        relations.append({
            "from_table": from_table,
            "to_table": to_table,
            "on": [[from_col, to_col]],
            "type": "many-to-one"
        })

    return relations


# =========================
# 5. 룰 기반 추론
# =========================
def infer_role(col_name: str) -> str:
    col_name = col_name.lower()

    if col_name.endswith("_id") or col_name in ["id", "idx"]:
        return "dimension"

    if any(k in col_name for k in ["count", "amount", "price", "damage", "total"]):
        return "measure"

    return "dimension"


def infer_aggregation(col_name: str) -> str:
    col_name = col_name.lower()

    if "count" in col_name:
        return "COUNT"

    if any(k in col_name for k in ["amount", "price", "damage", "total"]):
        return "SUM"

    return "SUM"


# =========================
# 6. 메인 생성
# =========================
def extract_schema(db_name: str):
    conn = get_connection()
    cursor = conn.cursor()

    tables = get_tables(cursor, db_name)

    schema = {
        "tables": [],
        "relations": get_relations(cursor, db_name)
    }

    for table in tables:
        columns = get_columns(cursor, db_name, table)
        pk = get_primary_keys(cursor, db_name, table)

        table_obj = {
            "name": table,
            "description": "",
            "semantic": {
                "grain": pk,
                "level": "detail" if len(pk) == 1 else "aggregate"
            },
            "columns": columns
        }

        schema["tables"].append(table_obj)

    cursor.close()
    conn.close()

    return schema


# =========================
# 7. 저장
# =========================
def save_schema(schema, path="schema.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    db_name = "w01_gamedb"

    schema = extract_schema(db_name)
    save_schema(schema)

    print("schema.json 생성 완료")