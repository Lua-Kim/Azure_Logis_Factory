import os
from dotenv import load_dotenv
import psycopg2

env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

main_url = os.getenv('AZ_POSTGRE_DATABASE_URL')
conn = psycopg2.connect(main_url)

with conn.cursor() as cur:
    print("=" * 60)
    
    # 전체 라인
    cur.execute("SELECT COUNT(*) FROM line")
    total_lines = cur.fetchone()[0]
    print(f"📍 전체 라인: {total_lines}개\n")
    
    cur.execute("SELECT line_id, name FROM line LIMIT 10")
    print("   라인 목록:")
    for line_id, name in cur.fetchall():
        print(f"     - {line_id}: {name}")
    
    # 병목이 있는 라인
    cur.execute("""
        SELECT DISTINCT line_id FROM bottleneck_event
    """)
    bottleneck_lines = [row[0] for row in cur.fetchall()]
    print(f"\n🚫 병목이 있는 라인: {len(bottleneck_lines)}개")
    print(f"   {bottleneck_lines}")
    
    print("\n" + "=" * 60)
    print("💡 DurationBar는 병목이 있는 라인만 표시합니다")
    print(f"   → 현재 3개 라인에만 병목 데이터가 있어서 3개만 표시됨")
    print("=" * 60)

conn.close()
