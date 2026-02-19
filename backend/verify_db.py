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
        print("=" * 60)
        print("🗄️  실시간 데이터베이스 상태")
        print("=" * 60)
        
        # 라인 데이터
        cur.execute("SELECT COUNT(*) FROM line")
        line_count = cur.fetchone()[0]
        print(f"\n📍 Line Count: {line_count}")
        
        # 라인 상태 데이터
        cur.execute("SELECT COUNT(*) FROM line_status")
        line_status_count = cur.fetchone()[0]
        print(f"🟢 Line Status Count: {line_status_count}")
        
        # KPI 데이터
        cur.execute("SELECT COUNT(*) FROM kpi_report")
        kpi_count = cur.fetchone()[0]
        print(f"📊 KPI Report Count: {kpi_count}")
        
        # KPI 최근 데이터 샘플
        if kpi_count > 0:
            cur.execute("""
                SELECT kpi_id, line_id, center_id, throughput_count, window_end 
                FROM kpi_report 
                ORDER BY window_end DESC 
                LIMIT 3
            """)
            print("   최근 KPI 샘플:")
            for row in cur.fetchall():
                print(f"     - Line {row[1]}: {row[3]} units @ {row[4]}")
        
        # 병목 데이터
        cur.execute("SELECT COUNT(*) FROM bottleneck_event")
        bn_count = cur.fetchone()[0]
        print(f"\n🚫 Bottleneck Event Count: {bn_count}")
        
        # 병목 최근 데이터 샘플
        if bn_count > 0:
            cur.execute("""
                SELECT bottleneck_id, line_id, cause_code, duration_sec, occurred_at 
                FROM bottleneck_event 
                ORDER BY occurred_at DESC 
                LIMIT 3
            """)
            print("   최근 Bottleneck 샘플:")
            for row in cur.fetchall():
                print(f"     - ID {row[0]}: Line {row[1]} ({row[2]}) - {row[3]}sec @ {row[4]}")
        
        # 센서 이벤트 데이터
        cur.execute("SELECT COUNT(*) FROM sensor_event")
        sensor_count = cur.fetchone()[0]
        print(f"\n📡 Sensor Event Count: {sensor_count}")
        
        # 센터 데이터
        cur.execute("SELECT COUNT(*) FROM center")
        center_count = cur.fetchone()[0]
        print(f"\n🏢 Center Count: {center_count}")
        
        cur.execute("SELECT center_id, name FROM center LIMIT 3")
        print("   센터 샘플:")
        for row in cur.fetchall():
            print(f"     - {row[0]}: {row[1]}")
        
        print("\n" + "=" * 60)
        print(f"✅ 모든 데이터는 로컬 PostgreSQL에서 실시간 조회됨")
        print(f"Connection: {main_url.split('@')[1] if '@' in main_url else main_url}")
        print("=" * 60)
        
finally:
    conn.close()
