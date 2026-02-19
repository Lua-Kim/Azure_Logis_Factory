import asyncio
from typing import Optional
from contextlib import asynccontextmanager  # 오타 수정 (r 추가)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, Date, BigInteger
from sqlalchemy.orm import declarative_base # 최신 방식으로 변경
from sqlalchemy.sql import func

# 모듈 임포트
from app.db import init_db, get_session
from app.models import Line, KpiReport, BottleneckEvent
from app.routers.health import router as health_router
from app.routers.metrics import router as metrics_router
from app.routers.settings import router as settings_router

# --- Lifespan 설정 ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. db.py에서 필요한 것들을 가져옵니다.
    # (언더바가 없는 공개 변수 engines를 가져오는지 확인하세요!)
    from app.db import init_db, engines 
    from app.models import Base
    
    # 2. DB 연결 초기화 (이걸 해야 'main' 키가 생깁니다)
    init_db() 
    
    # 3. 테이블 생성 (이미 있으면 스킵됨)
    for engine in engines.values():
        Base.metadata.create_all(bind=engine)
    
    print("모든 DB 엔진 및 테이블 준비 완료.")
    yield
    # [Shutdown] 앱 종료 시 실행 (필요한 경우)
    print("서버 종료 중...")

# --- FastAPI 앱 선언 (Lifespan 연결) ---
app = FastAPI(
    title="Azure Logistics Dashboard API (SQLAlchemy)",
    lifespan=lifespan
)

# 1. CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

# 2. 라우터 등록
app.include_router(health_router)
app.include_router(metrics_router, prefix="/api")
app.include_router(settings_router, prefix="/api")

# --- WebSocket용 실시간 데이터 조회 함수 ---
def _fetch_snapshot(center_id: Optional[str] = None, line_id: Optional[int] = None) -> dict:
    db_id = center_id if center_id else "main"
    db: Session = get_session(db_id)
    try:
        bind_url = db.get_bind().url
        # 비밀번호를 제외한 호스트, 포트, DB명만 출력
        print(f"DEBUG: [Center {db_id}] 쿼리 시작 -> DB 주소: {bind_url.host}:{bind_url.port}/{bind_url.database}")
    except Exception as e:
        print(f"DEBUG: [Center {db_id}] DB 주소 확인 불가: {e}")

        # 라인 상태
        line_query = db.query(Line)
        if line_id:
            line_query = line_query.filter(Line.id == line_id)
        line_status = line_query.all()

        # KPI
        kpi_query = db.query(KpiReport)
        if line_id:
            kpi_query = kpi_query.filter(KpiReport.line_id == line_id)
        kpis = kpi_query.order_by(desc(KpiReport.window_end)).limit(10).all()

        # 병목
        bn_query = db.query(BottleneckEvent)
        if line_id:
            bn_query = bn_query.filter(BottleneckEvent.line_id == line_id)
        bottlenecks = bn_query.order_by(desc(BottleneckEvent.occurred_at)).limit(5).all()

        return {
            "line_status": jsonable_encoder(line_status),
            "kpi": jsonable_encoder(kpis),
            "bottlenecks": jsonable_encoder(bottlenecks)
        }
    finally:
        db.close()

# --- 실시간 웹소켓 엔드포인트 ---
@app.websocket("/ws/live")
async def live_updates(websocket: WebSocket):
    await websocket.accept()
    center_id = websocket.query_params.get("center_id")
    line_param = websocket.query_params.get("line_id")
    line_id = int(line_param) if line_param else None

    try:
        while True:
            snapshot = await asyncio.to_thread(_fetch_snapshot, center_id, line_id)
            await websocket.send_json(snapshot)
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        print(f"웹소켓 연결 종료: Center {center_id}")

@app.get("/")
def root():
    return {"message": "Logistics API (SQLAlchemy) is running"}

if __name__ == "__main__":
    import uvicorn
    # host는 0.0.0.0으로 해야 외부 접근이 가능하고, 
    # reload=True는 코드 수정 시 서버가 자동으로 재시작되게 합니다.
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)