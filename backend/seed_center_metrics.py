import os
import random
from datetime import datetime, timedelta

import psycopg2
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

DB_URL = os.getenv("AZ_POSTGRE_DATABASE_URL")

CAUSE_CODES = ["JAM", "SENSOR", "OVERLOAD", "MAINT", "BLOCKED"]
STATUSES = ["NORMAL", "ALERT", "DELAY", "STOP"]


def _fetch_all(cur, query, params=None):
    cur.execute(query, params or ())
    return cur.fetchall()


def _has_recent_rows(cur, table, line_id, hours=24):
    cur.execute(
        f"SELECT COUNT(*) FROM {table} WHERE line_id = %s AND occurred_at >= %s",
        (line_id, datetime.utcnow() - timedelta(hours=hours))
    )
    return cur.fetchone()[0] > 0


def _has_recent_kpi(cur, line_id, hours=24):
    cur.execute(
        """
        SELECT COUNT(*)
        FROM kpi_report
        WHERE line_id = %s AND window_end >= %s
        """,
        (line_id, datetime.utcnow() - timedelta(hours=hours))
    )
    return cur.fetchone()[0] > 0


def seed_center_metrics() -> None:
    if not DB_URL:
        raise RuntimeError("AZ_POSTGRE_DATABASE_URL is not set")

    conn = psycopg2.connect(DB_URL)
    random.seed(42)
    inserted_kpi = 0
    inserted_bottlenecks = 0
    updated_status = 0

    try:
        with conn.cursor() as cur:
            centers = _fetch_all(cur, "SELECT center_id FROM center ORDER BY center_id")
            if not centers:
                print("No centers found. Seed centers first.")
                return

            for (center_id,) in centers:
                zones = _fetch_all(
                    cur,
                    "SELECT zone_id FROM zone WHERE center_id = %s ORDER BY zone_id",
                    (center_id,)
                )
                zone_id = zones[0][0] if zones else None

                lines = _fetch_all(
                    cur,
                    "SELECT line_id FROM line WHERE center_id = %s ORDER BY line_id",
                    (center_id,)
                )
                if not lines:
                    continue

                for (line_id,) in lines:
                    cur.execute(
                        """
                        INSERT INTO line_status (line_id, current_status, active_bottlenecks, last_updated_at)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (line_id)
                        DO UPDATE SET
                            current_status = EXCLUDED.current_status,
                            active_bottlenecks = EXCLUDED.active_bottlenecks,
                            last_updated_at = EXCLUDED.last_updated_at
                        """,
                        (
                            line_id,
                            random.choice(STATUSES),
                            random.randint(0, 3),
                            datetime.utcnow()
                        )
                    )
                    updated_status += 1

                    if not _has_recent_kpi(cur, line_id):
                        for hour_offset in range(12):
                            window_end = datetime.utcnow() - timedelta(hours=hour_offset)
                            cur.execute(
                                """
                                INSERT INTO kpi_report
                                    (window_end, center_id, zone_id, line_id, throughput_count, created_at)
                                VALUES (%s, %s, %s, %s, %s, %s)
                                """,
                                (
                                    window_end,
                                    center_id,
                                    zone_id,
                                    line_id,
                                    random.randint(80, 420),
                                    datetime.utcnow()
                                )
                            )
                            inserted_kpi += 1

                    if not _has_recent_rows(cur, "bottleneck_event", line_id):
                        for _ in range(4):
                            occurred_at = datetime.utcnow() - timedelta(
                                minutes=random.randint(10, 24 * 60)
                            )
                            cur.execute(
                                """
                                INSERT INTO bottleneck_event
                                    (occurred_at, center_id, zone_id, line_id, duration_sec, cause_code, status)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                                """,
                                (
                                    occurred_at,
                                    center_id,
                                    zone_id,
                                    line_id,
                                    random.randint(30, 600),
                                    random.choice(CAUSE_CODES),
                                    random.choice(["OPEN", "RESOLVED"])
                                )
                            )
                            inserted_bottlenecks += 1

        conn.commit()
        print(
            "Seeded center metrics: "
            f"kpi={inserted_kpi}, bottlenecks={inserted_bottlenecks}, "
            f"line_status={updated_status}"
        )
    finally:
        conn.close()


if __name__ == "__main__":
    seed_center_metrics()
