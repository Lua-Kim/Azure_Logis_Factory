import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Dict

# .env 로드
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# 엔진들을 저장할 딕셔너리
engines = {}
_SessionLocals = {}

def init_db():
    """환경 변수에서 URL을 읽어 모든 DB 엔진과 세션 초기화"""
    urls = {
        "main": os.getenv("AZ_POSTGRE_DATABASE_URL")
    }
    
    # AZ_POSTGRE_DATABASE_URL_0, _1 등을 찾아서 추가
    import re
    for key, value in os.environ.items():
        if re.match(r"AZ_POSTGRE_DATABASE_URL_\d+", key):
            center_id = key.split("_")[-1]
            urls[center_id] = value

    for db_id, url in urls.items():
        if not url: continue
        # PostgreSQL 주소가 postgresql:// 로 시작하지 않으면 수정 (필요시)
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)


        safe_url = url.split('@')[-1] if '@' in url else url
        print(f"DEBUG: [ID:{db_id}] 연결 주소: {safe_url}")
        engine = create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=10)

        
        engines[db_id] = engine
        # 수정: SessionLocals에 저장
        _SessionLocals[db_id] = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        print(f"SQLAlchemy engine initialized for: {db_id}")

def get_db(db_id: str = "main"):
    """특정 DB 세션을 생성하여 반환 (FastAPI Depends용)"""
    if db_id not in _SessionLocals:
        # 만약 없는 ID라면 main을 기본으로 사용하거나 에러 발생
        db_id = "main"
        
    db = _SessionLocals[db_id]()
    try:
        yield db
    finally:
        db.close()

def get_session(db_id: str = "main") -> Session:
    """일반 함수 내부에서 세션이 필요할 때 사용"""
    # 수정: SessionLocals에서 찾도록 변경
    if db_id not in _SessionLocals:
        db_id = "main"
    
    if db_id not in _SessionLocals:
        raise RuntimeError(f"DB 세션이 초기화되지 않았습니다. ID: {db_id}")
        
    return _SessionLocals[db_id]()