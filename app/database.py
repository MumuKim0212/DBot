import json
import os
import threading
from contextlib import contextmanager
from mysql.connector.pooling import MySQLConnectionPool
from dotenv import load_dotenv

load_dotenv()

_REQUIRED_ENV = ["MYSQL_HOST", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DB"]
_missing_env = [v for v in _REQUIRED_ENV if not os.getenv(v)]
if _missing_env and not os.getenv("DB_SERVERS"):
    raise RuntimeError(f"Missing required environment variables: {', '.join(_missing_env)}")

_pools: dict[str, MySQLConnectionPool] = {}
_pools_lock = threading.Lock()

def get_servers_config():
    servers_env = os.getenv("DB_SERVERS")
    if servers_env:
        return json.loads(servers_env)
    return {
        "default": {
            "name": "기본 서버",
            "host": os.getenv("MYSQL_HOST"),
            "port": int(os.getenv("MYSQL_PORT", "3306")),
            "user": os.getenv("MYSQL_USER"),
            "password": os.getenv("MYSQL_PASSWORD"),
            "db": os.getenv("MYSQL_DB"),
        }
    }

def _get_pool(server_id: str) -> MySQLConnectionPool:
    if server_id not in _pools:
        with _pools_lock:
            if server_id not in _pools:
                servers = get_servers_config()
                if server_id not in servers:
                    raise ValueError(f"Unknown server ID: {server_id}")
                
                config = servers[server_id]
                _pools[server_id] = MySQLConnectionPool(
                    pool_name=f"dbpool_{server_id}",
                    pool_size=5,
                    host=config.get("host"),
                    port=int(config.get("port", 3306)),
                    user=config.get("user"),
                    password=config.get("password"),
                    database=config.get("db"),
                    connection_timeout=10,
                    pool_reset_session=True,
                )
    return _pools[server_id]

@contextmanager
def get_db_connection(server_id: str):
    conn = _get_pool(server_id).get_connection()
    try:
        yield conn
    finally:
        conn.close()
