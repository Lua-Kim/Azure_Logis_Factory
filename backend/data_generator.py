import argparse
import os
import random
import time
import json
import uuid
import threading
from datetime import datetime, timezone
from dotenv import load_dotenv
from azure.iot.device import IoTHubDeviceClient
import psycopg2
from psycopg2.extras import RealDictCursor

# .env 파일 로드
env_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(env_path)

DB_URL = os.getenv('AZ_POSTGRE_DATABASE_URL')

device_client = None

def get_now():
    """현재 시간을 로그 포맷에 맞춰 반환"""
    return datetime.now().strftime("%H:%M:%S")

def create_event(basket_id, event_type, center_id, zone_id, line_id, section_id):
    """
    ASA 쿼리와 DB 컬럼에 100% 대응하는 데이터 생성
    """
    return {
        'event_id': str(uuid.uuid4()),
        'event_type_code': event_type,
        'occurred_at': datetime.now(timezone.utc).isoformat(),
        'center_id': center_id,
        'zone_id': zone_id,
        'line_id': line_id,
        'section_id': section_id,
        'sensor_id': None,
        'basket_id': basket_id,
        'numeric_value': round(random.uniform(20.0, 25.0), 2),
        'status': 'RUNNING',
        'error_code': 'NONE',
        'attributes_json': {"version": "1.4", "mode": "mass_parallel"}
    }


def load_runtime_config():
    if not DB_URL:
        return None

    conn = None
    try:
        conn = psycopg2.connect(DB_URL)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT center_id FROM center ORDER BY center_id")
            centers = [row["center_id"] for row in cur.fetchall()]

            cur.execute("SELECT zone_id, center_id FROM zone")
            zones = {}
            for row in cur.fetchall():
                zones.setdefault(row["center_id"], []).append(row["zone_id"])

            cur.execute("SELECT line_id, center_id FROM line")
            lines = {}
            for row in cur.fetchall():
                lines.setdefault(row["center_id"], []).append(row["line_id"])

            cur.execute("SELECT section_id, line_id FROM section")
            sections = {}
            for row in cur.fetchall():
                sections.setdefault(row["line_id"], []).append(row["section_id"])

            cur.execute(
                """
                SELECT s.sensor_id, sec.section_id
                FROM sensor s
                JOIN section sec ON sec.section_id = s.section_id
                """
            )
            sensors = {}
            for row in cur.fetchall():
                sensors.setdefault(row["section_id"], []).append(row["sensor_id"])

        if not centers:
            return None

        return {
            "centers": centers,
            "zones": zones,
            "lines": lines,
            "sections": sections,
            "sensors": sensors,
        }
    except Exception as e:
        print(f"❌ [설정 로드 실패] DB 설정을 확인하세요: {e}")
        return None
    finally:
        if conn:
            conn.close()


def pick_runtime_path(runtime_config, fixed_center_id=None):
    if not runtime_config:
        center_id = fixed_center_id if fixed_center_id is not None else 1
        return center_id, random.randint(1, 3), random.randint(1, 5), random.randint(1, 10), random.randint(1, 5)

    if fixed_center_id is not None and fixed_center_id in runtime_config["centers"]:
        center_id = fixed_center_id
    else:
        center_id = random.choice(runtime_config["centers"])
    zone_list = runtime_config["zones"].get(center_id, [1])
    line_list = runtime_config["lines"].get(center_id, [1])

    zone_id = random.choice(zone_list) if zone_list else 1
    line_id = random.choice(line_list) if line_list else 1

    section_list = runtime_config["sections"].get(line_id, [1])
    section_id = random.choice(section_list) if section_list else 1

    sensor_list = runtime_config["sensors"].get(section_id, [])
    sensor_id = random.choice(sensor_list) if sensor_list else None

    return center_id, zone_id, line_id, section_id, sensor_id

