import os
from datetime import date

import psycopg2
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

DB_URL = os.getenv("AZ_POSTGRE_DATABASE_URL")

CENTER_SEEDS = [
    {
        "name": "Seoul Hub",
        "location": "Seoul",
        "status": "ACTIVE",
        "opened_at": date(2023, 3, 1),
        "zones": [
            {"name": "Inbound", "type": "RECEIVE", "status": "ACTIVE"},
            {"name": "Outbound", "type": "SHIP", "status": "ACTIVE"}
        ],
        "lines": [
            {"name": "Line A", "type": "MAIN", "status": "ACTIVE", "rail_length_m": 120.0, "section_count": 6},
            {"name": "Line B", "type": "SUB", "status": "ACTIVE", "rail_length_m": 90.0, "section_count": 5}
        ]
    },
    {
        "name": "Busan Terminal",
        "location": "Busan",
        "status": "ACTIVE",
        "opened_at": date(2021, 7, 20),
        "zones": [
            {"name": "Dock", "type": "RECEIVE", "status": "ACTIVE"},
            {"name": "Sort", "type": "SORT", "status": "ACTIVE"}
        ],
        "lines": [
            {"name": "Line C", "type": "MAIN", "status": "ACTIVE", "rail_length_m": 140.0, "section_count": 7},
            {"name": "Line D", "type": "SUB", "status": "ACTIVE", "rail_length_m": 80.0, "section_count": 4}
        ]
    }
]


def get_or_create_center(cur, center):
    cur.execute("SELECT center_id FROM center WHERE name = %s", (center["name"],))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        """
        INSERT INTO center (name, location, status, opened_at)
        VALUES (%s, %s, %s, %s)
        RETURNING center_id
        """,
        (center["name"], center["location"], center["status"], center["opened_at"])
    )
    return cur.fetchone()[0]


def get_or_create_zone(cur, center_id, zone):
    cur.execute(
        "SELECT zone_id FROM zone WHERE center_id = %s AND name = %s",
        (center_id, zone["name"])
    )
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        """
        INSERT INTO zone (center_id, name, type, status)
        VALUES (%s, %s, %s, %s)
        RETURNING zone_id
        """,
        (center_id, zone["name"], zone["type"], zone["status"])
    )
    return cur.fetchone()[0]


def get_or_create_line(cur, center_id, line):
    cur.execute(
        "SELECT line_id FROM line WHERE center_id = %s AND name = %s",
        (center_id, line["name"])
    )
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        """
        INSERT INTO line (center_id, name, type, status, rail_length_m, section_count)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING line_id
        """,
        (
            center_id,
            line["name"],
            line["type"],
            line["status"],
            line["rail_length_m"],
            line["section_count"]
        )
    )
    return cur.fetchone()[0]


def get_or_create_section(cur, line_id, section):
    cur.execute(
        "SELECT section_id FROM section WHERE line_id = %s AND order_in_line = %s",
        (line_id, section["order_in_line"])
    )
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        """
        INSERT INTO section (line_id, name, order_in_line, type)
        VALUES (%s, %s, %s, %s)
        RETURNING section_id
        """,
        (line_id, section["name"], section["order_in_line"], section["type"])
    )
    return cur.fetchone()[0]


def get_or_create_sensor(cur, section_id, sensor):
    cur.execute(
        "SELECT sensor_id FROM sensor WHERE section_id = %s AND name = %s",
        (section_id, sensor["name"])
    )
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        """
        INSERT INTO sensor (section_id, equipment_id, sensor_type, name, status)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING sensor_id
        """,
        (
            section_id,
            sensor.get("equipment_id"),
            sensor["sensor_type"],
            sensor["name"],
            sensor["status"]
        )
    )
    return cur.fetchone()[0]


def seed_master() -> None:
    if not DB_URL:
        raise RuntimeError("AZ_POSTGRE_DATABASE_URL is not set")

    conn = psycopg2.connect(DB_URL)
    try:
        with conn.cursor() as cur:
            for center in CENTER_SEEDS:
                center_id = get_or_create_center(cur, center)

                for zone in center["zones"]:
                    get_or_create_zone(cur, center_id, zone)

                for line in center["lines"]:
                    line_id = get_or_create_line(cur, center_id, line)
                    for order in range(1, line["section_count"] + 1):
                        section = {
                            "name": f"Section {order}",
                            "order_in_line": order,
                            "type": "NORMAL"
                        }
                        section_id = get_or_create_section(cur, line_id, section)
                        for sensor_index in range(1, 3):
                            sensor = {
                                "name": f"Sensor {order}-{sensor_index}",
                                "sensor_type": "POSITION",
                                "status": "ACTIVE"
                            }
                            get_or_create_sensor(cur, section_id, sensor)

        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    seed_master()
    print("Seeded centers, zones, lines, sections, and sensors.")
