import os
import random
import time
import json
import uuid
import threading
from datetime import datetime, timezone
from dotenv import load_dotenv
from azure.iot.device import IoTHubDeviceClient

# .env 파일 로드
env_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(env_path)

IOT_HUB_DEVICE_CONNECTION_STRING = os.getenv('IOT_HUB_DEVICE_CONNECTION_STRING')

# IoT Hub 클라이언트 초기화 (전역 세션 유지)
try:
    device_client = IoTHubDeviceClient.create_from_connection_string(IOT_HUB_DEVICE_CONNECTION_STRING)
    device_client.connect()
except Exception as e:
    print(f"❌ [초기화 실패] IoT Hub 연결 문자열을 확인하세요: {e}")
    exit()

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
        'sensor_id': random.randint(1, 5),
        'basket_id': basket_id,
        'numeric_value': round(random.uniform(20.0, 25.0), 2),
        'status': 'RUNNING',
        'error_code': 'NONE',
        'attributes_json': {"version": "1.4", "mode": "mass_parallel"}
    }

def simulate_single_basket(basket_id):
    """
    한 개의 바스켓이 특정 경로를 통과하는 독립적인 흐름 시뮬레이션
    """
    # 전제 조건: 다양한 구역(Zone)과 라인(Line) 시뮬레이션
    center_id = 1 
    zone_id = random.randint(1, 3)    
    line_id = random.randint(1, 5)    
    section_id = random.randint(1, 10) 
    
    loc_str = f"C{center_id}-Z{zone_id}-L{line_id}-S{section_id}"

    try:
        # 1. ARRIVAL 전송 (진입)
        arrival = create_event(basket_id, 'ARRIVAL', center_id, zone_id, line_id, section_id)
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
        device_client.send_message(json.dumps(departure))
        
        if is_bottleneck:
            print(f"[{get_now()}] ✨ [운행 재개] {loc_str} | 바스켓 #{basket_id} 병목 해소 및 통과 (총 지연: {wait_time:.1f}s)")
        else:
            print(f"[{get_now()}] 🟢 [통과 보고] {loc_str} | 바스켓 #{basket_id} 정상 통과 ({wait_time:.1f}s)")
        
    except Exception as e:
        print(f"[{get_now()}] ❌ [전송 오류] 바스켓 #{basket_id} @ {loc_str}: {e}")

if __name__ == "__main__":
    print("="*60)
    print("🚀 물류센터 실시간 멀티 라인 시뮬레이터 가동")
    print("="*60)
    
    try:
        while True:
            # 새로운 바스켓 투입 (멀티스레딩)
            target_basket = random.randint(10000, 99999)
            basket_thread = threading.Thread(target=simulate_single_basket, args=(target_basket,))
            basket_thread.daemon = True 
            basket_thread.start()
            
            # 투입 간격 (0.5~2초마다 한 대씩)
            time.sleep(random.uniform(0.5, 2.0))
            
    except KeyboardInterrupt:
        print("\n🛑 시뮬레이션이 중단되었습니다.")
    finally:
        device_client.disconnect()