import os
from dotenv import load_dotenv
import psycopg2
from datetime import datetime

env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

main_url = os.getenv('AZ_POSTGRE_DATABASE_URL')
conn = psycopg2.connect(main_url)

try:
    with conn.cursor() as cur:
        # 현재 시간
        print(f"Current UTC time: {datetime.utcnow()}")
        
        # KPI 데이터의 window_end 시간 범위 확인
        cur.execute("""
            SELECT 
                MIN(window_end) as min_time,
                MAX(window_end) as max_time,
                COUNT(*) as count
            FROM kpi_report
        """)
        min_time, max_time, count = cur.fetchone()
        print(f"\nKPI Report Stats:")
        print(f"  Count: {count}")
        print(f"  Min window_end: {min_time}")
        print(f"  Max window_end: {max_time}")
        
        # 5분 이내 데이터 확인
        cur.execute("""
            SELECT COUNT(*) FROM kpi_report 
            WHERE window_end >= NOW() - INTERVAL '5 minutes'
        """)
        recent_5m = cur.fetchone()[0]
        print(f"  In last 5 minutes: {recent_5m}")
        
        # 12시간 이내 데이터 확인
        cur.execute("""
            SELECT COUNT(*) FROM kpi_report 
            WHERE window_end >= NOW() - INTERVAL '12 hours'
        """)
        recent_12h = cur.fetchone()[0]
        print(f"  In last 12 hours: {recent_12h}")
finally:
    conn.close()
