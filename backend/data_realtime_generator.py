"""
무한모드로 실행하는 방법 : python data_realtime_generator.py --mode continuous
실시간 데이터 생성 및 적재 엔진

[매번 생성되는 운영 데이터 테이블]
1. KpiReport - 생산량 KPI 리포트
   - 센터당 2-5개 레코드 (시간당 처리량)
   - run_once() 또는 continuous 모드에서 매번 생성

2. LineStatus - 라인 실시간 상태
   - 모든 라인(17개) 상태 업데이트
   - 현재 병목, 상태 정보 포함

3. BottleneckEvent - 병목 이벤트
   - 센터당 10-20개 레코드
   - 원인코드(JAM, SENSOR, OVERLOAD 등) 포함
   - 80% 과거, 20% 실시간

4. SensorEvent - 센서 이벤트
   - 센터당 30-100개 레코드
   - 센서 타입별 값 범위 관리
   - 90% 최근 1시간, 10% 과거 24시간
   - 5% 에러율 시뮬레이션

[추가 생성되는 운영/분석 테이블]
- order_event, maintenance_event, quality_event, operation_cost
- loss_analysis, aggregation_summary, bottleneck_event_sensor

[한 번만 생성되는 마스터 데이터]
- Center, Zone, Line, Section (seed_master.py로 생성)
- Sensor (자동 생성, 중복 방지)

사용법:
  python data_realtime_generator.py --mode once           # 한 번만 실행
  python data_realtime_generator.py --mode continuous    # 30초 간격 무한 실행
  python data_realtime_generator.py --mode continuous --interval 5 --iterations 20  # 5초 간격 20번
"""

import random
import time
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.db import engines, get_session, init_db, _SessionLocals
from app.models import (
    Line, Center, Zone, Section,
    KpiReport, LineStatus, BottleneckEvent, SensorEvent
)

# 상수
CAUSE_CODES = ["JAM", "SENSOR", "OVERLOAD", "MOTOR_FAILURE", "BELT_MISALIGNMENT"]
EVENT_TYPE_CODES = ["MOVEMENT", "STOP", "JAMMED", "OVERFLOW", "SENSOR_ERROR", "MAINTENANCE"]
SENSOR_TYPES = ["PRESSURE", "TEMPERATURE", "VIBRATION", "FLOW", "POSITION"]
STATUSES = ["NORMAL", "WARNING", "ERROR", "MAINTENANCE"]

