from app.db import init_db, get_session
from sqlalchemy import text

init_db()

# 센터 100 DB에서 센서 마스터 조회
db = get_session('0')  # 센터 100 = DB ID 0
try:
    # 테이블 존재 확인
    result = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
    tables = [r[0] for r in result.fetchall()]
    print(f'테이블 목록: {tables}')
    
    # 센서 테이블이 있으면 센서 ID 조회
    if 'sensor' in tables:
        result = db.execute(text('SELECT COUNT(*) FROM sensor'))
        count = result.scalar()
        print(f'센서 총 개수: {count}')
        
        result = db.execute(text('SELECT sensor_id FROM sensor ORDER BY sensor_id LIMIT 30'))
        ids = [r[0] for r in result.fetchall()]
        print(f'처음 30개 센서 ID: {ids}')
finally:
    db.close()
