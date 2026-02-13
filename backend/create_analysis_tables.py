import os
from dotenv import load_dotenv
import psycopg2

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

DB_URL = os.getenv("AZ_POSTGRE_DATABASE_URL")

CREATE_LOSS_ANALYSIS_TABLE = """
CREATE TABLE IF NOT EXISTS loss_analysis (
    loss_id BIGSERIAL PRIMARY KEY,
    center_id BIGINT,
    line_id BIGINT,
    section_id BIGINT,
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    bottleneck_count BIGINT,
    total_bottleneck_sec BIGINT,
    throughput_loss_est BIGINT,
    loss_amount BIGINT,
    created_at TIMESTAMP DEFAULT NOW()
);
"""

CREATE_AGGREGATION_SUMMARY_TABLE = """
CREATE TABLE IF NOT EXISTS aggregation_summary (
    aggregation_id BIGSERIAL PRIMARY KEY,
    granularity VARCHAR(10) NOT NULL,
    bucket_start TIMESTAMP NOT NULL,
    center_id BIGINT,
    line_id BIGINT,
    throughput_total BIGINT,
    bottleneck_count BIGINT,
    avg_bottleneck_duration_sec DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT NOW()
);
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_loss_analysis_bucket ON loss_analysis (window_start, center_id, line_id);",
    "CREATE INDEX IF NOT EXISTS idx_agg_summary_bucket ON aggregation_summary (granularity, bucket_start);",
    "CREATE INDEX IF NOT EXISTS idx_agg_summary_center_line ON aggregation_summary (center_id, line_id);"
]


def create_tables() -> None:
    if not DB_URL:
        raise RuntimeError("AZ_POSTGRE_DATABASE_URL is not set")

    conn = psycopg2.connect(DB_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_LOSS_ANALYSIS_TABLE)
            cur.execute(CREATE_AGGREGATION_SUMMARY_TABLE)
            for index_sql in CREATE_INDEXES:
                cur.execute(index_sql)
        conn.commit()
        print("Created loss_analysis and aggregation_summary tables.")
    finally:
        conn.close()


if __name__ == "__main__":
    create_tables()
