import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
conn = psycopg2.connect(os.getenv('AZ_POSTGRE_DATABASE_URL'))
cur = conn.cursor()

# 테이블 구조 확인
cur.execute("SELECT * FROM bottleneck_event LIMIT 1")
print('=== 병목 테이블 컬럼 ===')
for desc in cur.description:
    print(desc[0])

print('\n=== 현재 병목 데이터 ===')
cur.execute('SELECT * FROM bottleneck_event ORDER BY bottleneck_id LIMIT 10')
for row in cur.fetchall():
    print(row)

# 라인 정보 확인
print('\n=== 라인 정보 ===')
cur.execute('SELECT line_id, name FROM line')
for line_id, name in cur.fetchall():
    print(f"{line_id}: {name}")

cur.close()
conn.close()
