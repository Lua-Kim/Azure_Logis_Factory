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

class Line(Base):
    __tablename__ = "line"
    id = Column("line_id", BigInteger, primary_key=True, index=True)
    center_id = Column(BigInteger, ForeignKey("center.center_id"))
    name = Column(String, nullable=False)
    # ... 생략 ...

# --- 트랜잭션 및 상태 테이블 ---

class KpiReport(Base):
    __tablename__ = "kpi_report"
    # 변수명은 id로 통일, 실제 DB 컬럼은 kpi_id
    id = Column("kpi_id", BigInteger, primary_key=True, index=True)
    window_end = Column(DateTime, index=True)
    center_id = Column(BigInteger)
    line_id = Column(BigInteger)
    throughput_count = Column(BigInteger)
    created_at = Column(DateTime, server_default=func.now())

class BottleneckEvent(Base):
    __tablename__ = "bottleneck_event"
    id = Column("bottleneck_id", BigInteger, primary_key=True, index=True)
    occurred_at = Column(DateTime, index=True)

class SensorEvent(Base): # 추가
    __tablename__ = "sensor_event"
    id = Column(Integer, primary_key=True, index=True) # event_id -> id
    event_type_code = Column(String, nullable=False)
    occurred_at = Column(DateTime, index=True)
    center_id = Column(Integer)
    line_id = Column(Integer)
    numeric_value = Column(Float)
    status = Column(String)