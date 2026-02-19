import os
import random
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
DB_URL = os.getenv("AZ_POSTGRE_DATABASE_URL")
engine = create_engine(DB_URL, pool_size=20)

def generate_full_mega_data():
    # 규모 설정
    C_ID = 101
    NUM_ZONES = 10
    LINES_PER_ZONE = 20
    SECTIONS_PER_LINE = 10
    SENSORS_PER_SECTION = 4
    NUM_WORKERS = 500

    now = datetime.now()
    yesterday = now - timedelta(days=1)

    with engine.begin() as conn:
        print("1. 기초 마스터 정보 (Center, Weather, Threshold) 삽입...")
        conn.execute(text("INSERT INTO center (center_id, name, location, status) VALUES (:id, 'Mega Hub A1', 'Gyeonggi', 'ACTIVE') ON CONFLICT DO NOTHING"), {"id": C_ID})
        conn.execute(text("INSERT INTO weather (weather_id, date, center_id, temp, rain) VALUES (1, CURRENT_DATE, :c_id, 24.5, 0.0)"), {"c_id": C_ID})
        conn.execute(text("INSERT INTO threshold_config (config_id, config_key, config_value) VALUES (1, 'MAX_BOTTLENECK_DURATION', '300')"))

        print("2. 인력 및 자산 (Worker, Simulation) 삽입...")
        workers = [{"id": i, "n": f"Worker_{i}", "r": random.choice(['OP', 'MAINT']), "c": C_ID} for i in range(1, NUM_WORKERS+1)]
        conn.execute(text("INSERT INTO worker (worker_id, name, role, center_id, status) VALUES (:id, :n, :r, :c, 'ON_DUTY')"), workers)
        conn.execute(text("INSERT INTO simulation_result (simulation_id, scenario, result_json) VALUES (1, 'Peak_Season_Test', :js)"), {"js": json.dumps({"efficiency": 0.95})})

        print("3. 물리 계층 (Zone, Line, Section, Equipment, Sensor) 삽입...")
        # 이 섹션은 앞서 드린 로직으로 8,000개 센서까지 계층 구조를 생성합니다.
        zones, lines, sections, equips, sensors, l_status = [], [], [], [], [], []
        for z in range(1, NUM_ZONES + 1):
            z_id = (C_ID * 100) + z
            zones.append({"id": z_id, "c": C_ID, "n": f"Zone_{z}"})
            for l in range(1, LINES_PER_ZONE + 1):
                l_id = (z_id * 100) + l
                lines.append({"id": l_id, "c": C_ID, "n": f"Line_{l}"})
                l_status.append({"id": l_id, "st": 'RUNNING', "bc": 0})
                for s in range(1, SECTIONS_PER_LINE + 1):
                    s_id = (l_id * 100) + s
                    sections.append({"id": s_id, "l": l_id, "n": f"Sec_{s}"})
                    eq_id = s_id * 10
                    equips.append({"id": eq_id, "c": C_ID, "z": z_id, "l": l_id, "s": s_id, "n": f"EQ_{eq_id}"})
                    for sn in range(1, SENSORS_PER_SECTION + 1):
                        sn_id = (eq_id * 10) + sn
                        sensors.append({"id": sn_id, "s": s_id, "e": eq_id, "n": f"SN_{sn_id}"})

        conn.execute(text("INSERT INTO zone (zone_id, center_id, name) VALUES (:id, :c, :n)"), zones)
        conn.execute(text("INSERT INTO line (line_id, center_id, name) VALUES (:id, :c, :n)"), lines)
        conn.execute(text("INSERT INTO line_status (line_id, current_status, active_bottlenecks) VALUES (:id, :st, :bc)"), l_status)
        conn.execute(text("INSERT INTO section (section_id, line_id, name) VALUES (:id, :l, :n)"), sections)
        conn.execute(text("INSERT INTO equipment (equipment_id, center_id, zone_id, line_id, section_id, name) VALUES (:id, :c, :z, :l, :s, :n)"), equips)
        conn.execute(text("INSERT INTO sensor (sensor_id, section_id, equipment_id, name) VALUES (:id, :s, :e, :n)"), sensors)

        print("4. 운영 이벤트 (Order, Sensor_Event, Bottleneck) 삽입...")
        # Order 및 관련 이벤트
        orders = [{"id": i, "c_id": C_ID, "ts": yesterday + timedelta(minutes=i)} for i in range(1, 101)]
        conn.execute(text("INSERT INTO order_event (order_id, center_id, order_date, status) VALUES (:id, :c_id, :ts, 'COMPLETED')"), orders)

        # Sensor Events (대량 10,000건)
        sn_ids = [s['id'] for s in sensors]
        s_events = [{"id": i, "ts": yesterday + timedelta(seconds=i*5), "c": C_ID, "sn": random.choice(sn_ids)} for i in range(1, 10001)]
        conn.execute(text("INSERT INTO sensor_event (event_id, occurred_at, center_id, sensor_id, event_type_code) VALUES (:id, :ts, :c, :sn, 'PASS')"), s_events)

        # Bottleneck & Sensor Mapping
        b_events = [{"id": i, "ts": yesterday + timedelta(minutes=i*10), "c": C_ID, "l": random.choice([l['id'] for l in lines])} for i in range(1, 51)]
        conn.execute(text("INSERT INTO bottleneck_event (bottleneck_id, occurred_at, center_id, line_id, duration_sec) VALUES (:id, :ts, :c, :l, 120)"), b_events)
        
        b_sensors = [{"bid": i, "sid": random.choice(s_events)['id']} for i in range(1, 51)]
        conn.execute(text("INSERT INTO bottleneck_event_sensor (bottleneck_id, event_id) VALUES (:bid, :sid)"), b_sensors)

        print("5. 사후 분석 및 유지보수 (Quality, Maintenance, Loss, Cost, KPI) 삽입...")
        conn.execute(text("INSERT INTO quality_event (quality_id, center_id, line_id, defect_type) VALUES (1, :c, :l, 'DAMAGED')"), {"c": C_ID, "l": lines[0]['id']})
        conn.execute(text("INSERT INTO maintenance_event (maintenance_id, equipment_id, start_at) VALUES (1, :e, :ts)"), {"e": equips[0]['id'], "ts": yesterday})
        conn.execute(text("INSERT INTO loss_analysis (loss_id, center_id, line_id, total_bottleneck_sec) VALUES (1, :c, :l, 3600)"), {"c": C_ID, "l": lines[0]['id']})
        conn.execute(text("INSERT INTO operation_cost (cost_id, center_id, amount, category) VALUES (1, :c, 5000000, 'ELECTRICITY')"), {"c": C_ID})
        conn.execute(text("INSERT INTO kpi_report (kpi_id, window_end, center_id, throughput_count) VALUES (1, :ts, :c, 15000)"), {"ts": now, "c": C_ID})

    print(f"[{datetime.now()}] ✅ 20개 이상 모든 테이블에 대한 메가센터 데이터 로드 완료!")

if __name__ == "__main__":
    generate_full_mega_data()