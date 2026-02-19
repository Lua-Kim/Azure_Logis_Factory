import os
from dotenv import load_dotenv
import psycopg2
from datetime import datetime, timedelta

load_dotenv()
conn = psycopg2.connect(os.getenv('AZ_POSTGRE_DATABASE_URL'))
cur = conn.cursor()

# 테이블 구조 확인
cur.execute("SELECT * FROM bottleneck_event LIMIT 1")
print('=== 병목 테이블 컬럼 ===')
cols = [desc[0] for desc in cur.description]
print(cols)

print('\n=== 현재 병목 데이터 ===')
cur.execute('SELECT * FROM bottleneck_event ORDER BY bottleneck_id LIMIT 10')
for row in cur.fetchall():
    print(row)

conn.close()
