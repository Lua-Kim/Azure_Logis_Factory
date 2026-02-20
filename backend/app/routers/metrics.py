from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, join, or_

from app.db import get_session, engines
from app.models import KpiReport, BottleneckEvent, Line, LineStatus, SensorEvent

router = APIRouter()

CENTER_DB_MAP = {
    100: "main",
    110: "0",
    120: "1",
    130: "2",
    140: "3"
}


def resolve_db_id(center_id: Optional[int]) -> str:
    if center_id is None:
        return "main"
    return CENTER_DB_MAP.get(center_id, "main")

WINDOW_MAP = {
    "5m": 5,
    "1h": 60,
    "24h": 1440,
    "year": 525600
}

@router.get("/hq/kpi")
def hq_kpi(
    window: str = Query("5m"),
    limit: int = Query(200),
    center_id: Optional[int] = None,
    line_id: Optional[int] = None
):
    """모든 센터의 DB를 순회하며 KPI 데이터를 수집 (ORM 버전)"""
    
    all_kpi = []
    minutes = WINDOW_MAP.get(window, 5)
    time_threshold = datetime.utcnow() - timedelta(minutes=minutes)
    
    print(f"DEBUG: KPI 조회 시간 threshold = {time_threshold}, 현재시간 = {datetime.utcnow()}")

    # 2. center_id가 있으면 해당 DB, 없으면 main에서 조회
    db = get_session(resolve_db_id(center_id))
    try:
        query = db.query(KpiReport).filter(KpiReport.window_end >= time_threshold)
        if center_id is not None:
            query = query.filter(KpiReport.center_id == center_id)
        if line_id is not None:
            query = query.filter(KpiReport.line_id == line_id)

        results = query.order_by(desc(KpiReport.window_end)).limit(limit).all()
        print(f"DEBUG: KPI 조회 결과 {len(results)}개")
        all_kpi.extend(results)
    except Exception as e:
        print(f"DEBUG: KPI 조회 실패: {e}")
    finally:
        db.close()

    # 3. 전체 데이터 정렬 및 반환
    all_kpi.sort(key=lambda x: x.window_end, reverse=True)
    return all_kpi[:limit]

@router.get("/hq/bottlenecks")
def hq_bottlenecks(limit: int = Query(200)):
    """모든 센터의 병목 현상 데이터 수집 (ORM 버전)"""
    main_db = get_session("main")
    try:
        # Main DB에서 모든 병목 데이터 직접 조회
        events = (
            main_db.query(BottleneckEvent)
            .order_by(desc(BottleneckEvent.occurred_at))
            .limit(limit)
            .all()
        )
        return events
    except Exception as e:
        print(f"병목 조회 실패: {e}")
        return []
    finally:
        main_db.close()

@router.get("/kpi")
def get_kpi(
    window: str = Query("1h"),
    limit: int = Query(200),
    center_id: Optional[int] = None,
    line_id: Optional[int] = None
):
    """프론트엔드용 KPI 엔드포인트 (hq_kpi의 별칭)"""
    return hq_kpi(window, limit, center_id, line_id)

@router.get("/line/status")
def get_line_status():
    """모든 라인의 상태 조회 (라인 정보 + 라인 상태)"""
    db_ids = list(engines.keys()) or ["main"]
    result = []
    seen_line_keys = set()

    for db_id in db_ids:
        db = get_session(db_id)
        try:
            lines = db.query(Line).all()
            for line in lines:
                line_key = (line.center_id, line.id)
                if line_key in seen_line_keys:
                    continue

                line_data = {
                    "id": line.id,
                    "line_id": line.id,
                    "center_id": line.center_id,
                    "name": line.name,
                    "type": line.type,
                    "status": line.status,
                    "rail_length_m": line.rail_length_m,
                    "section_count": line.section_count,
                    "current_status": "NORMAL"  # 기본값
                }

                line_status = db.query(LineStatus).filter(LineStatus.id == line.id).first()
                if line_status:
                    line_data["current_status"] = line_status.current_status
                    line_data["active_bottlenecks"] = line_status.active_bottlenecks
                    line_data["last_updated_at"] = line_status.last_updated_at

                result.append(line_data)
                seen_line_keys.add(line_key)
        except Exception as e:
            print(f"라인 상태 조회 실패 ({db_id}): {e}")
        finally:
            db.close()

    return result

@router.get("/bottlenecks")
def get_bottlenecks(
    limit: int = Query(200),
    center_id: Optional[int] = None,
    line_id: Optional[int] = None,
    from_ts: Optional[str] = None,
    to_ts: Optional[str] = None
):
    """프론트엔드용 병목 현상 엔드포인트 (필터 지원)"""
    db = get_session(resolve_db_id(center_id))
    try:
        query = db.query(BottleneckEvent)
        
        if center_id:
            query = query.filter(BottleneckEvent.center_id == center_id)
        if line_id:
            query = query.filter(BottleneckEvent.line_id == line_id)
        if from_ts:
            try:
                from_dt = datetime.fromisoformat(from_ts)
                query = query.filter(BottleneckEvent.occurred_at >= from_dt)
            except:
                pass
        if to_ts:
            try:
                to_dt = datetime.fromisoformat(to_ts)
                query = query.filter(BottleneckEvent.occurred_at <= to_dt)
            except:
                pass
        
        events = query.order_by(desc(BottleneckEvent.occurred_at)).limit(limit).all()
        return events
    except Exception as e:
        print(f"병목 조회 실패: {e}")
        return []
    finally:
        db.close()

@router.get("/events/recent")
def get_recent_events(
    limit: int = Query(100),
    center_id: Optional[int] = None,
    line_id: Optional[int] = None
):
    """최근 센서/운영 이벤트 조회"""
    db = get_session(resolve_db_id(center_id))
    try:
        from app.models import SensorEvent
        query = db.query(SensorEvent)
        if center_id:
            query = query.filter(SensorEvent.center_id == center_id)
        if line_id:
            query = query.filter(SensorEvent.line_id == line_id)
        events = query.order_by(desc(SensorEvent.occurred_at)).limit(limit).all()
        return events
    except Exception as e:
        print(f"최근 이벤트 조회 실패: {e}")
        return []
    finally:
        db.close()

@router.get("/line/analytics")
def get_line_analytics(
    line_id: int = Query(...),
    granularity: str = Query("hour"),
    start_ts: Optional[str] = None,
    end_ts: Optional[str] = None
):
    """라인 분석 데이터 조회"""
    main_db = get_session("main")
    try:
        if granularity == "hour":
            kpis = main_db.query(KpiReport).filter(
                KpiReport.line_id == line_id
            ).order_by(desc(KpiReport.window_end)).limit(24).all()
        else:
            kpis = main_db.query(KpiReport).filter(
                KpiReport.line_id == line_id
            ).order_by(desc(KpiReport.window_end)).limit(50).all()
        return kpis
    except Exception as e:
        print(f"라인 분석 조회 실패: {e}")
        return []
    finally:
        main_db.close()