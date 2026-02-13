import os
from dotenv import load_dotenv
from psycopg2.pool import SimpleConnectionPool

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

DB_URL = os.getenv("AZ_POSTGRE_DATABASE_URL")

_pool = None


def init_pool(minconn: int = 1, maxconn: int = 5) -> None:
    global _pool
    if _pool is not None:
        return
    if not DB_URL:
        raise RuntimeError("AZ_POSTGRE_DATABASE_URL is not set")
    _pool = SimpleConnectionPool(minconn, maxconn, DB_URL)


def get_conn():
    if _pool is None:
        init_pool()
    return _pool.getconn()


def put_conn(conn) -> None:
    if _pool is None:
        return
    _pool.putconn(conn)


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None
