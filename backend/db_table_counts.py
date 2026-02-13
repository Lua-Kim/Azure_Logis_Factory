import os
from dotenv import load_dotenv
import psycopg2

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

DB_URL = os.getenv("AZ_POSTGRE_DATABASE_URL")
if not DB_URL:
    raise SystemExit("AZ_POSTGRE_DATABASE_URL not set")

conn = psycopg2.connect(DB_URL)
try:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
            """
        )
        tables = [row[0] for row in cur.fetchall()]
        print("table\trows")
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM public.{table}")
            count = cur.fetchone()[0]
            print(f"{table}\t{count}")
finally:
    conn.close()
