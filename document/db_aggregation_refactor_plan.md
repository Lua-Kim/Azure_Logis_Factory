# 데이터베이스 분산 집계 리팩토링 계획

## 1. 목표

기존 단일 데이터베이스 구조에서 여러 센터(물류센터)별 데이터베이스와 중앙(본사) 데이터베이스 구조로 변경됨에 따라, 백엔드 애플리케이션의 데이터 집계 및 조회 로직을 수정합니다.

-   **분산된 데이터 수집:** 여러 센터 데이터베이스에서 운영 데이터를 병렬적으로 또는 순차적으로 조회합니다.
-   **중앙 데이터 집계:** 수집된 데이터를 가공/집계하여 중앙(본사) 데이터베이스에 저장합니다.
-   **효율적인 데이터 조회:** 최종 사용자는 중앙 데이터베이스에 저장된 집계 데이터를 조회하여 빠른 응답 속도를 경험하게 합니다.

## 2. 데이터베이스 연결 정보

-   **중앙 (본사) 데이터베이스:** `AZ_POSTGRE_DATABASE_URL`
-   **센터 (물류센터) 데이터베이스:** `AZ_POSTGRE_DATABASE_URL_0`, `AZ_POSTGRE_DATABASE_URL_1`, `AZ_POSTGRE_DATABASE_URL_2`, ... (패턴으로 관리)

## 3. 리팩토링 단계

### 1단계: 환경 변수 및 설정 관리 (`backend/app/routers/settings.py`, `backend/app/schemas/settings.py`)

-   **목표:** 여러 개의 데이터베이스 URL을 효과적으로 관리하고 애플리케이션 전체에서 사용할 수 있도록 설정 구조를 변경합니다.
-   **작업:**
    1.  `backend/app/schemas/settings.py`의 `Settings` 스키마에 센터 데이터베이스 URL 목록을 관리할 필드 (`center_database_urls: list[str]`)를 추가합니다.
    2.  `backend/app/routers/settings.py`에서 `AZ_POSTGRE_DATABASE_URL_` 접두사를 가진 모든 환경 변수를 동적으로 읽어와 `center_database_urls` 리스트를 생성하도록 수정합니다.
    3.  기존 `database_url` 필드는 중앙 데이터베이스 용도로 명확히 하고, 이름을 `hq_database_url` 등으로 변경하여 역할을 명확히 합니다.

### 2단계: 데이터베이스 연결 관리자 리팩토링 (`backend/app/db.py`)

-   **목표:** 단일 연결 풀이 아닌, 중앙 데이터베이스와 여러 센터 데이터베이스 각각에 대한 연결 풀을 관리하는 객체를 구현합니다.
-   **작업:**
    1.  `DatabaseManager`와 같은 클래스를 생성합니다.
    2.  초기화 시점에 `settings`를 주입받아, 중앙 DB(`hq_database_url`)와 각 센터 DB(`center_database_urls`)에 대한 `SQLAlchemy` 엔진과 세션 풀을 각각 생성하여 딕셔너리 형태로 관리합니다. (예: `self.engines = {'hq': hq_engine, 'center_0': center_0_engine, ...}`)
    3.  `get_hq_db_session()`: 중앙 데이터베이스 세션을 반환하는 메서드를 제공합니다.
    4.  `get_center_db_session(center_id: int)`: 특정 센터의 데이터베이스 세션을 반환하는 메서드를 제공합니다.
    5.  FastAPI의 `Depends`에서 사용할 수 있도록 `get_db` 함수들을 수정/추가합니다.

### 3단계: 데이터 집계 서비스 로직 구현 (`backend/app/services/aggregation_service.py` - 신규 생성)

-   **목표:** 분산된 센터 데이터베이스에서 데이터를 읽어와 집계하는 핵심 로직을 구현합니다.
-   **작업:**
    1.  `aggregation_service.py` 파일을 생성합니다.
    2.  `aggregate_metrics`와 같은 함수를 정의합니다.
    3.  이 함수는 `db_manager: DatabaseManager`를 인자로 받습니다.
    4.  `db_manager`를 통해 모든 센터의 데이터베이스 연결을 순회하며 필요한 데이터(예: `bottleneck_events`, `throughput`)를 조회합니다.
    5.  조회된 결과를 Python 코드 내에서 메모리상으로 집계합니다. (e.g., Pandas DataFrame 사용 고려)
    6.  집계된 최종 결과를 반환합니다.

### 4단계: 집계 데이터 중앙 데이터베이스 저장 로직 구현 (`backend/app/services/aggregation_service.py`)

-   **목표:** `3단계`에서 집계된 데이터를 중앙 데이터베이스에 저장(Insert/Update)합니다.
-   **작업:**
    1.  `save_aggregated_metrics`와 같은 함수를 정의합니다.
    2.  이 함수는 집계된 데이터와 `db_manager`를 인자로 받습니다.
    3.  `db_manager.get_hq_db_session()`을 통해 중앙 데이터베이스 세션을 얻습니다.
    4.  집계된 데이터를 중앙 데이터베이스의 분석용 테이블 (예: `aggregated_metrics`)에 저장합니다. 데이터가 이미 존재할 경우를 대비하여 `UPSERT` 로직을 구현합니다. (SQLAlchemy의 `on_conflict_do_update` 등 활용)

### 5단계: API 라우터 수정 및 스케줄링 (`backend/app/routers/metrics.py`)

-   **목표:** 기존 데이터 조회 API가 중앙 집계 데이터베이스를 바라보도록 수정하고, 데이터 집계 프로세스를 트리거할 방법을 제공합니다.
-   **작업:**
    1.  대시보드 등에서 사용하는 기존 `metrics` 관련 API 엔드포인트들이 `db_manager.get_hq_db_session()`을 사용하도록 수정하여, 중앙 데이터베이스에서 직접 데이터를 읽어가도록 변경합니다.
    2.  데이터 집계를 수동으로 트리거할 수 있는 API 엔드포인트(예: `POST /metrics/aggregate`)를 신규 생성합니다. 이 엔드포인트는 내부적으로 `aggregation_service`의 함수들을 호출합니다.
    3.  (선택 사항) `fastapi-utils`의 `RepeatedTask` 또는 별도의 스케줄러(APScheduler, Celery 등)를 사용하여 주기적으로(예: 1분마다) 집계 프로세스를 자동 실행하는 로직을 추가합니다. `main.py`의 `on_event("startup")` 핸들러에서 스케줄러를 시작할 수 있습니다.

### 6단계: 테스트

-   **목표:** 변경된 로직이 정상적으로 동작하는지 검증합니다.
-   **작업:**
    1.  각 센터별로 테스트 데이터를 삽입합니다.
    2.  `/metrics/aggregate` API를 호출하여 데이터 집계가 성공하는지 확인합니다.
    3.  중앙 데이터베이스에 집계된 데이터가 정확히 저장되었는지 직접 확인합니다.
    4.  기존 조회 API들이 중앙 데이터베이스의 데이터를 기반으로 올바른 값을 반환하는지 확인합니다.
