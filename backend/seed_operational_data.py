import os
import random
from datetime import datetime, timedelta, date

import psycopg2
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

DB_URL = os.getenv("AZ_POSTGRE_DATABASE_URL")

COST_CATEGORIES = ["LABOR", "ENERGY", "MAINTENANCE", "MATERIAL"]
WEATHER_NOTES = ["CLEAR", "RAIN", "WIND", "SNOW"]


def _fetch_all(cur, query, params=None):
    cur.execute(query, params or ())
    return cur.fetchall()


def _table_has_rows(cur, table):
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    return cur.fetchone()[0] > 0


def seed_operational_data() -> None:
    if not DB_URL:
        raise RuntimeError("AZ_POSTGRE_DATABASE_URL is not set")

    random.seed(7)
    conn = psycopg2.connect(DB_URL)
    try:
        with conn.cursor() as cur:
            centers = _fetch_all(cur, "SELECT center_id FROM center ORDER BY center_id")
            if not centers:
                print("No centers found. Seed centers first.")
                return

            if not _table_has_rows(cur, "equipment"):
                for (center_id,) in centers:
                    lines = _fetch_all(
                        cur,
                        "SELECT line_id FROM line WHERE center_id = %s ORDER BY line_id",
                        (center_id,)
                    )
                    for idx, (line_id,) in enumerate(lines, start=1):
                        cur.execute(
                            """
                            INSERT INTO equipment
                                (center_id, line_id, name, type, status, install_date, last_maintenance, manufacturer, model)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                center_id,
                                line_id,
                                f"Conveyor Motor {center_id}-{idx}",
                                "MOTOR",
                                "ACTIVE",
                                date(2022, 6, 1),
                                date.today() - timedelta(days=random.randint(5, 60)),
                                "LogisTech",
                                "LT-MTR-300"
                            )
                        )

            if not _table_has_rows(cur, "worker"):
                for (center_id,) in centers:
                    for idx in range(3):
                        cur.execute(
                            """
                            INSERT INTO worker (name, role, center_id, status)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (
                                f"Worker {center_id}-{idx + 1}",
                                random.choice(["OPERATOR", "SUPERVISOR"]),
                                center_id,
                                "ACTIVE"
                            )
                        )

            if not _table_has_rows(cur, "threshold_config"):
                thresholds = [
                    ("bottleneck_duration_sec", "30", "Bottleneck threshold (sec)"),
                    ("throughput_target_per_hour", "250", "Target throughput per hour"),
                    ("max_error_rate", "2", "Max error rate (%)"),
                ]
                for key, value, desc in thresholds:
                    cur.execute(
                        """
                        INSERT INTO threshold_config (config_key, config_value, description)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (config_key) DO NOTHING
                        """,
                        (key, value, desc)
                    )

            if not _table_has_rows(cur, "maintenance_event"):
                equipments = _fetch_all(cur, "SELECT equipment_id FROM equipment")
                for (equipment_id,) in equipments:
                    start_at = datetime.utcnow() - timedelta(days=random.randint(1, 20))
                    end_at = start_at + timedelta(hours=random.randint(1, 4))
                    cur.execute(
                        """
                        INSERT INTO maintenance_event
                            (equipment_id, start_at, end_at, type, result, downtime_sec, notes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            equipment_id,
                            start_at,
                            end_at,
                            random.choice(["PREVENTIVE", "BREAKDOWN"]),
                            random.choice(["OK", "REPAIR"]),
                            int((end_at - start_at).total_seconds()),
                            "Auto-seeded"
                        )
                    )

            if not _table_has_rows(cur, "operation_cost"):
                for (center_id,) in centers:
                    for month_offset in range(3):
                        cost_date = date.today().replace(day=1) - timedelta(days=30 * month_offset)
                        for category in COST_CATEGORIES:
                            cur.execute(
                                """
                                INSERT INTO operation_cost
                                    (center_id, date, category, amount, notes)
                                VALUES (%s, %s, %s, %s, %s)
                                """,
                                (
                                    center_id,
                                    cost_date,
                                    category,
                                    random.randint(4000, 20000),
                                    "Auto-seeded"
                                )
                            )

            if not _table_has_rows(cur, "order_event"):
                for (center_id,) in centers:
                    for _ in range(10):
                        order_date = datetime.utcnow() - timedelta(hours=random.randint(1, 120))
                        cur.execute(
                            """
                            INSERT INTO order_event
                                (customer_id, product_id, center_id, order_date, status, sla)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            """,
                            (
                                random.randint(1000, 2000),
                                random.randint(2000, 3000),
                                center_id,
                                order_date,
                                random.choice(["RECEIVED", "PICKING", "SHIPPED", "DONE"]),
                                random.uniform(2.0, 24.0)
                            )
                        )

            if not _table_has_rows(cur, "quality_event"):
                recent_events = _fetch_all(
                    cur,
                    "SELECT event_id, center_id, line_id, section_id FROM sensor_event ORDER BY occurred_at DESC LIMIT 100"
                )
                for event_id, center_id, line_id, section_id in recent_events[:20]:
                    cur.execute(
                        """
                        INSERT INTO quality_event
                            (event_id, center_id, line_id, section_id, product_id, defect_type, quantity, detected_at, notes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            event_id,
                            center_id,
                            line_id,
                            section_id,
                            random.randint(3000, 4000),
                            random.choice(["SCRATCH", "MISALIGN", "MISSING"]),
                            random.randint(1, 6),
                            datetime.utcnow(),
                            "Auto-seeded"
                        )
                    )

            if not _table_has_rows(cur, "weather"):
                for (center_id,) in centers:
                    for day_offset in range(5):
                        cur.execute(
                            """
                            INSERT INTO weather
                                (date, location, center_id, temp, rain, wind, notes)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                date.today() - timedelta(days=day_offset),
                                f"Center {center_id}",
                                center_id,
                                round(random.uniform(-2.0, 28.0), 1),
                                round(random.uniform(0.0, 20.0), 1),
                                round(random.uniform(0.0, 12.0), 1),
                                random.choice(WEATHER_NOTES)
                            )
                        )

            if not _table_has_rows(cur, "simulation_result"):
                cur.execute(
                    """
                    INSERT INTO simulation_result
                        (scenario, executed_at, input_params_json, result_json, notes)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        "baseline",
                        datetime.utcnow(),
                        '{"mode": "seed"}',
                        '{"throughput_gain": 3.2, "bottleneck_drop": 1.1}',
                        "Auto-seeded"
                    )
                )

            if not _table_has_rows(cur, "bottleneck_event_sensor"):
                cur.execute(
                    """
                    INSERT INTO bottleneck_event_sensor (bottleneck_id, event_id)
                    SELECT b.bottleneck_id, s.event_id
                    FROM bottleneck_event b
                    JOIN sensor_event s
                      ON s.line_id = b.line_id
                     AND s.section_id = b.section_id
                     AND s.occurred_at BETWEEN b.occurred_at - INTERVAL '30 seconds'
                                         AND b.occurred_at + INTERVAL '30 seconds'
                    ON CONFLICT DO NOTHING
                    """
                )

        conn.commit()
        print("Seeded operational tables (skipped non-empty tables).")
    finally:
        conn.close()


if __name__ == "__main__":
    seed_operational_data()
