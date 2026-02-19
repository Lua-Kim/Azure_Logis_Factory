import os
from dotenv import load_dotenv
import psycopg2
from datetime import datetime, timedelta
from random import randint, choice

load_dotenv()
conn = psycopg2.connect(os.getenv('AZ_POSTGRE_DATABASE_URL'))
cur = conn.cursor()

# 기존 병목 데이터 삭제
cur.execute("DELETE FROM bottleneck_event")
conn.commit()

# 모든 17개 라인 포함 (1010101 ~ 1010117)
line_ids = list(range(1010101, 1010118))  # 1010101 ~ 1010117 (17개 라인)
center_ids = [100, 110, 120, 130]
causes = ['JAM', 'SENSOR', 'OVERLOAD', 'BELT_MISALIGNMENT', 'MOTOR_FAILURE']
status_list = ['ACTIVE', 'RESOLVED', 'RECOVERING']

# 과거 14일간의 병목 데이터 생성
base_time = datetime(2026, 2, 19, 12, 0, 0)  # 2026-02-19 12:00:00

bottlenecks = []
bottleneck_id = 1

for day_offset in range(14):  # 14일간
    current_day = base_time - timedelta(days=day_offset)
    
    # 하루에 15-25개의 병목 발생 (훨씬 증가: 3-5 → 15-25)
    for _ in range(randint(15, 25)):
        line_id = choice(line_ids)
        center_id = choice(center_ids)
        
        # 시작 시간: 랜덤 시간대 (0-23시)
        start_hour = randint(0, 23)
        start_minute = randint(0, 59)
        start_second = randint(0, 59)
        
        occurred_at = current_day.replace(hour=start_hour, minute=start_minute, second=start_second)
        
        # 지속 시간: 30초 ~ 15분 (현실적인 범위)
        duration_seconds = choice([30, 45, 60, 90, 120, 180, 300, 600, 900])
        
        # 원인 선택
        cause = choice(causes)
        
        # 상태 (대부분 RESOLVED, 일부 ACTIVE)
        status = choice([status_list[2], status_list[2], status_list[1]])  # 70% RECOVERING, 30% RESOLVED
        
        # 데이터 추가
        bottlenecks.append({
            'line_id': line_id,
            'duration_seconds': duration_seconds,
            'cause_code': cause,
            'status': status,
            'occurred_at': occurred_at,
            'center_id': center_id
        })

# 데이터 정렬 (최신 순)
bottlenecks.sort(key=lambda x: x['occurred_at'], reverse=True)

print(f"생성될 병목 데이터: {len(bottlenecks)}개")

# 데이터베이스에 삽입
try:
    for bn in bottlenecks:
        cur.execute("""
            INSERT INTO bottleneck_event 
            (line_id, duration_sec, cause_code, status, occurred_at, center_id, zone_id, section_id, sensor_id, root_event_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            bn['line_id'],
            bn['duration_seconds'],
            bn['cause_code'],
            bn['status'],
            bn['occurred_at'],
            bn['center_id'],
            1,  # zone_id (기본값)
            1,  # section_id (기본값)
            randint(1, 100),  # sensor_id (랜덤)
            randint(1, 1000)  # root_event_id (랜덤)
        ))
    
    conn.commit()
    print("✅ 병목 데이터 생성 완료!")
    
    # 결과 확인
    cur.execute("SELECT COUNT(*) FROM bottleneck_event")
    count = cur.fetchone()[0]
    print(f"총 병목 레코드: {count}개")
    
    # 라인별 통계
    print("\n라인별 병목 발생 건수:")
    cur.execute("""
        SELECT line_id, COUNT(*) as count FROM bottleneck_event
        GROUP BY line_id
        ORDER BY count DESC
    """)
    for line_id, count in cur.fetchall():
        print(f"  Line {line_id}: {count}건")
    
    # 원인별 통계
    print("\n원인별 병목 발생 건수:")
    cur.execute("""
        SELECT cause_code, COUNT(*) as count FROM bottleneck_event
        GROUP BY cause_code
        ORDER BY count DESC
    """)
    for cause, count in cur.fetchall():
        print(f"  {cause}: {count}건")
    
    # 최근 5개 데이터
    print("\n최근 5개 병목 이벤트:")
    cur.execute("""
        SELECT bottleneck_id, line_id, occurred_at, duration_sec, cause_code, status
        FROM bottleneck_event
        ORDER BY occurred_at DESC
        LIMIT 5
    """)
    for row in cur.fetchall():
        print(f"  ID:{row[0]} Line:{row[1]} Time:{row[2]} Duration:{row[3]}s Cause:{row[4]} Status:{row[5]}")

except Exception as e:
    print(f"❌ 오류: {e}")
    conn.rollback()
finally:
    cur.close()
    conn.close()
