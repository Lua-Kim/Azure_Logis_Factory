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
    
    def __init__(self):
        self.center_ids = [100, 110, 120, 130]
        self.line_ids = list(range(1010101, 1010118))  # 17 lines
        self.zone_ids = list(range(1, 5))
        self.section_ids = list(range(1, 11))  # 10 sections per line
        self.center_sensor_map = {}  # 센터별 실제 센서 ID 매핑
        
    def generate_kpi_report(self, center_id: int, db_session: Session) -> KpiReport:
        """KPI 리포트 생성"""
        lines = db_session.query(Line).filter(Line.center_id == center_id).all()
        
        throughput = random.randint(100, 500)
        
        kpi = KpiReport(
            window_end=datetime.utcnow(),
            center_id=center_id,
            zone_id=random.choice(self.zone_ids),
            line_id=random.choice([l.id for l in lines]) if lines else self.line_ids[0],
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
    
    def generate_bottleneck_event(self, center_id: int) -> BottleneckEvent:
        """병목 이벤트 생성"""
        line_id = random.choice(self.line_ids)
        zone_id = random.choice(self.zone_ids)
        section_id = random.choice(self.section_ids)
        
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
            sensor_id=random.randint(1, 20),  # 1-20 센서 ID
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
    
    def generate_sensor_event(self, center_id: int, db_session: Session) -> SensorEvent:
        """센서 이벤트 생성"""
        # 센터별 실제 센서 ID 조회 (한 번만)
        if center_id not in self.center_sensor_map:
            # 모든 센서 ID 조회
            from sqlalchemy import text
            result = db_session.execute(text("SELECT DISTINCT sensor_id FROM sensor_event WHERE sensor_id IS NOT NULL LIMIT 10000"))
            sensor_ids = [row[0] for row in result]
            if not sensor_ids:
                sensor_ids = list(range(1, 101))  # 기본값
            self.center_sensor_map[center_id] = sensor_ids
        
        sensor_id = random.choice(self.center_sensor_map[center_id])
        line_id = random.choice(self.line_ids)
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
        
        # 5% 확률로 에러
        has_error = random.random() < 0.05
        
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
                
                # 센터별 DB 세션
                center_db = get_session(str(center_id))
                
                # 센서 마스터 데이터 확인/생성
                self.ensure_sensors_exist(center_db)
                
                batch = []
                
                # 1. KPI Report (센터당 2-5개)
                for _ in range(random.randint(2, 5)):
                    kpi = self.generate_kpi_report(center_id, center_db)
                    batch.append(kpi)
                
                # 2. Line Status (모든 라인)
                for line_id in self.line_ids:
                    status = self.generate_line_status(line_id, center_db)
                    batch.append(status)
                
                # 3. Bottleneck Events (센터당 10-20)
                for _ in range(random.randint(10, 20)):
                    event = self.generate_bottleneck_event(center_id)
                    batch.append(event)
                
                # 4. Sensor Events (센터당 30-100)
                for _ in range(random.randint(30, 100)):
                    event = self.generate_sensor_event(center_id, center_db)
                    batch.append(event)
                
                # 배치 삽입
                inserted = self.batch_insert(batch, center_db)
                total_inserted += inserted or 0
                
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
