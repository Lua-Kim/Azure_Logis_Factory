-- =============================================================
-- Bottleneck Event의 Cause Code 데이터 추가
-- =============================================================

-- Bottleneck ID 40: JAM (적체)
UPDATE bottleneck_event 
SET 
    cause_code = 'JAM',
    detail_reason = '컨베이어 적체로 인한 병목'
WHERE bottleneck_id = 40;

-- Bottleneck ID 29: SENSOR (센서 오류)
UPDATE bottleneck_event 
SET 
    cause_code = 'SENSOR',
    detail_reason = '센서 감지 오류로 인한 지연'
WHERE bottleneck_id = 29;

-- Bottleneck ID 19: OVERLOAD (과부하)
UPDATE bottleneck_event 
SET 
    cause_code = 'OVERLOAD',
    detail_reason = '시스템 과부하로 인한 처리 지연'
WHERE bottleneck_id = 19;

-- 확인 쿼리
SELECT bottleneck_id, line_id, cause_code, detail_reason, occurred_at
FROM bottleneck_event
ORDER BY bottleneck_id;
