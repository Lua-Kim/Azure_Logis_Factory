from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Query
from sqlalchemy import func, desc
from app.db import get_session
from app.models import BottleneckEvent, KpiReport, LineStatus, Line, Center, SensorEvent

router = APIRouter(tags=["Performance"])

@router.get("/performance/summary")
def performance_summary(center_id: Optional[int] = None, hours: int = Query(24)):
    """
    현재 센터의 전체 성능 요약
    - 총 병목 이벤트 수
    - 평균 병목 지속시간
    - 총 정지 시간
    - 라인 가용성
    """
    db = get_session("main" if not center_id else str(center_id))
    try:
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        
        # 1. 병목 이벤트 집계
        bottleneck_stats = db.query(
            func.count(BottleneckEvent.id).label("total_events"),
            func.avg(BottleneckEvent.duration_sec).label("avg_duration"),
            func.sum(BottleneckEvent.duration_sec).label("total_downtime_sec")
        ).filter(BottleneckEvent.occurred_at >= time_threshold).first()
        
        # 2. 센서 이벤트 (에러 카운트)
        sensor_error_count = db.query(
            func.count(SensorEvent.id)
        ).filter(
            SensorEvent.occurred_at >= time_threshold,
            SensorEvent.error_code != None
        ).scalar() or 0
        
        # 3. 처리량 (KPI)
        throughput = db.query(
            func.sum(KpiReport.throughput_count)
        ).filter(KpiReport.window_end >= time_threshold).scalar() or 0
        
        # 4. 라인별 가용성 (자세한 정보)
        lines = db.query(Line).all()
        line_availability = []
        
        for line in lines:
            line_bottlenecks = db.query(
                func.count(BottleneckEvent.id),
                func.sum(BottleneckEvent.duration_sec)
            ).filter(
                BottleneckEvent.line_id == line.id,
                BottleneckEvent.occurred_at >= time_threshold
            ).first()
            
            bottleneck_count = line_bottlenecks[0] or 0
            downtime = line_bottlenecks[1] or 0
            
            # 가용성 = (전체 시간 - 정지 시간) / 전체 시간
            total_seconds = hours * 3600
            availability = max(0, (total_seconds - downtime) / total_seconds * 100)
            
            line_availability.append({
                "line_id": line.id,
                "line_name": line.name,
                "bottleneck_count": bottleneck_count,
                "downtime_sec": downtime,
                "availability_percent": round(availability, 2)
            })
        
        return {
            "total_bottleneck_events": bottleneck_stats[0] or 0,
            "avg_bottleneck_duration_sec": round(bottleneck_stats[1] or 0, 2),
            "total_downtime_sec": int(bottleneck_stats[2] or 0),
            "sensor_error_count": sensor_error_count,
            "total_throughput": int(throughput),
            "line_availability": line_availability,
            "period_hours": hours,
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        db.close()

@router.get("/performance/line-metrics")
def line_metrics(center_id: Optional[int] = None, hours: int = Query(24)):
    """
    라인별 성능 지표:
    - 각 라인의 처리량
    - 각 라인의 병목 통계
    - 각 라인의 가용성
    """
    db = get_session("main" if not center_id else str(center_id))
    try:
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        
        # 라인 목록
        lines_query = db.query(Line)
        if center_id:
            lines_query = lines_query.filter(Line.center_id == center_id)
        
        lines = lines_query.all()
        metrics = []
        
        for line in lines:
            # 처리량
            throughput = db.query(
                func.sum(KpiReport.throughput_count)
            ).filter(
                KpiReport.line_id == line.id,
                KpiReport.window_end >= time_threshold
            ).scalar() or 0
            
            # 병목
            bottleneck_data = db.query(
                func.count(BottleneckEvent.id),
                func.avg(BottleneckEvent.duration_sec),
                func.max(BottleneckEvent.duration_sec),
                func.sum(BottleneckEvent.duration_sec)
            ).filter(
                BottleneckEvent.line_id == line.id,
                BottleneckEvent.occurred_at >= time_threshold
            ).first()
            
            bottleneck_count = bottleneck_data[0] or 0
            avg_duration = bottleneck_data[1] or 0
            max_duration = bottleneck_data[2] or 0
            total_downtime = bottleneck_data[3] or 0
            
            # 가용성
            total_seconds = hours * 3600
            availability = max(0, (total_seconds - total_downtime) / total_seconds * 100)
            
            # 오류율
            total_events = db.query(func.count(SensorEvent.id)).filter(
                SensorEvent.line_id == line.id,
                SensorEvent.occurred_at >= time_threshold
            ).scalar() or 1
            
            error_events = db.query(func.count(SensorEvent.id)).filter(
                SensorEvent.line_id == line.id,
                SensorEvent.occurred_at >= time_threshold,
                SensorEvent.error_code != None
            ).scalar() or 0
            
            error_rate = (error_events / total_events * 100) if total_events > 0 else 0
            
            metrics.append({
                "line_id": line.id,
                "line_name": line.name,
                "throughput": int(throughput),
                "bottleneck_count": bottleneck_count,
                "avg_bottleneck_duration_sec": round(avg_duration, 2),
                "max_bottleneck_duration_sec": int(max_duration),
                "total_downtime_sec": int(total_downtime),
                "availability_percent": round(availability, 2),
                "error_rate_percent": round(error_rate, 2)
            })
        
        return sorted(metrics, key=lambda x: x["availability_percent"])
    finally:
        db.close()

@router.get("/performance/error-analysis")
def error_analysis(center_id: Optional[int] = None, hours: int = Query(24)):
    """
    오류 분석:
    - 가장 많은 오류 센서
    - 가장 많은 오류 유형
    - 오류별 빈도
    """
    db = get_session("main" if not center_id else str(center_id))
    try:
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        
        # 센서별 오류 통계
        sensor_errors = db.query(
            SensorEvent.sensor_id,
            func.count(SensorEvent.id).label("error_count")
        ).filter(
            SensorEvent.error_code != None,
            SensorEvent.occurred_at >= time_threshold
        ).group_by(SensorEvent.sensor_id).order_by(
            func.count(SensorEvent.id).desc()
        ).limit(10).all()
        
        # 오류 코드별 통계
        error_codes = db.query(
            SensorEvent.error_code,
            func.count(SensorEvent.id).label("error_count")
        ).filter(
            SensorEvent.error_code != None,
            SensorEvent.occurred_at >= time_threshold
        ).group_by(SensorEvent.error_code).order_by(
            func.count(SensorEvent.id).desc()
        ).all()
        
        return {
            "top_error_sensors": [
                {"sensor_id": s[0], "error_count": s[1]} for s in sensor_errors
            ],
            "error_code_distribution": [
                {"error_code": e[0], "count": e[1]} for e in error_codes
            ],
            "period_hours": hours,
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        db.close()

@router.get("/performance/trend")
def performance_trend(center_id: Optional[int] = None, interval: str = Query("hourly")):
    """
    성능 추이:
    - 시간대별 처리량
    - 시간대별 병목 사건 수
    - 시간대별 가용성
    """
    db = get_session("main" if not center_id else str(center_id))
    try:
        if interval == "hourly":
            hours_back = 24
            time_threshold = datetime.utcnow() - timedelta(hours=hours_back)
        elif interval == "daily":
            hours_back = 30 * 24
            time_threshold = datetime.utcnow() - timedelta(days=30)
        else:
            hours_back = 7 * 24
            time_threshold = datetime.utcnow() - timedelta(days=7)
        
        # KPI 시계열 (처리량)
        kpi_trend = db.query(
            KpiReport.window_end,
            func.sum(KpiReport.throughput_count)
        ).filter(KpiReport.window_end >= time_threshold).group_by(
            KpiReport.window_end
        ).order_by(KpiReport.window_end).all()
        
        # 병목 시계열
        bottleneck_trend = db.query(
            func.date_trunc('hour', BottleneckEvent.occurred_at).label('hour'),
            func.count(BottleneckEvent.id),
            func.avg(BottleneckEvent.duration_sec)
        ).filter(
            BottleneckEvent.occurred_at >= time_threshold
        ).group_by(
            func.date_trunc('hour', BottleneckEvent.occurred_at)
        ).order_by('hour').all()
        
        return {
            "throughput_trend": [
                {
                    "timestamp": k[0].isoformat() if k[0] else None,
                    "throughput": int(k[1] or 0)
                } for k in kpi_trend
            ],
            "bottleneck_trend": [
                {
                    "timestamp": str(b[0]) if b[0] else None,
                    "event_count": b[1] or 0,
                    "avg_duration_sec": round(b[2] or 0, 2)
                } for b in bottleneck_trend
            ],
            "interval": interval,
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        db.close()

@router.get("/performance/sensor-monitoring")
def sensor_monitoring(center_id: Optional[int] = None, limit: int = Query(100), hours: int = Query(1)):
    """
    실시간 센서 모니터링:
    - 최근 센서 이벤트
    - 센서별 상태 (정상/경고/오류)
    - 라인별 센서 건강도
    """
    db = get_session("main" if not center_id else str(center_id))
    try:
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        
        # 1. 최근 센서 이벤트
        recent_events = db.query(SensorEvent).filter(
            SensorEvent.occurred_at >= time_threshold
        ).order_by(desc(SensorEvent.occurred_at)).limit(limit).all()
        
        # 2. 센서별 건강도 (라인별)
        from sqlalchemy import and_
        sensors_by_line = db.query(
            SensorEvent.line_id,
            SensorEvent.sensor_id,
            func.count(SensorEvent.id).label("event_count"),
            func.count(SensorEvent.error_code).label("error_count"),
            func.avg(SensorEvent.numeric_value).label("avg_value"),
            func.max(SensorEvent.occurred_at).label("last_updated")
        ).filter(
            SensorEvent.occurred_at >= time_threshold
        ).group_by(
            SensorEvent.line_id,
            SensorEvent.sensor_id
        ).all()
        
        # 센서 건강도 계산
        sensor_health = []
        for line_id, sensor_id, event_count, error_count, avg_value, last_updated in sensors_by_line:
            error_rate = (error_count / event_count * 100) if event_count > 0 else 0
            
            # 건강도 판단: 오류율이 높을수록 낮음
            if error_rate > 20:
                health_status = "CRITICAL"
                health_score = max(0, 100 - error_rate * 5)
            elif error_rate > 10:
                health_status = "WARNING"
                health_score = max(30, 100 - error_rate * 3)
            else:
                health_status = "HEALTHY"
                health_score = 100 - error_rate * 2
            
            sensor_health.append({
                "line_id": line_id,
                "sensor_id": sensor_id,
                "event_count": event_count,
                "error_count": error_count or 0,
                "error_rate_percent": round(error_rate, 2),
                "avg_value": round(avg_value or 0, 2),
                "health_status": health_status,
                "health_score": round(health_score, 2),
                "last_updated": last_updated.isoformat() if last_updated else None
            })
        
        # 3. 라인별 센서 상태 요약
        line_sensor_summary = {}
        for sensor in sensor_health:
            line_id = sensor["line_id"]
            if line_id not in line_sensor_summary:
                line_sensor_summary[line_id] = {
                    "total_sensors": 0,
                    "healthy_sensors": 0,
                    "warning_sensors": 0,
                    "critical_sensors": 0,
                    "avg_health_score": 0
                }
            
            summary = line_sensor_summary[line_id]
            summary["total_sensors"] += 1
            if sensor["health_status"] == "HEALTHY":
                summary["healthy_sensors"] += 1
            elif sensor["health_status"] == "WARNING":
                summary["warning_sensors"] += 1
            else:
                summary["critical_sensors"] += 1
            summary["avg_health_score"] += sensor["health_score"]
        
        # 평균 계산
        for line_id in line_sensor_summary:
            count = line_sensor_summary[line_id]["total_sensors"]
            if count > 0:
                line_sensor_summary[line_id]["avg_health_score"] /= count
                line_sensor_summary[line_id]["avg_health_score"] = round(line_sensor_summary[line_id]["avg_health_score"], 2)
        
        # 4. 오류 이벤트만 필터링
        error_events = [
            {
                "event_id": e.id,
                "timestamp": e.occurred_at.isoformat() if e.occurred_at else None,
                "line_id": e.line_id,
                "sensor_id": e.sensor_id,
                "error_code": e.error_code,
                "error_message": e.error_message,
                "event_type": e.event_type_code
            } for e in recent_events if e.error_code
        ]
        
        return {
            "recent_events": [
                {
                    "event_id": e.id,
                    "timestamp": e.occurred_at.isoformat() if e.occurred_at else None,
                    "line_id": e.line_id,
                    "sensor_id": e.sensor_id,
                    "event_type": e.event_type_code,
                    "numeric_value": e.numeric_value,
                    "status": e.status,
                    "error_code": e.error_code
                } for e in recent_events
            ],
            "sensor_health": sorted(sensor_health, key=lambda x: x["health_score"]),
            "line_sensor_summary": line_sensor_summary,
            "error_events": error_events,
            "period_hours": hours,
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        db.close()