class RealtimeDataGenerator:
    """실시간 데이터 생성 및 적재"""
    
    # center_id -> db_id 매핑
    # postgres (main): 센터 100
    # IoTLogifa00: 센터 110
    # IoTLogifa01: 센터 120
    # IoTLogifa02: 센터 130
    # IoTLogifa03: 센터 140
    CENTER_DB_MAP = {
        100: 'main',   # postgres
        110: '0',      # IoTLogifa00
        120: '1',      # IoTLogifa01
        130: '2',      # IoTLogifa02
        140: '3',      # IoTLogifa03
    }
    
    def __init__(self):
        self.center_ids = [100, 110, 120, 130, 140]
        self.line_ids = list(range(1010101, 1010118))  # 17 lines
        self.zone_ids = list(range(1, 5))
        self.section_ids = list(range(1, 11))  # 10 sections per line
        self.center_sensor_map = {}  # 센터별 실제 센서 ID 매핑

    def get_center_sensor_ids(self, center_id: int, db_session: Session) -> list:
        """센터별 센서 ID 목록 확보"""
        if center_id not in self.center_sensor_map:
            from sqlalchemy import text
            result = db_session.execute(text("SELECT sensor_id FROM sensor"))
            sensor_ids = [row[0] for row in result]
            if not sensor_ids:
                sensor_ids = list(range(1, 101))
            self.center_sensor_map[center_id] = sensor_ids
        return self.center_sensor_map[center_id]
        
    def _pick_kpi_window_end(self, bucket: str) -> datetime:
        """최근 구간별로 분산된 window_end를 생성한다."""
        now = datetime.utcnow()
        if bucket == "5m":
            minutes_ago = random.uniform(0, 5)
        elif bucket == "1h":
            minutes_ago = random.uniform(5, 60)
        else:
            minutes_ago = random.uniform(60, 24 * 60)
        return now - timedelta(minutes=minutes_ago)

    def _kpi_throughput_base(self, center_id: int, line_id: int) -> int:
        """센터/라인별 편차를 주기 위한 기준 처리량."""
        center_factor = (center_id % 100) + 1
        line_factor = (line_id % 100) + 1
        return 120 + (center_factor * 8) + (line_factor * 3)

    def generate_kpi_report(self, center_id: int, db_session: Session, bucket: str) -> KpiReport:
        """KPI 리포트 생성 (window 버킷별 분산)"""
        lines = db_session.query(Line).filter(Line.center_id == center_id).all()
        line_id = random.choice([l.id for l in lines]) if lines else self.line_ids[0]
        base = self._kpi_throughput_base(center_id, line_id)

        if bucket == "5m":
            throughput = random.randint(base + 30, base + 120)
        elif bucket == "1h":
            throughput = random.randint(base + 80, base + 250)
        else:
            throughput = random.randint(base + 200, base + 500)

        kpi = KpiReport(
            window_end=self._pick_kpi_window_end(bucket),
            center_id=center_id,
            zone_id=random.choice(self.zone_ids),
            line_id=line_id,
            throughput_count=throughput,
            created_at=datetime.utcnow()
        )
        return kpi
    
    def generate_line_status(self, line_id: int, db_session: Session) -> LineStatus:
        """라인 상태 생성/업데이트"""
        active_bottlenecks = random.randint(0, 5)
        
        status = db_session.query(LineStatus).filter(LineStatus.id == line_id).first()
        
        if status:
            status.current_status = random.choice(STATUSES)
            status.active_bottlenecks = active_bottlenecks
            status.last_updated_at = datetime.utcnow()
        else:
            status = LineStatus(
                id=line_id,
                current_status=random.choice(STATUSES),
                active_bottlenecks=active_bottlenecks,
                last_basket_id=random.randint(10000, 99999),
                last_updated_at=datetime.utcnow()
            )
        
        return status
    
    def generate_bottleneck_event(self, center_id: int, db_session: Session) -> BottleneckEvent:
        """병목 이벤트 생성"""
        line_id = random.choice(self.line_ids)
        zone_id = random.choice(self.zone_ids)
        section_id = random.choice(self.section_ids)
        sensor_ids = self.get_center_sensor_ids(center_id, db_session)
        
        # 80% 확률로 과거 시간에 생성 (최대 24시간)
        if random.random() < 0.8:
            minutes_ago = random.randint(1, 24 * 60)
            occurred_at = datetime.utcnow() - timedelta(minutes=minutes_ago)
        else:
            occurred_at = datetime.utcnow()
        
        duration = random.randint(30, 900)  # 30초 ~ 15분
        
        event = BottleneckEvent(
            root_event_id=random.randint(1000, 9999),
            occurred_at=occurred_at,
            center_id=center_id,
            zone_id=zone_id,
            line_id=line_id,
            section_id=section_id,
            sensor_id=random.choice(sensor_ids),
            duration_sec=duration,
            cause_code=random.choice(CAUSE_CODES),
            affected_basket=random.randint(10000, 99999),
            result_code="RESOLVED",
            detail_reason=f"Auto-generated event at {datetime.utcnow()}",
            worker_id=random.randint(1000, 9999) if random.random() > 0.3 else None,
            status="COMPLETED",
            error_code=random.choice([None, None, None, "ERR_001"]),  # 25% 확률 에러
            error_message="System generated event" if random.random() > 0.7 else None
        )
        return event
    
    def generate_sensor_event(self, center_id: int, db_session: Session, line_id: int = None) -> SensorEvent:
        """센서 이벤트 생성"""
        sensor_ids = self.get_center_sensor_ids(center_id, db_session)
        sensor_id = random.choice(sensor_ids)
        line_id = line_id if line_id is not None else random.choice(self.line_ids)
        zone_id = random.choice(self.zone_ids)
        section_id = random.choice(self.section_ids)
        sensor_type = random.choice(SENSOR_TYPES)
        
        # 대부분 최근 이벤트
        if random.random() < 0.9:
            minutes_ago = random.randint(0, 60)
            occurred_at = datetime.utcnow() - timedelta(minutes=minutes_ago)
        else:
            occurred_at = datetime.utcnow() - timedelta(hours=random.randint(1, 24))
        
        # 값 생성 (센서 타입별)
        if sensor_type == "PRESSURE":
            numeric_value = random.uniform(50, 150)
        elif sensor_type == "TEMPERATURE":
            numeric_value = random.uniform(20, 80)
        elif sensor_type == "VIBRATION":
            numeric_value = random.uniform(0.1, 10.0)
        elif sensor_type == "FLOW":
            numeric_value = random.uniform(0, 100)
        else:  # POSITION
            numeric_value = random.uniform(0, 360)
        
        # 1% 확률로 에러 (현실적인 오류율)
        has_error = random.random() < 0.01
        
        event = SensorEvent(
            event_type_code=random.choice(EVENT_TYPE_CODES),
            occurred_at=occurred_at,
            center_id=center_id,
            zone_id=zone_id,
            line_id=line_id,
            section_id=section_id,
            sensor_id=sensor_id,
            basket_id=random.randint(10000, 99999),
            container_id=random.randint(100000, 999999) if random.random() > 0.5 else None,
            vehicle_id=random.randint(1000, 9999) if random.random() > 0.7 else None,
            worker_id=random.randint(1000, 9999) if random.random() > 0.8 else None,
            numeric_value=numeric_value,
            string_value=sensor_type,
            status="OK" if not has_error else "ERROR",
            error_code="SENSOR_ERR" if has_error else None,
            error_message="Sensor malfunction detected" if has_error else None,
            target_value=numeric_value * 0.9,
            sla=0.95,
            predicted_value=numeric_value * 1.02,
            attributes_json={"sensor_type": sensor_type, "batch_id": random.randint(1000, 9999)}
        )
        return event
    
    def batch_insert(self, objects: list, db_session: Session):
        """배치 삽입"""
        if not objects:
            return
        
        try:
            db_session.add_all(objects)
            db_session.commit()
            return len(objects)
        except Exception as e:
            db_session.rollback()
            print(f"[ERROR] 배치 삽입 실패: {e}")
            return 0
    
    def ensure_sensors_exist(self, db_session: Session, start_id: int = 1, end_id: int = 100):
        """센서 마스터 데이터 확인 및 생성"""
        from sqlalchemy import text
        try:
            # 기존 센서 ID 조회
            result = db_session.execute(text("SELECT COUNT(*) FROM sensor WHERE sensor_id >= :start AND sensor_id <= :end").bindparams(start=start_id, end=end_id))
            count = result.scalar() or 0
            
            # 센서가 충분하지 않으면 생성
            if count < (end_id - start_id):
                for sensor_id in range(start_id, end_id + 1):
                    try:
                        db_session.execute(text(
                            "INSERT INTO sensor (sensor_id, name, status) VALUES (:sid, :name, :status) ON CONFLICT (sensor_id) DO NOTHING"
                        ).bindparams(sid=sensor_id, name=f"Auto_Sensor_{sensor_id}", status="ACTIVE"))
                    except Exception as e:
                        # 이미 존재하거나 다른 오류면 무시
                        pass
                db_session.commit()
        except Exception as e:
            # 센서 테이블이 없거나 다른 오류면 무시
            pass

    def ensure_master_data(self, db_session: Session, center_id: int):
        """마스터 데이터가 없으면 최소 세트 생성"""
        from sqlalchemy import text
        now = datetime.utcnow()
        try:
            db_session.execute(text(
                "INSERT INTO center (center_id, name, location, status, opened_at) "
                "VALUES (:center_id, :name, :location, :status, :opened_at) "
                "ON CONFLICT (center_id) DO NOTHING"
            ).bindparams(
                center_id=center_id,
                name=f"Center_{center_id}",
                location="Auto",
                status="ACTIVE",
                opened_at=now.date()
            ))

            zone_count = db_session.execute(text("SELECT COUNT(*) FROM zone")).scalar() or 0
            if zone_count == 0:
                zones = []
                for idx in range(1, 5):
                    zone_id = (center_id * 100) + idx
                    zones.append({"zone_id": zone_id, "center_id": center_id, "name": f"Zone_{idx}", "type": "GENERAL", "status": "ACTIVE"})
                db_session.execute(text(
                    "INSERT INTO zone (zone_id, center_id, name, type, status) "
                    "VALUES (:zone_id, :center_id, :name, :type, :status) "
                    "ON CONFLICT (zone_id) DO NOTHING"
                ), zones)

            line_count = db_session.execute(text("SELECT COUNT(*) FROM line")).scalar() or 0
            if line_count == 0:
                lines = []
                for line_id in self.line_ids:
                    lines.append({
                        "line_id": line_id,
                        "center_id": center_id,
                        "name": f"Line_{line_id}",
                        "type": "MAIN",
                        "status": "ACTIVE",
                        "rail_length_m": random.uniform(80.0, 160.0),
                        "section_count": 10
                    })
                db_session.execute(text(
                    "INSERT INTO line (line_id, center_id, name, type, status, rail_length_m, section_count) "
                    "VALUES (:line_id, :center_id, :name, :type, :status, :rail_length_m, :section_count) "
                    "ON CONFLICT (line_id) DO NOTHING"
                ), lines)

            section_count = db_session.execute(text("SELECT COUNT(*) FROM section")).scalar() or 0
            if section_count == 0:
                sections = []
                for line_id in self.line_ids:
                    for order in range(1, 11):
                        section_id = (line_id * 100) + order
                        sections.append({
                            "section_id": section_id,
                            "line_id": line_id,
                            "name": f"Section_{order}",
                            "order_in_line": order,
                            "type": "NORMAL"
                        })
                db_session.execute(text(
                    "INSERT INTO section (section_id, line_id, name, order_in_line, type) "
                    "VALUES (:section_id, :line_id, :name, :order_in_line, :type) "
                    "ON CONFLICT (section_id) DO NOTHING"
                ), sections)

            equipment_count = db_session.execute(text("SELECT COUNT(*) FROM equipment")).scalar() or 0
            if equipment_count == 0:
                zone_ids = [row[0] for row in db_session.execute(text("SELECT zone_id FROM zone"))]
                sections = list(db_session.execute(text("SELECT section_id, line_id FROM section")))
                equipment_rows = []
                for section_id, line_id in sections:
                    equipment_id = section_id * 10
                    equipment_rows.append({
                        "equipment_id": equipment_id,
                        "center_id": center_id,
                        "zone_id": random.choice(zone_ids) if zone_ids else None,
                        "line_id": line_id,
                        "section_id": section_id,
                        "name": f"EQ_{equipment_id}",
                        "type": "CONVEYOR",
                        "status": "ACTIVE",
                        "install_date": now.date(),
                        "last_maintenance": now.date(),
                        "manufacturer": "Auto",
                        "model": "A-100"
                    })
                db_session.execute(text(
                    "INSERT INTO equipment (equipment_id, center_id, zone_id, line_id, section_id, name, type, status, install_date, last_maintenance, manufacturer, model) "
                    "VALUES (:equipment_id, :center_id, :zone_id, :line_id, :section_id, :name, :type, :status, :install_date, :last_maintenance, :manufacturer, :model) "
                    "ON CONFLICT (equipment_id) DO NOTHING"
                ), equipment_rows)

            sensor_count = db_session.execute(text("SELECT COUNT(*) FROM sensor")).scalar() or 0
            if sensor_count == 0:
                sensors = []
                sections = [row[0] for row in db_session.execute(text("SELECT section_id FROM section"))]
                for section_id in sections:
                    equipment_id = section_id * 10
                    for idx in range(1, 3):
                        sensor_id = (equipment_id * 10) + idx
                        sensors.append({
                            "sensor_id": sensor_id,
                            "section_id": section_id,
                            "equipment_id": equipment_id,
                            "sensor_type": random.choice(SENSOR_TYPES),
                            "name": f"SN_{sensor_id}",
                            "status": "ACTIVE"
                        })
                db_session.execute(text(
                    "INSERT INTO sensor (sensor_id, section_id, equipment_id, sensor_type, name, status) "
                    "VALUES (:sensor_id, :section_id, :equipment_id, :sensor_type, :name, :status) "
                    "ON CONFLICT (sensor_id) DO NOTHING"
                ), sensors)

            worker_count = db_session.execute(text("SELECT COUNT(*) FROM worker")).scalar() or 0
            if worker_count == 0:
                workers = []
                for idx in range(1, 21):
                    workers.append({
                        "worker_id": (center_id * 1000) + idx,
                        "name": f"Worker_{center_id}_{idx}",
                        "role": random.choice(["OP", "MAINT"]),
                        "center_id": center_id,
                        "status": "ON_DUTY"
                    })
                db_session.execute(text(
                    "INSERT INTO worker (worker_id, name, role, center_id, status) "
                    "VALUES (:worker_id, :name, :role, :center_id, :status) "
                    "ON CONFLICT (worker_id) DO NOTHING"
                ), workers)

            threshold_count = db_session.execute(text("SELECT COUNT(*) FROM threshold_config")).scalar() or 0
            if threshold_count == 0:
                db_session.execute(text(
                    "INSERT INTO threshold_config (config_key, config_value, description) "
                    "VALUES (:key, :value, :desc)"
                ), [
                    {"key": "MAX_BOTTLENECK_DURATION", "value": "300", "desc": "Auto seed"},
                    {"key": "MAX_SENSOR_ERROR_RATE", "value": "0.05", "desc": "Auto seed"}
                ])

            db_session.execute(text(
                "INSERT INTO weather (date, location, center_id, temp, rain, wind, notes) "
                "SELECT :date, :location, :center_id, :temp, :rain, :wind, :notes "
                "WHERE NOT EXISTS (SELECT 1 FROM weather WHERE date = :date AND center_id = :center_id)"
            ).bindparams(
                date=now.date(),
                location="Auto",
                center_id=center_id,
                temp=random.uniform(10.0, 28.0),
                rain=random.uniform(0.0, 5.0),
                wind=random.uniform(0.0, 8.0),
                notes="Auto seed"
            ))

            sim_count = db_session.execute(text("SELECT COUNT(*) FROM simulation_result")).scalar() or 0
            if sim_count == 0:
                db_session.execute(text(
                    "INSERT INTO simulation_result (scenario, executed_at, input_params_json, result_json, notes) "
                    "VALUES (:scenario, :executed_at, :input_params, :result, :notes)"
                ).bindparams(
                    scenario="AutoSeed",
                    executed_at=now,
                    input_params='{"seed": true}',
                    result='{"status": "ok"}',
                    notes="Auto seed"
                ))

            db_session.commit()
        except Exception:
            db_session.rollback()

    def load_reference_ids(self, db_session: Session) -> dict:
        """마스터 ID 목록 로드"""
        from sqlalchemy import text
        try:
            zone_ids = [row[0] for row in db_session.execute(text("SELECT zone_id FROM zone"))]
            line_ids = [row[0] for row in db_session.execute(text("SELECT line_id FROM line"))]
            section_ids = [row[0] for row in db_session.execute(text("SELECT section_id FROM section"))]
            sensor_ids = [row[0] for row in db_session.execute(text("SELECT sensor_id FROM sensor"))]
            equipment_ids = [row[0] for row in db_session.execute(text("SELECT equipment_id FROM equipment"))]
            worker_ids = [row[0] for row in db_session.execute(text("SELECT worker_id FROM worker"))]
        except Exception:
            zone_ids = []
            line_ids = []
            section_ids = []
            sensor_ids = []
            equipment_ids = []
            worker_ids = []

        return {
            "zone_ids": zone_ids or self.zone_ids,
            "line_ids": line_ids or self.line_ids,
            "section_ids": section_ids or self.section_ids,
            "sensor_ids": sensor_ids or list(range(1, 101)),
            "equipment_ids": equipment_ids,
            "worker_ids": worker_ids
        }

    def generate_additional_tables(self, db_session: Session, center_id: int, ref_ids: dict) -> dict:
        """그 외 테이블 데이터 생성"""
        from sqlalchemy import text
        now = datetime.utcnow()

        line_ids = ref_ids["line_ids"]
        section_ids = ref_ids["section_ids"]
        equipment_ids = ref_ids["equipment_ids"]
        worker_ids = ref_ids["worker_ids"]

        counts = {
            "order_event": 0,
            "maintenance_event": 0,
            "quality_event": 0,
            "operation_cost": 0,
            "loss_analysis": 0,
            "aggregation_summary": 0,
            "bottleneck_event_sensor": 0
        }

        try:
            # order_event
            order_count = random.randint(3, 8)
            for _ in range(order_count):
                db_session.execute(text(
                    "INSERT INTO order_event (customer_id, product_id, event_id, center_id, order_date, status, sla) "
                    "VALUES (:customer_id, :product_id, :event_id, :center_id, :order_date, :status, :sla)"
                ).bindparams(
                    customer_id=random.randint(1, 10000),
                    product_id=random.randint(1, 5000),
                    event_id=None,
                    center_id=center_id,
                    order_date=now,
                    status=random.choice(["CREATED", "PROCESSING", "COMPLETED"]),
                    sla=0.95
                ))
            counts["order_event"] = order_count

            # maintenance_event
            if equipment_ids:
                db_session.execute(text(
                    "INSERT INTO maintenance_event (equipment_id, worker_id, start_at, end_at, type, result, downtime_sec, notes) "
                    "VALUES (:equipment_id, :worker_id, :start_at, :end_at, :type, :result, :downtime_sec, :notes)"
                ).bindparams(
                    equipment_id=random.choice(equipment_ids),
                    worker_id=random.choice(worker_ids) if worker_ids else None,
                    start_at=now - timedelta(minutes=random.randint(10, 120)),
                    end_at=now,
                    type=random.choice(["INSPECTION", "REPAIR"]),
                    result="DONE",
                    downtime_sec=random.randint(60, 600),
                    notes="Auto maintenance"
                ))
                counts["maintenance_event"] = 1

            # quality_event
            if line_ids and section_ids:
                db_session.execute(text(
                    "INSERT INTO quality_event (event_id, center_id, line_id, section_id, product_id, defect_type, quantity, detected_at, notes) "
                    "VALUES (:event_id, :center_id, :line_id, :section_id, :product_id, :defect_type, :quantity, :detected_at, :notes)"
                ).bindparams(
                    event_id=None,
                    center_id=center_id,
                    line_id=random.choice(line_ids),
                    section_id=random.choice(section_ids),
                    product_id=random.randint(1, 5000),
                    defect_type=random.choice(["DAMAGED", "MISSING", "LABEL"]),
                    quantity=random.randint(1, 10),
                    detected_at=now,
                    notes="Auto quality"
                ))
                counts["quality_event"] = 1

            # operation_cost
            db_session.execute(text(
                "INSERT INTO operation_cost (center_id, zone_id, line_id, section_id, equipment_id, date, category, amount, notes) "
                "VALUES (:center_id, :zone_id, :line_id, :section_id, :equipment_id, :date, :category, :amount, :notes)"
            ).bindparams(
                center_id=center_id,
                zone_id=random.choice(ref_ids["zone_ids"]),
                line_id=random.choice(line_ids),
                section_id=random.choice(section_ids),
                equipment_id=random.choice(equipment_ids) if equipment_ids else None,
                date=now.date(),
                category=random.choice(["ELECTRICITY", "MAINTENANCE", "LABOR"]),
                amount=random.randint(1000, 100000),
                notes="Auto cost"
            ))
            counts["operation_cost"] = 1

            # loss_analysis
            if line_ids and section_ids:
                db_session.execute(text(
                    "INSERT INTO loss_analysis (center_id, line_id, section_id, window_start, window_end, bottleneck_count, total_bottleneck_sec, throughput_loss_est, loss_amount) "
                    "VALUES (:center_id, :line_id, :section_id, :window_start, :window_end, :bottleneck_count, :total_bottleneck_sec, :throughput_loss_est, :loss_amount)"
                ).bindparams(
                    center_id=center_id,
                    line_id=random.choice(line_ids),
                    section_id=random.choice(section_ids),
                    window_start=now - timedelta(hours=1),
                    window_end=now,
                    bottleneck_count=random.randint(0, 5),
                    total_bottleneck_sec=random.randint(0, 3600),
                    throughput_loss_est=random.randint(0, 1000),
                    loss_amount=random.randint(0, 100000)
                ))
                counts["loss_analysis"] = 1

            # aggregation_summary
            if line_ids:
                db_session.execute(text(
                    "INSERT INTO aggregation_summary (granularity, bucket_start, center_id, line_id, throughput_total, bottleneck_count, avg_bottleneck_duration_sec) "
                    "VALUES (:granularity, :bucket_start, :center_id, :line_id, :throughput_total, :bottleneck_count, :avg_bottleneck_duration_sec)"
                ).bindparams(
                    granularity="hour",
                    bucket_start=now.replace(minute=0, second=0, microsecond=0),
                    center_id=center_id,
                    line_id=random.choice(line_ids),
                    throughput_total=random.randint(1000, 10000),
                    bottleneck_count=random.randint(0, 5),
                    avg_bottleneck_duration_sec=random.uniform(10.0, 600.0)
                ))
                counts["aggregation_summary"] = 1

            # bottleneck_event_sensor
            db_session.execute(text(
                "INSERT INTO bottleneck_event_sensor (bottleneck_id, event_id) "
                "SELECT b.bottleneck_id, s.event_id "
                "FROM (SELECT bottleneck_id FROM bottleneck_event WHERE center_id = :center_id ORDER BY occurred_at DESC LIMIT 5) b "
                "CROSS JOIN (SELECT event_id FROM sensor_event WHERE center_id = :center_id ORDER BY occurred_at DESC LIMIT 5) s "
                "ON CONFLICT DO NOTHING"
            ).bindparams(center_id=center_id))
            counts["bottleneck_event_sensor"] = 1

            db_session.commit()
            return counts
        except Exception:
            db_session.rollback()
            return {"error": "additional_tables_failed"}
    
    def run_once(self, num_events: int = 50, verbose: bool = True):
        """한 번의 데이터 생성 및 적재"""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            # DB 엔진 초기화
            init_db()
            
            # Main DB 세션
            main_db = get_session("main")
            
            # 마스터 데이터 조회
            centers = main_db.query(Center).all()
            
            if not centers:
                print("[ERROR] 센터 정보가 없습니다.")
                main_db.close()
                return
            
            total_inserted = 0
            
            # 각 센터별로 데이터 생성
            for center in centers:
                center_id = center.id
                
                # center_id -> db_id 매핑 (정의된 센터만 처리)
                if center_id not in self.CENTER_DB_MAP:
                    continue
                db_id = self.CENTER_DB_MAP[center_id]
                
                # 센터별 DB 세션
                center_db = get_session(db_id)
                
                # 마스터 데이터 확인/생성
                self.ensure_master_data(center_db, center_id)
                
                # 참조 ID 로드
                ref_ids = self.load_reference_ids(center_db)
                self.zone_ids = ref_ids["zone_ids"]
                self.line_ids = ref_ids["line_ids"]
                self.section_ids = ref_ids["section_ids"]
                self.center_sensor_map[center_id] = ref_ids["sensor_ids"]

                if verbose:
                    print(
                        f"[INFO] center={center_id} db={db_id} refs: "
                        f"zones={len(ref_ids['zone_ids'])}, lines={len(ref_ids['line_ids'])}, "
                        f"sections={len(ref_ids['section_ids'])}, sensors={len(ref_ids['sensor_ids'])}"
                    )
                
                batch = []
                
                # 1. KPI Report (센터당 구간별 분산 생성)
                kpi_buckets = ("5m", "1h", "24h")
                for bucket in kpi_buckets:
                    for _ in range(random.randint(2, 4)):
                        kpi = self.generate_kpi_report(center_id, center_db, bucket)
                        batch.append(kpi)
                
                # 2. Line Status (모든 라인)
                for line_id in self.line_ids:
                    status = self.generate_line_status(line_id, center_db)
                    batch.append(status)
                
                # 3. Bottleneck Events (센터당 10-20)
                for _ in range(random.randint(10, 20)):
                    event = self.generate_bottleneck_event(center_id, center_db)
                    batch.append(event)
                
                # 4. Sensor Events (라인별 균등 생성)
                for line_id in self.line_ids:
                    for _ in range(random.randint(2, 5)):
                        event = self.generate_sensor_event(center_id, center_db, line_id=line_id)
                        batch.append(event)
                
                # 배치 삽입
                inserted = self.batch_insert(batch, center_db)
                total_inserted += inserted or 0
                
                # 추가 테이블 데이터 생성
                extra_counts = self.generate_additional_tables(center_db, center_id, ref_ids)

                if verbose:
                    print(
                        f"[INFO] center={center_id} db={db_id} inserted: "
                        f"kpi={len([x for x in batch if isinstance(x, KpiReport)])}, "
                        f"line_status={len([x for x in batch if isinstance(x, LineStatus)])}, "
                        f"bottleneck={len([x for x in batch if isinstance(x, BottleneckEvent)])}, "
                        f"sensor={len([x for x in batch if isinstance(x, SensorEvent)])}, "
                        f"extra={extra_counts}"
                    )
                
                center_db.close()
            
            main_db.close()
            
            if verbose:
                print(f"[OK] [{timestamp}] {total_inserted}개 레코드 적재 완료")
            
            return total_inserted
        
        except Exception as e:
            print(f"[ERROR] [{timestamp}] 에러 발생: {e}")
            return 0
    
    def run_continuous(self, interval_seconds: int = 30, iterations: int = None):
        """지속적으로 데이터 생성"""
        print(f"[INFO] 실시간 데이터 생성 시작 (간격: {interval_seconds}초)")
        
        iteration = 0
        total_inserted = 0
        
        try:
            while iterations is None or iteration < iterations:
                iteration += 1
                inserted = self.run_once(verbose=True)
                total_inserted += inserted
                
                if iterations:
                    print(f"   진행 상황: {iteration}/{iterations}")
                
                if iterations is None or iteration < iterations:
                    time.sleep(interval_seconds)
        
        except KeyboardInterrupt:
            print(f"\n[STOP]  데이터 생성 중단")
        
        finally:
            print(f"[INFO] 총 {total_inserted}개 레코드 적재됨")


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="실시간 데이터 생성기")
    parser.add_argument("--mode", choices=["once", "continuous"], default="continuous",
                        help="실행 모드")
    parser.add_argument("--interval", type=int, default=30,
                        help="데이터 생성 간격 (초, continuous 모드에서만 사용)")
    parser.add_argument("--iterations", type=int, default=None,
                        help="반복 횟수 (None이면 무한 반복)")
    parser.add_argument("--events", type=int, default=50,
                        help="이벤트 수")
    
    args = parser.parse_args()
    
    generator = RealtimeDataGenerator()
    
    if args.mode == "once":
        print("[INFO] 한 번의 데이터 생성 및 적재 실행")
        generator.run_once(num_events=args.events)
    else:
        print("[INFO] 지속적인 데이터 생성 모드 실행")
        generator.run_continuous(
            interval_seconds=args.interval,
            iterations=args.iterations
        )


if __name__ == "__main__":
    main()
