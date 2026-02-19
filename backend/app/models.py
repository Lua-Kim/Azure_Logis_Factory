from sqlalchemy import BigInteger, Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()
# --- 마스터 데이터 테이블 ---

class Center(Base):
    __tablename__ = "center"
    # 변수명은 id로 통일, 실제 DB 컬럼은 center_id
    id = Column("center_id", BigInteger, primary_key=True, index=True)
    name = Column(String, nullable=False)
    location = Column(String)
    status = Column(String, default="active")
    opened_at = Column(DateTime)

class Zone(Base):
    __tablename__ = "zone"
    id = Column("zone_id", BigInteger, primary_key=True, index=True) 
    center_id = Column(BigInteger, ForeignKey("center.center_id"))
    name = Column(String, nullable=False)
    type = Column(String)
    status = Column(String, default="active")

class Section(Base):
    __tablename__ = "section"
    id = Column("section_id", BigInteger, primary_key=True, index=True)
    line_id = Column(BigInteger, ForeignKey("line.line_id"))
    name = Column(String, nullable=False)
    order_in_line = Column(Integer)
    type = Column(String)

class Line(Base):
    __tablename__ = "line"
    id = Column("line_id", BigInteger, primary_key=True, index=True)
    center_id = Column(BigInteger, ForeignKey("center.center_id"))
    name = Column(String, nullable=False)
    type = Column(String)
    status = Column(String, default="active")
    rail_length_m = Column(Float)
    section_count = Column(Integer)

# --- 트랜잭션 및 상태 테이블 ---

class KpiReport(Base):
    __tablename__ = "kpi_report"
    id = Column("kpi_id", BigInteger, primary_key=True, index=True)
    window_end = Column(DateTime, index=True)
    center_id = Column(BigInteger)
    zone_id = Column(BigInteger)
    line_id = Column(BigInteger)
    throughput_count = Column(BigInteger)
    created_at = Column(DateTime, server_default=func.now())

class LineStatus(Base):
    __tablename__ = "line_status"
    id = Column("line_id", BigInteger, primary_key=True, index=True)
    current_status = Column(String, default="NORMAL")
    active_bottlenecks = Column(Integer, default=0)
    last_basket_id = Column(BigInteger)
    last_updated_at = Column(DateTime)

class BottleneckEvent(Base):
    __tablename__ = "bottleneck_event"
    id = Column("bottleneck_id", BigInteger, primary_key=True, index=True)
    root_event_id = Column(BigInteger)
    occurred_at = Column(DateTime, index=True)
    center_id = Column(BigInteger)
    zone_id = Column(BigInteger)
    line_id = Column(BigInteger)
    section_id = Column(BigInteger)
    sensor_id = Column(BigInteger)
    duration_sec = Column(BigInteger)
    cause_code = Column(String)
    affected_basket = Column(BigInteger)
    result_code = Column(String)
    detail_reason = Column(String)
    worker_id = Column(BigInteger)
    status = Column(String)
    error_code = Column(String)
    error_message = Column(String)

class SensorEvent(Base):
    __tablename__ = "sensor_event"
    id = Column("event_id", BigInteger, primary_key=True, index=True)
    event_type_code = Column(String, nullable=False)
    occurred_at = Column(DateTime, index=True)
    center_id = Column(BigInteger)
    zone_id = Column(BigInteger)
    line_id = Column(BigInteger)
    section_id = Column(BigInteger)
    sensor_id = Column(BigInteger)
    basket_id = Column(BigInteger)
    container_id = Column(BigInteger)
    vehicle_id = Column(BigInteger)
    worker_id = Column(BigInteger)
    numeric_value = Column(Float)
    string_value = Column(String)
    status = Column(String)
    error_code = Column(String)
    error_message = Column(String)
    prev_event_id = Column(BigInteger)
    next_event_id = Column(BigInteger)
    route_id = Column(BigInteger)
    target_value = Column(Float)
    sla = Column(Float)
    predicted_value = Column(Float)
    attributes_json = Column(JSON)