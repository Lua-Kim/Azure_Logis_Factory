import os
from dotenv import load_dotenv
import psycopg2

env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

main_url = os.getenv('AZ_POSTGRE_DATABASE_URL')
conn = psycopg2.connect(main_url)

try:
    with conn.cursor() as cur:
        # KPI 데이터 개수
        cur.execute("SELECT COUNT(*) FROM kpi_report")
        kpi_count = cur.fetchone()[0]
        print(f"KPI Report Count: {kpi_count}")
        
        if kpi_count > 0:
            cur.execute("SELECT kpi_id, window_end, center_id, line_id, throughput_count FROM kpi_report LIMIT 5")
            for row in cur.fetchall():
                print(f"  {row}")
        
        # Bottleneck 데이터 개수
        cur.execute("SELECT COUNT(*) FROM bottleneck_event")
        bn_count = cur.fetchone()[0]
        print(f"\nBottleneck Event Count: {bn_count}")
        
        # Line Status 데이터 개수
        cur.execute("SELECT COUNT(*) FROM line_status")
        ls_count = cur.fetchone()[0]
        print(f"Line Status Count: {ls_count}")
        
        if ls_count > 0:
            cur.execute("SELECT line_id, current_status FROM line_status LIMIT 5")
            for row in cur.fetchall():
                print(f"  {row}")
finally:
    conn.close()
