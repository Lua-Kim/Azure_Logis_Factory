import os
from dotenv import load_dotenv
import psycopg2
from datetime import datetime, timedelta
import random

env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

main_url = os.getenv('AZ_POSTGRE_DATABASE_URL')
conn = psycopg2.connect(main_url)

try:
    with conn.cursor() as cur:
        # 모든 라인에 대해 KPI 데이터 생성
        cur.execute("SELECT line_id, center_id, name FROM line")
        lines = cur.fetchall()
        
        inserted = 0
        for line_id, center_id, line_name in lines:
            # 각 라인에 대해 과거 12시간의 KPI 데이터 생성
            for hour_offset in range(12):
                window_end = datetime.utcnow() - timedelta(hours=hour_offset)
                throughput = random.randint(80, 420)
                
                cur.execute(
                    """
                    INSERT INTO kpi_report 
                        (window_end, center_id, line_id, throughput_count, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (window_end, center_id, line_id, throughput, datetime.utcnow())
                )
                inserted += 1
        
        conn.commit()
        print(f"KPI 데이터 {inserted}개 생성 완료")
        
        # 확인
        cur.execute("SELECT COUNT(*) FROM kpi_report")
        count = cur.fetchone()[0]
        print(f"현재 KPI Report 총합: {count}개")
        
finally:
    conn.close()
