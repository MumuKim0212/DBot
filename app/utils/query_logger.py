import json
import logging
import logging.handlers
from datetime import datetime, UTC
from pathlib import Path


class QueryLogger:
    def __init__(self, log_path: str | None = None):
        if log_path is None:
            log_path = str(Path(__file__).parent.parent / "logs" / "query_log.jsonl")

        log_file = Path(log_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        self._logger = logging.getLogger("query_logger")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

        if not self._logger.handlers:
            handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5,
                encoding="utf-8",
            )
            handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(handler)

    def log(self, query: str, selected_tables: list, sql: str, status: str = "ok", error: str | None = None, result_count: int | None = None):
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "query": query,
            "tables": [t["name"] for t in selected_tables],
            "sql": sql,
            "status": status,
        }
        if result_count is not None:
            log_entry["result_count"] = result_count
        if error is not None:
            log_entry["error"] = error

        self._logger.info(json.dumps(log_entry, ensure_ascii=False))
