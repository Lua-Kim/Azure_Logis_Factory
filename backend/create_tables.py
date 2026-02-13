import os
import psycopg2
from dotenv import load_dotenv

# .env 파일 로드
env_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(env_path)

DB_URL = os.getenv('AZ_POSTGRE_DATABASE_URL')

# --- 1. Master Tables ---
CREATE_CENTER_TABLE = """
CREATE TABLE IF NOT EXISTS center (
    center_id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(200),
    status VARCHAR(20),
    opened_at DATE
);
"""

CREATE_ZONE_TABLE = """
CREATE TABLE IF NOT EXISTS zone (
    zone_id BIGSERIAL PRIMARY KEY,
    center_id BIGINT,
    name VARCHAR(100),
    type VARCHAR(50),
    status VARCHAR(20)
);
"""

CREATE_LINE_TABLE = """
CREATE TABLE IF NOT EXISTS line (
    line_id BIGSERIAL PRIMARY KEY,
    center_id BIGINT,
    name VARCHAR(100),
    type VARCHAR(50),
    status VARCHAR(20),
    rail_length_m DOUBLE PRECISION,
    section_count INT
);
"""

CREATE_SECTION_TABLE = """
CREATE TABLE IF NOT EXISTS section (
    section_id BIGSERIAL PRIMARY KEY,
    line_id BIGINT,
    name VARCHAR(100),
    order_in_line INT,
    type VARCHAR(50)
);
"""

CREATE_SENSOR_TABLE = """
CREATE TABLE IF NOT EXISTS sensor (
    sensor_id BIGSERIAL PRIMARY KEY,
    section_id BIGINT,
    equipment_id BIGINT,
    sensor_type VARCHAR(50),
    name VARCHAR(100),
    status VARCHAR(20)
);
"""

CREATE_EQUIPMENT_TABLE = """
CREATE TABLE IF NOT EXISTS equipment (
    equipment_id BIGSERIAL PRIMARY KEY,
    center_id BIGINT,
    zone_id BIGINT,
    line_id BIGINT,
    section_id BIGINT,
    name VARCHAR(100),
    type VARCHAR(50),
    status VARCHAR(20),
    install_date DATE,
    last_maintenance DATE,
    manufacturer VARCHAR(100),
    model VARCHAR(100)
);
"""

CREATE_WORKER_TABLE = """
CREATE TABLE IF NOT EXISTS worker (
    worker_id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100),
    role VARCHAR(50),
    center_id BIGINT,
    status VARCHAR(20)
);
"""

# --- 2. Management & KPI Tables ---
CREATE_LINE_STATUS_TABLE = """
CREATE TABLE IF NOT EXISTS line_status (
    line_id BIGINT PRIMARY KEY,
    current_status VARCHAR(20) DEFAULT 'NORMAL',
    active_bottlenecks INT DEFAULT 0,
    last_basket_id BIGINT,
    last_updated_at TIMESTAMP
);
"""

CREATE_THRESHOLD_CONFIG_TABLE = """
CREATE TABLE IF NOT EXISTS threshold_config (
    config_id BIGSERIAL PRIMARY KEY,
    config_key VARCHAR(50) UNIQUE NOT NULL,
    config_value VARCHAR(100) NOT NULL,
    description VARCHAR(200)
);
"""

CREATE_KPI_REPORT_TABLE = """
CREATE TABLE IF NOT EXISTS kpi_report (
    kpi_id BIGSERIAL PRIMARY KEY,
    window_end TIMESTAMP NOT NULL,
    center_id BIGINT,
    zone_id BIGINT,
    line_id BIGINT,
    throughput_count BIGINT,
    created_at TIMESTAMP
);
"""

# --- 3. Event Tables ---
CREATE_SENSOR_EVENT_TABLE = """
CREATE TABLE IF NOT EXISTS sensor_event (
    event_id BIGSERIAL PRIMARY KEY,
    event_type_code VARCHAR(50) NOT NULL,
    occurred_at TIMESTAMP NOT NULL,
    center_id BIGINT,
    zone_id BIGINT,
    line_id BIGINT,
    section_id BIGINT,
    sensor_id BIGINT,
    basket_id BIGINT,
    container_id BIGINT,
    vehicle_id BIGINT,
    worker_id BIGINT,
    numeric_value DOUBLE PRECISION,
    string_value VARCHAR(200),
    status VARCHAR(20),
    error_code VARCHAR(50),
    error_message VARCHAR(500),
    prev_event_id BIGINT,
    next_event_id BIGINT,
    route_id BIGINT,
    target_value DOUBLE PRECISION,
    sla DOUBLE PRECISION,
    predicted_value DOUBLE PRECISION,
    attributes_json JSONB
);
"""

CREATE_BOTTLENECK_EVENT_TABLE = """
CREATE TABLE IF NOT EXISTS bottleneck_event (
    bottleneck_id BIGSERIAL PRIMARY KEY,
    root_event_id BIGINT,
    occurred_at TIMESTAMP NOT NULL,
    center_id BIGINT,
    zone_id BIGINT,
    line_id BIGINT,
    section_id BIGINT,
    sensor_id BIGINT,
    duration_sec BIGINT,
    cause_code VARCHAR(50),
    affected_basket BIGINT,
    result_code VARCHAR(50),
    detail_reason VARCHAR(500),
    worker_id BIGINT,
    status VARCHAR(20),
    error_code VARCHAR(50),
    error_message VARCHAR(500)
);
"""

