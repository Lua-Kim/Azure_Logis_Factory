from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db import get_session
from app.models import Center, Zone, Line
from app.schemas.settings import (
    CenterCreate, CenterUpdate, 
    ZoneCreate, LineCreate
)

router = APIRouter(tags=["Settings"])

# --- Helper: 세션 관리용 내부 함수 ---
def get_db_session(center_id: Optional[int] = None) -> Session:
    db_id = str(center_id) if center_id is not None else "main"
    return get_session(db_id)

# --- Centers (항상 중앙 DB인 'main'에서 처리) ---

@router.get("/settings/centers")
def list_centers(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=200)):
    db = get_db_session() # main DB
    try:
        total = db.query(Center).count()
        items = db.query(Center).offset((page - 1) * size).limit(size).all()
        return {"items": items, "total": total, "page": page, "size": size}
    finally:
        db.close()

@router.post("/settings/centers")
def create_center(payload: CenterCreate):
    db = get_db_session() # main DB
    try:
        new_center = Center(**payload.model_dump())
        db.add(new_center)
        db.commit()
        db.refresh(new_center)
        return new_center
    finally:
        db.close()

@router.put("/settings/centers/{center_id}")
def update_center(center_id: int, payload: CenterUpdate):
    db = get_db_session() # main DB
    try:
        center = db.query(Center).filter(Center.id == center_id).first()
        if not center:
            raise HTTPException(status_code=404, detail="Center not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(center, key, value)
        db.commit()
        db.refresh(center)
        return center
    finally:
        db.close()

@router.delete("/settings/centers/{center_id}")
def delete_center(center_id: int):
    db = get_db_session() # main DB
    try:
        center = db.query(Center).filter(Center.id == center_id).first()
        if not center:
            raise HTTPException(status_code=404, detail="Center not found")
        db.delete(center)
        db.commit()
        return {"status": "deleted", "center_id": center_id}
    finally:
        db.close()

# --- Zones (특정 센터 DB에서 처리) ---

@router.get("/settings/centers/{center_id}/zones")
def list_zones(center_id: int):
    db = get_db_session(center_id)
    try:
        return db.query(Zone).all()
    finally:
        db.close()

@router.post("/settings/zones")
def create_zone(payload: ZoneCreate):
    db = get_db_session(payload.center_id)
    try:
        new_zone = Zone(**payload.model_dump())
        db.add(new_zone)
        db.commit()
        db.refresh(new_zone)
        return new_zone
    finally:
        db.close()

# --- Lines (특정 센터 DB에서 처리) ---

@router.get("/settings/centers/{center_id}/lines")
def list_lines(center_id: int):
    db = get_db_session(center_id)
    try:
        return db.query(Line).all()
    finally:        db.close()

@router.post("/settings/lines")
def create_line(payload: LineCreate):
    db = get_db_session(payload.center_id)
    try:
        new_line = Line(**payload.model_dump())
        db.add(new_line)
        db.commit()
        db.refresh(new_line)
        return new_line
    finally:
        db.close()