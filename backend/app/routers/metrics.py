from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db import get_session
from app.models import KpiReport, Center, BottleneckEvent

router = APIRouter()

WINDOW_MAP = {
    "5m": 5,
    "1h": 60,
    "24h": 1440,
    "year": 525600
}

@router.get("/hq/kpi")
def hq_kpi(window: str = Query("5m"), limit: int = Query(200)):
    """모든 센터의 DB를 순회하며 KPI 데이터를 수집 (ORM 버전)"""
    
    # 1. 중앙 DB 세션 생성 및 센터 목록 조회
    main_db = get_session("main")
    try:
        centers = main_db.query(Center.id).all()
    finally:
        main_db.close()

    all_kpi = []
    minutes = WINDOW_MAP.get(window, 5)
    time_threshold = datetime.now() - timedelta(minutes=minutes)

    # 2. 각 센터별 DB 세션을 열어 데이터 조회
    for center in centers:
        cid = str(center.id)
        # 해당 센터 전용 세션 생성
        center_db = get_session(cid)
        try:
            results = (
                center_db.query(KpiReport)
                .filter(KpiReport.window_end >= time_threshold)
                .order_by(desc(KpiReport.window_end))
                .limit(limit)
                .all()
            )
            all_kpi.extend(results)
        except Exception as e:
            print(f"Center {cid} 조회 실패: {e}")
            continue
        finally:
            center_db.close()

    # 3. 전체 데이터 정렬 및 반환
    all_kpi.sort(key=lambda x: x.window_end, reverse=True)
    return all_kpi[:limit]

@router.get("/hq/bottlenecks")
def hq_bottlenecks(limit: int = Query(200)):
    """모든 센터의 병목 현상 데이터 수집 (ORM 버전)"""
    main_db = get_session("main")
    try:
        centers = main_db.query(Center.id).all()
    finally:
        main_db.close()

    all_events = []
    for center in centers:
        cid = str(center.center_id)
        center_db = get_session(cid)
        try:
            events = (
                center_db.query(BottleneckEvent)
                .order_by(desc(BottleneckEvent.occurred_at))
                .limit(limit)
                .all()
            )
            all_events.extend(events)
        except Exception as e:
            print(f"Center {cid} 병목 조회 실패: {e}")
            continue
        finally:
            center_db.close()

    all_events.sort(key=lambda x: x.occurred_at, reverse=True)
    return all_events[:limit]