CREATE_BOTTLENECK_EVENT_SENSOR_TABLE = """
CREATE TABLE IF NOT EXISTS bottleneck_event_sensor (
    bottleneck_id BIGINT NOT NULL,
    event_id BIGINT NOT NULL,
    PRIMARY KEY (bottleneck_id, event_id)
);
"""

# --- 4. Operational & Analysis Tables ---
CREATE_MAINTENANCE_EVENT_TABLE = """
CREATE TABLE IF NOT EXISTS maintenance_event (
    maintenance_id BIGSERIAL PRIMARY KEY,
    equipment_id BIGINT NOT NULL,
    worker_id BIGINT,
    start_at TIMESTAMP NOT NULL,
    end_at TIMESTAMP,
    type VARCHAR(50),
    result VARCHAR(100),
    downtime_sec BIGINT,
    notes VARCHAR(500)
);
"""

CREATE_QUALITY_EVENT_TABLE = """
CREATE TABLE IF NOT EXISTS quality_event (
    quality_id BIGSERIAL PRIMARY KEY,
    event_id BIGINT,
    center_id BIGINT,
    line_id BIGINT,
    section_id BIGINT,
    product_id BIGINT,
    defect_type VARCHAR(50),
    quantity BIGINT,
    detected_at TIMESTAMP,
    notes VARCHAR(200)
);
"""

CREATE_OPERATION_COST_TABLE = """
CREATE TABLE IF NOT EXISTS operation_cost (
    cost_id BIGSERIAL PRIMARY KEY,
    center_id BIGINT,
    zone_id BIGINT,
    line_id BIGINT,
    section_id BIGINT,
    equipment_id BIGINT,
    date DATE,
    category VARCHAR(50),
    amount BIGINT,
    notes VARCHAR(200)
);
"""

CREATE_ORDER_EVENT_TABLE = """
CREATE TABLE IF NOT EXISTS order_event (
    order_id BIGSERIAL PRIMARY KEY,
    customer_id BIGINT,
    product_id BIGINT,
    event_id BIGINT,
    center_id BIGINT,
    order_date TIMESTAMP,
    status VARCHAR(20),
    sla DOUBLE PRECISION
);
"""

CREATE_WEATHER_TABLE = """
CREATE TABLE IF NOT EXISTS weather (
    weather_id BIGSERIAL PRIMARY KEY,
    date DATE,
    location VARCHAR(100),
    center_id BIGINT,
    temp FLOAT,
    rain FLOAT,
    wind FLOAT,
    notes VARCHAR(200)
);
"""

CREATE_SIMULATION_RESULT_TABLE = """
CREATE TABLE IF NOT EXISTS simulation_result (
    simulation_id BIGSERIAL PRIMARY KEY,
    scenario VARCHAR(100),
    executed_at TIMESTAMP,
    input_params_json JSONB,
    result_json JSONB,
    notes VARCHAR(200)
);
"""

# --- 5. Indexes ---
CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_sensor_event_occurred_at ON sensor_event (occurred_at);",
    "CREATE INDEX IF NOT EXISTS idx_sensor_event_center_line ON sensor_event (center_id, line_id);",
    "CREATE INDEX IF NOT EXISTS idx_bottleneck_event_occurred_at ON bottleneck_event (occurred_at);",
    "CREATE INDEX IF NOT EXISTS idx_kpi_window ON kpi_report (window_end);",
    "CREATE INDEX IF NOT EXISTS idx_line_status_upd ON line_status (last_updated_at);"
]

def create_tables():
    conn = None
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        tables = [
            CREATE_CENTER_TABLE, CREATE_ZONE_TABLE, CREATE_LINE_TABLE, 
            CREATE_SECTION_TABLE, CREATE_SENSOR_TABLE, CREATE_EQUIPMENT_TABLE, 
            CREATE_WORKER_TABLE, 
            CREATE_LINE_STATUS_TABLE, CREATE_THRESHOLD_CONFIG_TABLE, CREATE_KPI_REPORT_TABLE,
            CREATE_SENSOR_EVENT_TABLE, CREATE_BOTTLENECK_EVENT_TABLE,
            CREATE_BOTTLENECK_EVENT_SENSOR_TABLE, CREATE_MAINTENANCE_EVENT_TABLE,
            CREATE_QUALITY_EVENT_TABLE, CREATE_OPERATION_COST_TABLE,
            CREATE_ORDER_EVENT_TABLE, CREATE_WEATHER_TABLE, CREATE_SIMULATION_RESULT_TABLE
        ]
        
        print("테이블 생성을 시작합니다...")
        for table_sql in tables:
            cur.execute(table_sql)
            
        for index_sql in CREATE_INDEXES:
            cur.execute(index_sql)
            
        conn.commit()
        print("✅ 모든 테이블 및 인덱스가 성공적으로 생성되었습니다.")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        if conn: conn.rollback()
    finally:
        if cur: cur.close()
        if conn: conn.close()

if __name__ == "__main__":
    create_tables()