Azure Stream Analytics 실시간 쿼리 설계이 문서는 IoT Hub에서 수집된 데이터를 분석하여 PostgreSQL DB의 각 테이블(sensor_event, bottleneck_event)로 라우팅하고 실시간 KPI를 산출하는 ASA SQL 쿼리 예시를 포함합니다.


<최종 쿼리문>
WITH RawData AS (
    SELECT *
    FROM [aziothub01] TIMESTAMP BY occurred_at
)

-- 1. 센서 이벤트 적재 (1초 단위 중복 제거 및 타입 변환)
SELECT
    event_type_code,
    System.Timestamp AS occurred_at, -- DB Default 에러 방지
    CAST(center_id AS bigint) AS center_id,
    CAST(zone_id AS bigint) AS zone_id,
    CAST(line_id AS bigint) AS line_id,
    CAST(section_id AS bigint) AS section_id,
    CAST(sensor_id AS bigint) AS sensor_id,
    CAST(basket_id AS bigint) AS basket_id,
    MAX(numeric_value) AS numeric_value,
    status,
    error_code
INTO
    [out-psql-sensor-event]
FROM
    RawData
GROUP BY
    event_type_code,
    center_id,
    zone_id,
    line_id,
    section_id,
    sensor_id,
    basket_id,
    status,
    error_code,
    TumblingWindow(second, 1);

-- 2. 실시간 병목 감지 (조인 후 타입 변환 및 시간 주입)
SELECT 
    System.Timestamp AS occurred_at,
    CAST(A.center_id AS bigint) AS center_id,
    CAST(A.zone_id AS bigint) AS zone_id,
    CAST(A.line_id AS bigint) AS line_id,
    CAST(A.section_id AS bigint) AS section_id,
    CAST(A.sensor_id AS bigint) AS sensor_id,
    CAST(30 AS bigint) AS duration_sec,
    'TRAFFIC_JAM' AS cause_code,
    'ACTIVE' AS status,
    CAST(A.basket_id AS bigint) AS affected_basket
INTO [out-psql-bottleneck-event]
FROM RawData A
LEFT OUTER JOIN RawData B
ON 
    A.basket_id = B.basket_id 
    AND A.section_id = B.section_id
    AND B.event_type_code = 'DEPARTURE'
    AND DATEDIFF(second, A, B) BETWEEN 1 AND 30
WHERE 
    A.event_type_code = 'ARRIVAL'
    AND B.basket_id IS NULL
GROUP BY 
    A.center_id, A.zone_id, A.line_id, A.section_id, A.sensor_id, A.basket_id, 
    TumblingWindow(second, 5);

-- 3. KPI 리포트 (처리량 타입 변환 및 생성 시간 명시)
SELECT
    System.Timestamp AS window_end,
    CAST(center_id AS bigint) AS center_id,
    CAST(zone_id AS bigint) AS zone_id,
    CAST(line_id AS bigint) AS line_id,
    CAST(COUNT(DISTINCT basket_id) AS bigint) AS throughput_count,
    System.Timestamp AS created_at
INTO [out-psql-throughput-kpi]
FROM RawData
WHERE event_type_code = 'DEPARTURE'
GROUP BY center_id, zone_id, line_id, TumblingWindow(minute, 1);

-- 4. 실시간 라인 상태 업데이트 (문자열 타입 세이프 집계)
SELECT
    CAST(line_id AS bigint) AS line_id,
    CAST(MAX(CASE 
        WHEN event_type_code = 'DEPARTURE' THEN 'NORMAL'
        WHEN event_type_code = 'ERROR' THEN 'ERROR'
        ELSE 'RUNNING' 
    END) AS nvarchar(max)) AS current_status,
    CAST(MAX(basket_id) AS bigint) AS last_basket_id,
    System.Timestamp AS last_updated_at
INTO [out-psql-line-status]
FROM RawData
WHERE event_type_code IN ('DEPARTURE', 'ERROR', 'ARRIVAL')
GROUP BY line_id, TumblingWindow(second, 1);