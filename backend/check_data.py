import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

main_url = os.getenv('AZ_POSTGRE_DATABASE_URL')
print(f"Main DB URL: {main_url.split('@')[1] if '@' in main_url else main_url}")

engine = create_engine(main_url)
with engine.connect() as conn:
    # 센터 확인
    centers = conn.execute(text("SELECT center_id, name FROM center LIMIT 5;"))
    print("\n=== Centers ===")
    for row in centers:
        print(f"  ID: {row[0]}, Name: {row[1]}")
    
    # KPI 데이터 확인
    kpis = conn.execute(text("SELECT COUNT(*) FROM kpi_report;"))
    count = kpis.scalar()
    print(f"\n=== KPI Report Count: {count} ===")
    
    if count > 0:
        kpi_data = conn.execute(text("SELECT kpi_id, window_end, center_id, line_id, throughput_count FROM kpi_report LIMIT 3;"))
        for row in kpi_data:
            print(f"  {row}")
            
    # Center DB 확인
    center_url_0 = os.getenv('AZ_POSTGRE_DATABASE_URL_0')
    print(f"\n=== Center DB URL_0: {center_url_0.split('@')[1] if '@' in center_url_0 else center_url_0} ===")
    engine_0 = create_engine(center_url_0)
    with engine_0.connect() as conn_0:
        kpi_count_0 = conn_0.execute(text("SELECT COUNT(*) FROM kpi_report;")).scalar()
        print(f"Center DB 0: KPI Count = {kpi_count_0}")
