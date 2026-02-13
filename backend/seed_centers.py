import os
from datetime import date

import psycopg2
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

DB_URL = os.getenv("AZ_POSTGRE_DATABASE_URL")

SEED_CENTERS = [
    {"name": "Seoul Hub", "location": "Seoul", "status": "ACTIVE", "opened_at": date(2023, 3, 1)},
    {"name": "Incheon Port", "location": "Incheon", "status": "ACTIVE", "opened_at": date(2022, 11, 15)},
    {"name": "Busan Terminal", "location": "Busan", "status": "ACTIVE", "opened_at": date(2021, 7, 20)},
    {"name": "Daejeon Sort", "location": "Daejeon", "status": "ACTIVE", "opened_at": date(2024, 1, 10)},
]


def seed_centers() -> None:
    if not DB_URL:
        raise RuntimeError("AZ_POSTGRE_DATABASE_URL is not set")

    conn = psycopg2.connect(DB_URL)
    try:
        with conn.cursor() as cur:
            for center in SEED_CENTERS:
                cur.execute(
                    "SELECT center_id FROM center WHERE name = %s",
                    (center["name"],)
                )
                exists = cur.fetchone()
                if exists:
                    continue
                cur.execute(
                    """
                    INSERT INTO center (name, location, status, opened_at)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (center["name"], center["location"], center["status"], center["opened_at"])
                )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    seed_centers()
    print("Seeded centers (skipped existing names).")
