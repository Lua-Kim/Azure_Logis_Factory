from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from psycopg2.extras import RealDictCursor

from app.db import get_conn, put_conn

router = APIRouter()

WINDOW_MAP = {
    "5m": "5 minutes",
    "1h": "1 hour",
    "24h": "24 hours"
}

GRANULARITY_MAP = {
    "hour": "hour",
    "day": "day",
    "month": "month",
    "year": "year"
}


def fetch_all(query: str, params: tuple = ()):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()
    finally:
        put_conn(conn)


@router.get("/line/status")
def get_line_status():
    query = """
        SELECT line_id, current_status, active_bottlenecks, last_basket_id, last_updated_at
        FROM line_status
        ORDER BY line_id
    """
    return fetch_all(query)


@router.get("/kpi")
def get_kpi(window: str = Query("5m"), limit: int = Query(200, ge=1, le=1000)):
    interval = WINDOW_MAP.get(window)
    if not interval:
        raise HTTPException(status_code=400, detail="window must be one of 5m, 1h, 24h")

    query = """
        SELECT window_end, center_id, zone_id, line_id, throughput_count, created_at
        FROM kpi_report
        WHERE window_end >= (now() - %s::interval)
        ORDER BY window_end DESC
        LIMIT %s
    """
    return fetch_all(query, (interval, limit))


@router.get("/bottlenecks")
def get_bottlenecks(
    from_ts: Optional[str] = None,
    to_ts: Optional[str] = None,
    center_id: Optional[int] = None,
    line_id: Optional[int] = None,
    limit: int = Query(200, ge=1, le=1000)
):
    where = []
    params = []

    if from_ts:
        where.append("occurred_at >= %s")
        params.append(from_ts)
    if to_ts:
        where.append("occurred_at <= %s")
        params.append(to_ts)
    if center_id is not None:
        where.append("center_id = %s")
        params.append(center_id)
    if line_id is not None:
        where.append("line_id = %s")
        params.append(line_id)

    where_sql = " WHERE " + " AND ".join(where) if where else ""
    query = f"""
        SELECT bottleneck_id, root_event_id, occurred_at, center_id, zone_id, line_id,
               section_id, sensor_id, duration_sec, cause_code, affected_basket,
               result_code, detail_reason, worker_id, status, error_code, error_message
        FROM bottleneck_event
        {where_sql}
        ORDER BY occurred_at DESC
        LIMIT %s
    """
    params.append(limit)
    return fetch_all(query, tuple(params))


@router.get("/events/recent")
def get_recent_events(limit: int = Query(100, ge=1, le=500)):
    query = """
        SELECT event_id, event_type_code, occurred_at, center_id, zone_id, line_id,
               section_id, sensor_id, basket_id, numeric_value, status, error_code
        FROM sensor_event
        ORDER BY occurred_at DESC
        LIMIT %s
    """
    return fetch_all(query, (limit,))


@router.get("/line/analytics")
def get_line_analytics(
    line_id: int,
    granularity: str = Query("hour"),
    start_ts: Optional[str] = None,
    end_ts: Optional[str] = None
):
    gran = GRANULARITY_MAP.get(granularity)
    if not gran:
        raise HTTPException(status_code=400, detail="granularity must be hour, day, month, year")

    start_dt = datetime.now(timezone.utc) - timedelta(hours=24)
    end_dt = datetime.now(timezone.utc)

    if start_ts:
        start_dt = datetime.fromisoformat(start_ts)
    if end_ts:
        end_dt = datetime.fromisoformat(end_ts)

    query = """
        SELECT date_trunc(%s, occurred_at) AS bucket,
               COUNT(*) AS event_count,
               SUM(CASE WHEN event_type_code = 'ARRIVAL' THEN 1 ELSE 0 END) AS arrival_count,
               SUM(CASE WHEN event_type_code = 'DEPARTURE' THEN 1 ELSE 0 END) AS departure_count
        FROM sensor_event
        WHERE line_id = %s
          AND occurred_at >= %s
          AND occurred_at <= %s
        GROUP BY bucket
        ORDER BY bucket
    """
    return fetch_all(query, (gran, line_id, start_dt, end_dt))
