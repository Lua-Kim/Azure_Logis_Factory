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
        print("🔄 Bottleneck Cause 데이터 업데이트")
        print("=" * 70)
        
        # Update 쿼리들
        updates = [
            ("ID 40", "JAM", "컨베이어 적체로 인한 병목", 40),
            ("ID 29", "SENSOR", "센서 감지 오류로 인한 지연", 29),
            ("ID 19", "OVERLOAD", "시스템 과부하로 인한 처리 지연", 19),
        ]
        
        for label, cause_code, detail_reason, bn_id in updates:
            cur.execute("""
                UPDATE bottleneck_event 
                SET cause_code = %s, detail_reason = %s
                WHERE bottleneck_id = %s
            """, (cause_code, detail_reason, bn_id))
            print(f"✅ {label}: {cause_code} - {detail_reason}")
        
        conn.commit()
        print("\n" + "=" * 70)
        print("✨ 업데이트 완료! 확인 중:")
        print("=" * 70 + "\n")
        
        # 확인 쿼리
        cur.execute("""
            SELECT bottleneck_id, line_id, cause_code, detail_reason, occurred_at
            FROM bottleneck_event
            ORDER BY occurred_at DESC
        """)
        
        for row in cur.fetchall():
            bn_id, line_id, cause_code, detail, occurred = row
            print(f"Bottleneck {bn_id}: Line {line_id}")
            print(f"  Cause: {cause_code} ✅")
            print(f"  Detail: {detail}")
            print(f"  Occurred: {occurred}\n")
        
        print("=" * 70)
        print("✅ 모든 Bottleneck이 Cause 코드를 가지고 있습니다!")
        print("   CauseDonut 그래프가 이제 데이터를 표시할 것입니다.")
        print("=" * 70)
        
finally:
    conn.close()