def simulate_single_basket(basket_id, runtime_config, fixed_center_id=None):
    """
    한 개의 바스켓이 특정 경로를 통과하는 독립적인 흐름 시뮬레이션
    """
    # 설정 데이터 기반으로 유효한 경로 선택
    center_id, zone_id, line_id, section_id, sensor_id = pick_runtime_path(
        runtime_config,
        fixed_center_id
    )
    
    loc_str = f"C{center_id}-Z{zone_id}-L{line_id}-S{section_id}"

    try:
        # 1. ARRIVAL 전송 (진입)
        arrival = create_event(basket_id, 'ARRIVAL', center_id, zone_id, line_id, section_id)
        arrival['sensor_id'] = sensor_id if sensor_id is not None else random.randint(1, 5)
        device_client.send_message(json.dumps(arrival))
        print(f"[{get_now()}] 🔵 [진입 보고] {loc_str} | 바스켓 #{basket_id}")

        # 2. 대기 (병목 테스트 여부 결정)
        # 10% 확률로 35초 지연 발생 (ASA 병목 감지용)
        is_bottleneck = random.random() < 0.1
        wait_time = random.uniform(32.0, 38.0) if is_bottleneck else random.uniform(2.0, 8.0)
        
        if is_bottleneck:
            print(f"[{get_now()}] ⚠️  [병목 발생] {loc_str} | 바스켓 #{basket_id} 정체 시작... (예상 대기: {wait_time:.1f}초)")
        
        # 물리적 시간 대기 (비차단 스레드 방식)
        time.sleep(wait_time)

        # 3. DEPARTURE 전송 (통과/운행 재개)
        departure = create_event(basket_id, 'DEPARTURE', center_id, zone_id, line_id, section_id)
        departure['sensor_id'] = sensor_id if sensor_id is not None else random.randint(1, 5)
        device_client.send_message(json.dumps(departure))
        
        if is_bottleneck:
            print(f"[{get_now()}] ✨ [운행 재개] {loc_str} | 바스켓 #{basket_id} 병목 해소 및 통과 (총 지연: {wait_time:.1f}s)")
        else:
            print(f"[{get_now()}] 🟢 [통과 보고] {loc_str} | 바스켓 #{basket_id} 정상 통과 ({wait_time:.1f}s)")
        
    except Exception as e:
        print(f"[{get_now()}] ❌ [전송 오류] 바스켓 #{basket_id} @ {loc_str}: {e}")

def init_iothub_client(center_id):
    connection_string_key = f"IOT_HUB_DEVICE_CONNECTION_STRING{center_id}"
    connection_string = os.getenv(connection_string_key)
    if not connection_string:
        connection_string = os.getenv("IOT_HUB_DEVICE_CONNECTION_STRING")
        if not connection_string:
            print(
                "❌ [초기화 실패] IoT Hub 연결 문자열을 확인하세요: "
                f"{connection_string_key} 또는 IOT_HUB_DEVICE_CONNECTION_STRING"
            )
            exit()
    try:
        client = IoTHubDeviceClient.create_from_connection_string(connection_string)
        client.connect()
        return client
    except Exception as e:
        print(f"❌ [초기화 실패] IoT Hub 연결 문자열을 확인하세요: {e}")
        exit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Logistics center data generator")
    parser.add_argument("--center-id", type=int, required=True, help="Fix all events to a center_id")
    args = parser.parse_args()
    device_client = init_iothub_client(args.center_id)

    print("="*60)
    print("🚀 물류센터 실시간 멀티 라인 시뮬레이터 가동")
    print("="*60)

    runtime_config = load_runtime_config()
    if runtime_config:
        print("✅ 설정 DB 연동 활성화")
    else:
        print("⚠️  설정 DB 연동 실패: 기본 범위 사용")
    
    try:
        while True:
            # 새로운 바스켓 투입 (멀티스레딩)
            target_basket = random.randint(10000, 99999)
            basket_thread = threading.Thread(
                target=simulate_single_basket,
                args=(target_basket, runtime_config, args.center_id)
            )
            basket_thread.daemon = True 
            basket_thread.start()
            
            # 투입 간격 (0.5~2초마다 한 대씩)
            time.sleep(random.uniform(0.5, 2.0))
            
    except KeyboardInterrupt:
        print("\n🛑 시뮬레이션이 중단되었습니다.")
    finally:
        device_client.disconnect()