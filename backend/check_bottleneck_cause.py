import os
from dotenv import load_dotenv
import psycopg2

env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

main_url = os.getenv('AZ_POSTGRE_DATABASE_URL')
conn = psycopg2.connect(main_url)

try:
    with conn.cursor() as cur:
        print("=" * 70)
        print("🔍 Bottleneck 상세 데이터 분석")
        print("=" * 70)
        
        # 전체 Bottleneck 데이터 조회
        cur.execute("""
            SELECT 
                bottleneck_id, 
                line_id, 
                cause_code, 
                duration_sec,
                detail_reason,
                occurred_at
            FROM bottleneck_event
            ORDER BY occurred_at DESC
        """)
        
        rows = cur.fetchall()
        print(f"\n총 {len(rows)}개 Bottleneck 이벤트:\n")
        
        for i, row in enumerate(rows, 1):
            bn_id, line_id, cause_code, duration, detail, occurred = row
            print(f"{i}. ID {bn_id}")
            print(f"   Line: {line_id}")
            print(f"   Cause Code: {cause_code} {'❌ (없음)' if cause_code is None else '✅'}")
            print(f"   Duration: {duration}초")
            print(f"   Detail: {detail}")
            print(f"   Occurred: {occurred}\n")
        
        # Cause Code 분포
        cur.execute("""
            SELECT cause_code, COUNT(*) as count 
            FROM bottleneck_event 
            GROUP BY cause_code
        """)
        
        print("=" * 70)
        print("📊 Cause Code 분포:")
        causes = cur.fetchall()
        for cause, count in causes:
            print(f"  {cause if cause else '(NULL/없음)'}: {count}개")
        
        print("\n" + "=" * 70)
        print("💡 권장사항:")
        if any(c[0] is None for c in causes):
            print("  ⚠️  cause_code가 NULL인 데이터가 있습니다.")
            print("  → CauseDonut 그래프가 정상 표시되려면 cause_code 데이터 필요")
            print("  → 데이터 수정 또는 재생성을 권장합니다.")
        print("=" * 70)
        
finally:
    conn.close()
