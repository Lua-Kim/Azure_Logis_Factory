Azure Stream Analytics 실시간 쿼리 설계이 문서는 IoT Hub에서 수집된 데이터를 분석하여 PostgreSQL DB의 각 테이블(sensor_event, bottleneck_event)로 라우팅하고 실시간 KPI를 산출하는 ASA SQL 쿼리 예시를 포함합니다.

1. 기본 원천 데이터 저장 (Passthrough)
모든 센서 이벤트를 가공 없이 sensor_event 테이블에 저장합니다.

-- [Output: PostgreSQL SensorEventTable]
SELECT
    event_id,
    event_type_code,
    CAST(occurred_at AS datetime) AS occurred_at,
    center_id,
    zone_id,
    line_id,
    section_id,
    sensor_id,
    basket_id,
    numeric_value,
    string_value,
    status,
    error_code,
    attributes_json
INTO
    [PostgresSensorEventOutput]
FROM
    [IoTHubInput]



2. 실시간 처리량(Throughput) KPI 산출최근 1분간 각 라인별로 통과한 바스켓의 수를 실시간으로 집계합니다. 이 데이터는 대시보드의 실시간 그래프에 활용됩니다.

-- [Output: PostgreSQL SummaryOutput]
SELECT
    System.Timestamp AS window_end,
    center_id,
    line_id,
    COUNT(basket_id) AS throughput_count
INTO
    [RealtimeKPIOutput]
FROM
    [IoTHubInput] TIMESTAMP BY occurred_at
WHERE
    event_type_code = 'DEPARTURE' -- 출발(완료) 이벤트 기준
GROUP BY
    center_id,
    line_id,
    TumblingWindow(minute, 1)


3. 실시간 병목(Bottleneck) 감지 로직특정 섹션에 바스켓이 '도착'한 후, 설정된 시간(예: 30초) 내에 '출발' 이벤트가 발생하지 않는 경우를 실시간으로 포착합니다.
-- [Output: PostgreSQL BottleneckEventTable]
-- Self-Join을 활용하여 도착은 했으나 출발 신호가 없는 객체 식별
SELECT
    A.center_id,
    A.line_id,
    A.section_id,
    A.basket_id,
    A.occurred_at AS start_time,
    'DELAY_ERROR' AS cause_code,
    '병목 감지: 30초 이상 정체' AS detail_reason
INTO
    [BottleneckOutput]
FROM
    [IoTHubInput] A TIMESTAMP BY occurred_at
LEFT OUTER JOIN
    [IoTHubInput] B TIMESTAMP BY occurred_at
ON
    A.basket_id = B.basket_id
    AND A.section_id = B.section_id
    AND DATEDIFF(second, A, B) BETWEEN 1 AND 30
    AND B.event_type_code = 'DEPARTURE'
WHERE
    A.event_type_code = 'ARRIVAL'
    AND B.basket_id IS NULL -- 30초 이내에 출발(B)이 없는 경우만 추출



4. 이상 징후 알림 (Alerting)장비 상태가 'ERROR'이거나 numeric_value(예: 온도)가 임계치를 초과하는 경우 즉시 알림 서비스로 데이터를 보냅니다.-- [Output: Azure Functions / Service Bus]
SELECT
    occurred_at,
    center_id,
    equipment_id,
    error_code,
    error_message
INTO
    [CriticalAlertOutput]
FROM
    [IoTHubInput]
WHERE
    status = 'ERROR' 
    OR numeric_value > 80 -- 예: 장비 온도 80도 초과 시
