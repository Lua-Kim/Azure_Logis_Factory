물류 시스템 데이터 저장 예시
이 문서는 현재 설계된 데이터베이스 구조(create_tables.py)와 시뮬레이터(data_generator.py)가 작동했을 때, 실제 테이블에 데이터가 어떻게 저장되는지 시나리오별 예시를 보여줍니다.
1. 마스터 데이터 (구조 정의)
시스템 가동 전, 물류센터의 물리적 구조를 먼저 등록합니다.
[center] 테이블
center_id
name
location
status
1
서울 제1 물류센터
서울시 송파구
ACTIVE

[zone] 테이블 (센터 내 구역)
zone_id
center_id
name
type
10
1
피킹 존 A
PICKING

[line] 테이블 (구역 내 라인)
line_id
zone_id
name
type
101
10
메인 컨베이어 1호기
MAIN_RAIL

[section] 테이블 (라인 내 세부 구간)
section_id
line_id
name
order_in_line
1001
101
입구 진입 구간
1
1002
101
검수 대기 구간
2

[sensor] 테이블 (구간별 설치된 센서)
sensor_id
section_id
name
sensor_type
5001
1001
진입 감지 센서 01
ARRIVAL_SENSOR
5002
1002
검수 위치 센서 01
PROXIMITY_SENSOR

2. 이벤트 데이터 (실시간 로그)
바스켓(ID: 5501)이 이동하면서 생성하는 데이터입니다.
[sensor_event] 테이블
바스켓이 구간을 통과할 때마다 행(Row)이 추가됩니다.
event_id
event_type_code
occurred_at
basket_id
sensor_id
section_id
status
UUID-1
ARRIVAL
2024-05-20 10:00:01
5501
5001
1001
RUNNING
UUID-2
DEPARTURE
2024-05-20 10:00:03
5501
5001
1001
RUNNING
UUID-3
ARRIVAL
2024-05-20 10:00:05
5501
5002
1002
RUNNING

3. 병목 데이터 (분석 결과)
ASA(Stream Analytics)가 위 이벤트를 분석하여 자동으로 생성하는 요약 정보입니다.
[bottleneck_event] 테이블
만약 바스켓 5501이 1001 구간에 ARRIVAL은 찍혔는데, 30초 동안 DEPARTURE가 발생하지 않는다면?
bottleneck_id
root_event_id
occurred_at
section_id
duration_sec
cause_code
77
UUID-1
2024-05-20 10:00:31
1001
30
TRAFFIC_JAM

4. 데이터 저장 흐름 (Summary)
정적 정보: center → zone → line → section → sensor 순으로 미리 입력되어 있음.
동적 정보: 바스켓이 움직일 때마다 sensor_event에 기록됨.
분석 정보: sensor_event를 토대로 ASA가 계산하여 bottleneck_event를 생성함.
