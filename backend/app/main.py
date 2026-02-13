import asyncio
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from psycopg2.extras import RealDictCursor
from websockets.exceptions import ConnectionClosedError

from app.db import close_pool, get_conn, init_pool, put_conn
from app.routers.health import router as health_router
from app.routers.metrics import router as metrics_router
from app.routers.settings import router as settings_router

WINDOW_MAP = {
    "5m": "5 minutes",
    "1h": "1 hour",
    "24h": "24 hours"
}

app = FastAPI(title="Azure Logistics Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(health_router)
app.include_router(metrics_router, prefix="/api")
app.include_router(settings_router, prefix="/api")


def _fetch_snapshot(
    window_interval: str = "5 minutes",
    center_id: Optional[int] = None,
    line_id: Optional[int] = None
) -> dict:
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            line_where = []
            line_params = []
            if line_id is not None:
                line_where.append("line_id = %s")
                line_params.append(line_id)
            line_where_sql = " WHERE " + " AND ".join(line_where) if line_where else ""
            cur.execute(
                f"""
                SELECT line_id, current_status, active_bottlenecks, last_basket_id, last_updated_at
                FROM line_status
                {line_where_sql}
                ORDER BY line_id
                """,
                tuple(line_params)
            )
            line_status = cur.fetchall()

            kpi_where = ["window_end >= (now() - %s::interval)"]
            kpi_params = [window_interval]
            if center_id is not None:
                kpi_where.append("center_id = %s")
                kpi_params.append(center_id)
            if line_id is not None:
                kpi_where.append("line_id = %s")
                kpi_params.append(line_id)
            kpi_where_sql = " WHERE " + " AND ".join(kpi_where)
            cur.execute(
                f"""
                SELECT window_end, center_id, zone_id, line_id, throughput_count, created_at
                FROM kpi_report
                {kpi_where_sql}
                ORDER BY window_end DESC
                LIMIT 50
                """,
                tuple(kpi_params)
            )
            kpi = cur.fetchall()

            bn_where = []
            bn_params = []
            if center_id is not None:
                bn_where.append("center_id = %s")
                bn_params.append(center_id)
            if line_id is not None:
                bn_where.append("line_id = %s")
                bn_params.append(line_id)
            bn_where_sql = " WHERE " + " AND ".join(bn_where) if bn_where else ""
            cur.execute(
                f"""
                SELECT bottleneck_id, root_event_id, occurred_at, center_id, zone_id, line_id,
                       section_id, sensor_id, duration_sec, cause_code, affected_basket,
                       result_code, detail_reason, worker_id, status, error_code, error_message
                FROM bottleneck_event
                {bn_where_sql}
                ORDER BY occurred_at DESC
                LIMIT 20
                """,
                tuple(bn_params)
            )
            bottlenecks = cur.fetchall()

        return {
            "line_status": line_status,
            "kpi": kpi,
            "bottlenecks": bottlenecks
        }
    finally:
        put_conn(conn)


@app.websocket("/ws/live")
async def live_updates(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        window = websocket.query_params.get("window", "5m")
        center_param = websocket.query_params.get("center_id")
        line_param = websocket.query_params.get("line_id")
        interval = WINDOW_MAP.get(window, "5 minutes")
        center_id = int(center_param) if center_param else None
        line_id = int(line_param) if line_param else None
        while True:
            snapshot = await asyncio.to_thread(
                _fetch_snapshot,
                interval,
                center_id,
                line_id
            )
            try:
                await websocket.send_json(jsonable_encoder(snapshot))
            except (ConnectionClosedError, WebSocketDisconnect):
                break
            await asyncio.sleep(5)
    except (WebSocketDisconnect, ConnectionClosedError, asyncio.CancelledError):
        return


@app.on_event("startup")
def on_startup() -> None:
    init_pool()


@app.on_event("shutdown")
def on_shutdown() -> None:
    close_pool()
