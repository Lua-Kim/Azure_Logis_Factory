import os
import psycopg2
from dotenv import load_dotenv

# .env 파일 로드
env_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(env_path)

DB_URL = os.getenv('AZ_POSTGRE_DATABASE_URL')

ALTER_LINE_TABLE = """
ALTER TABLE line
    ADD COLUMN IF NOT EXISTS rail_length_m DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS section_count INT;
"""


def alter_tables():
    conn = None
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()

        print("테이블 변경을 시작합니다...")
        cur.execute(ALTER_LINE_TABLE)

        conn.commit()
        print("✅ 테이블 변경이 완료되었습니다.")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    alter_tables()
