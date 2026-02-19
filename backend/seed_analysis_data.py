import os
from datetime import datetime

import psycopg2
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

# 중앙 집계용(대상) 데이터베이스
DEST_DB_URL = os.getenv("AZ_POSTGRE_DATABASE_URL")

# 개별 센터(소스) 데이터베이스 목록
SOURCE_DB_URLS = []
i = 0
while True:
    url = os.getenv(f"AZ_POSTGRE_DATABASE_URL_{i}")
    if url is None:
        break
    SOURCE_DB_URLS.append(url)
    i += 1

# 소스 DB가 하나도 없으면, 중앙 DB를 소스로 간주 (기존 로직 호환성)
if not SOURCE_DB_URLS and DEST_DB_URL:
    SOURCE_DB_URLS.append(DEST_DB_URL)

LOSS_RATE = 0.15
LOSS_UNIT_AMOUNT = 1200


def _fetch_all(cur, query, params=None):
    cur.execute(query, params or ())
    return cur.fetchall()


def _table_has_rows(cur, table):
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    return cur.fetchone()[0] > 0


def seed_analysis_data() -> None:
    if not DB_URL:
        raise RuntimeError("AZ_POSTGRE_DATABASE_URL is not set")

    conn = psycopg2.connect(DB_URL)
    try:
        with conn.cursor() as cur:
            if not _table_has_rows(cur, "aggregation_summary"):
                for granularity in ("hour", "day"):
                    cur.execute(
                        """
                        SELECT date_trunc(%s, window_end) AS bucket_start,
                               center_id,
                               line_id,
                               SUM(throughput_count) AS throughput_total
                        FROM kpi_report
                        GROUP BY bucket_start, center_id, line_id
                        ORDER BY bucket_start
                        """,
                        (granularity,)
                    )
                    kpi_rows = cur.fetchall()

                    cur.execute(
                        """
                        SELECT date_trunc(%s, occurred_at) AS bucket_start,
                               center_id,
                               line_id,
                               COUNT(*) AS bottleneck_count,
                               AVG(duration_sec) AS avg_duration
                        FROM bottleneck_event
                        GROUP BY bucket_start, center_id, line_id
                        """,
                        (granularity,)
                    )
                    bn_rows = cur.fetchall()

                    bottleneck_map = {}
                    for bucket_start, center_id, line_id, count, avg_duration in bn_rows:
                        bottleneck_map[(bucket_start, center_id, line_id)] = (count, avg_duration)

                    for bucket_start, center_id, line_id, throughput_total in kpi_rows:
                        count, avg_duration = bottleneck_map.get(
                            (bucket_start, center_id, line_id),
                            (0, 0.0)
                        )
                        cur.execute(
                            """
                            INSERT INTO aggregation_summary
                                (granularity, bucket_start, center_id, line_id,
                                 throughput_total, bottleneck_count, avg_bottleneck_duration_sec, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                granularity,
                                bucket_start,
                                center_id,
                                line_id,
                                throughput_total,
                                count,
                                avg_duration,
                                datetime.utcnow()
                            )
                        )

            if not _table_has_rows(cur, "loss_analysis"):
                cur.execute(
                    """
                    SELECT date_trunc('hour', occurred_at) AS bucket_start,
                           center_id,
                           line_id,
                           COUNT(*) AS bottleneck_count,
                           SUM(duration_sec) AS total_bottleneck_sec
                    FROM bottleneck_event
                    GROUP BY bucket_start, center_id, line_id
                    """
                )
                bn_rows = cur.fetchall()

                cur.execute(
                    """
                    SELECT date_trunc('hour', window_end) AS bucket_start,
                           center_id,
                           line_id,
                           SUM(throughput_count) AS throughput_total
                    FROM kpi_report
                    GROUP BY bucket_start, center_id, line_id
                    """
                )
                kpi_rows = cur.fetchall()

                kpi_map = {}
                for bucket_start, center_id, line_id, throughput_total in kpi_rows:
                    kpi_map[(bucket_start, center_id, line_id)] = throughput_total

                for bucket_start, center_id, line_id, count, total_sec in bn_rows:
                    throughput_total = kpi_map.get((bucket_start, center_id, line_id), 0)
                    throughput_value = float(throughput_total or 0)
                    total_sec_value = float(total_sec or 0)
                    loss_ratio = min(total_sec_value / 3600.0, 1.0) * LOSS_RATE
                    throughput_loss = int(round(throughput_value * loss_ratio))
                    loss_amount = throughput_loss * LOSS_UNIT_AMOUNT
                    cur.execute(
                        """
                        INSERT INTO loss_analysis
                            (center_id, line_id, window_start, window_end,
                             bottleneck_count, total_bottleneck_sec,
                             throughput_loss_est, loss_amount, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            center_id,
                            line_id,
                            bucket_start,
                            bucket_start,
                            count,
                            total_sec,
                            throughput_loss,
                            loss_amount,
                            datetime.utcnow()
                        )
                    )

        conn.commit()
        print("Seeded aggregation_summary and loss_analysis (skipped non-empty tables).")
    finally:
        conn.close()


if __name__ == "__main__":
    seed_analysis_data()
