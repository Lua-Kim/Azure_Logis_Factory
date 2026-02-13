from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from psycopg2.extras import RealDictCursor

from app.db import get_conn, put_conn
from app.schemas.settings import (
    CenterCreate,
    CenterUpdate,
    LineCreate,
    SectionCreate,
    SensorCreate,
    ThresholdUpdate,
    ZoneCreate,
)

router = APIRouter()


def fetch_all(query: str, params: tuple = ()):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()
    finally:
        put_conn(conn)


def fetch_one(query: str, params: tuple = ()):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchone()
    finally:
        put_conn(conn)


def execute(query: str, params: tuple = ()):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            conn.commit()
    finally:
        put_conn(conn)


@router.get("/settings/centers")
def list_centers(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    q: Optional[str] = None
):
    offset = (page - 1) * size
    where_sql = ""
    params = []

    if q:
        where_sql = " WHERE name ILIKE %s "
        params.append(f"%{q}%")

    count_query = f"SELECT COUNT(*) AS total FROM center{where_sql}"
    data_query = f"""
        SELECT center_id, name, location, status, opened_at
        FROM center
        {where_sql}
        ORDER BY center_id
        LIMIT %s OFFSET %s
    """
    total_row = fetch_one(count_query, tuple(params))
    params.extend([size, offset])
    items = fetch_all(data_query, tuple(params))

    return {
        "items": items,
        "page": page,
        "size": size,
        "total": total_row["total"] if total_row else 0
    }


@router.post("/settings/centers")
def create_center(payload: CenterCreate):
    query = """
        INSERT INTO center (name, location, status, opened_at)
        VALUES (%s, %s, %s, %s)
        RETURNING center_id
    """
    row = fetch_one(query, (payload.name, payload.location, payload.status, payload.opened_at))
    return {"center_id": row["center_id"]}


@router.put("/settings/centers/{center_id}")
def update_center(center_id: int, payload: CenterUpdate):
    fields = []
    params = []

    for key, value in payload.model_dump(exclude_unset=True).items():
        fields.append(f"{key} = %s")
        params.append(value)

    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(center_id)
    query = f"UPDATE center SET {', '.join(fields)} WHERE center_id = %s"
    execute(query, tuple(params))
    return {"updated": True}


@router.get("/settings/centers/{center_id}/zones")
def list_zones(center_id: int):
    query = """
        SELECT zone_id, center_id, name, type, status
        FROM zone
        WHERE center_id = %s
        ORDER BY zone_id
    """
    return fetch_all(query, (center_id,))


@router.post("/settings/zones")
def create_zone(payload: ZoneCreate):
    query = """
        INSERT INTO zone (center_id, name, type, status)
        VALUES (%s, %s, %s, %s)
        RETURNING zone_id
    """
    row = fetch_one(query, (payload.center_id, payload.name, payload.type, payload.status))
    return {"zone_id": row["zone_id"]}


@router.get("/settings/centers/{center_id}/lines")
def list_lines(center_id: int):
    query = """
        SELECT line_id, center_id, name, type, status, rail_length_m, section_count
        FROM line
        WHERE center_id = %s
        ORDER BY line_id
    """
    return fetch_all(query, (center_id,))


@router.post("/settings/lines")
def create_line(payload: LineCreate):
    query = """
        INSERT INTO line (center_id, name, type, status, rail_length_m, section_count)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING line_id
    """
    row = fetch_one(
        query,
        (
            payload.center_id,
            payload.name,
            payload.type,
            payload.status,
            payload.rail_length_m,
            payload.section_count,
        )
    )
    return {"line_id": row["line_id"]}


@router.get("/settings/lines/{line_id}/sections")
def list_sections(line_id: int):
    query = """
        SELECT section_id, line_id, name, order_in_line, type
        FROM section
        WHERE line_id = %s
        ORDER BY section_id
    """
    return fetch_all(query, (line_id,))


@router.post("/settings/sections")
def create_section(payload: SectionCreate):
    line_row = fetch_one(
        "SELECT section_count FROM line WHERE line_id = %s",
        (payload.line_id,)
    )
    if not line_row:
        raise HTTPException(status_code=404, detail="Line not found")

    if payload.order_in_line is not None:
        max_sections = line_row["section_count"]
        if max_sections and payload.order_in_line > int(max_sections):
            raise HTTPException(status_code=400, detail="order_in_line exceeds section_count")

    query = """
        INSERT INTO section (line_id, name, order_in_line, type)
        VALUES (%s, %s, %s, %s)
        RETURNING section_id
    """
    row = fetch_one(query, (payload.line_id, payload.name, payload.order_in_line, payload.type))
    return {"section_id": row["section_id"]}


@router.get("/settings/lines/{line_id}/sensors")
def list_sensors(line_id: int):
    query = """
        SELECT s.sensor_id, s.section_id, s.equipment_id, s.sensor_type, s.name, s.status
        FROM sensor s
        JOIN section sec ON sec.section_id = s.section_id
        WHERE sec.line_id = %s
        ORDER BY s.sensor_id
    """
    return fetch_all(query, (line_id,))


@router.post("/settings/sensors")
def create_sensor(payload: SensorCreate):
    line_row = fetch_one(
        """
        SELECT sec.line_id, l.rail_length_m
        FROM section sec
        JOIN line l ON l.line_id = sec.line_id
        WHERE sec.section_id = %s
        """,
        (payload.section_id,)
    )
    if not line_row or line_row["rail_length_m"] is None:
        raise HTTPException(status_code=400, detail="Line rail_length_m is required")

    count_row = fetch_one(
        """
        SELECT COUNT(*) AS count
        FROM sensor s
        JOIN section sec ON sec.section_id = s.section_id
        WHERE sec.line_id = %s
        """,
        (line_row["line_id"],)
    )

    max_sensors = int(2 * float(line_row["rail_length_m"]))
    current_count = int(count_row["count"]) if count_row else 0

    # Enforce max sensors per line based on rail length
    if current_count + 1 > max_sensors:
        raise HTTPException(
            status_code=400,
            detail=f"Sensor limit exceeded: {current_count}/{max_sensors}"
        )

    query = """
        INSERT INTO sensor (section_id, equipment_id, sensor_type, name, status)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING sensor_id
    """
    row = fetch_one(
        query,
        (
            payload.section_id,
            payload.equipment_id,
            payload.sensor_type,
            payload.name,
            payload.status,
        )
    )
    return {"sensor_id": row["sensor_id"]}


@router.get("/settings/thresholds")
def list_thresholds():
    query = """
        SELECT config_key, config_value, description
        FROM threshold_config
        ORDER BY config_key
    """
    return fetch_all(query)


@router.put("/settings/thresholds/{config_key}")
def update_threshold(config_key: str, payload: ThresholdUpdate):
    query = """
        UPDATE threshold_config
        SET config_value = %s, description = %s
        WHERE config_key = %s
    """
    execute(query, (payload.config_value, payload.description, config_key))
    return {"updated": True}
