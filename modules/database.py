"""SQLite persistence layer for institutes and monthly carbon footprint records.

Enforces relational integrity via foreign keys and ON DELETE CASCADE.
Handles database initialization, institute profile management,
monthly emissions upserts, and reporting queries.
"""

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
import sqlite3
from typing import Any, Generator
import pandas as pd

from modules.calculator import (
    calculate_diesel_emission,
    calculate_electricity_emission,
    calculate_total,
    calculate_transport_emission,
    calculate_water_emission,
)

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "carbon_footprint.db"


@contextmanager
def get_connection(db_path: Path | str | None = None) -> Generator[sqlite3.Connection, None, None]:
    """Provide a transactional database connection with foreign keys enabled."""
    target_path = Path(db_path) if db_path else DEFAULT_DB_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Path | str | None = None) -> None:
    """Initialize SQLite database tables with appropriate schemas and foreign keys."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # Institutes table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS institutes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE COLLATE NOCASE NOT NULL,
                address TEXT,
                academic_year TEXT,
                total_students INTEGER DEFAULT 0,
                total_staff INTEGER DEFAULT 0,
                campus_area_sqft REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # Monthly records table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS monthly_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                institute_id INTEGER NOT NULL,
                month TEXT NOT NULL,
                electricity_kwh REAL DEFAULT 0.0,
                water_kl REAL DEFAULT 0.0,
                diesel_litres REAL DEFAULT 0.0,
                electricity_co2 REAL DEFAULT 0.0,
                diesel_co2 REAL DEFAULT 0.0,
                water_co2 REAL DEFAULT 0.0,
                transport_co2 REAL DEFAULT 0.0,
                total_co2 REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(institute_id, month),
                FOREIGN KEY (institute_id) REFERENCES institutes(id) ON DELETE CASCADE
            );
            """
        )

        # Transport rows breakdown table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS transport_rows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id INTEGER NOT NULL,
                vehicle_type TEXT NOT NULL,
                vehicle_count INTEGER NOT NULL,
                distance_km REAL NOT NULL,
                factor REAL NOT NULL,
                co2_kg REAL NOT NULL,
                FOREIGN KEY (record_id) REFERENCES monthly_records(id) ON DELETE CASCADE
            );
            """
        )


def save_institute(
    name: str,
    address: str,
    academic_year: str,
    total_students: int,
    total_staff: int,
    campus_area_sqft: float,
    institute_id: int | None = None,
    db_path: Path | str | None = None,
) -> int:
    """Insert or update an educational institute profile.

    Returns:
        int: The institute ID.
    """
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        if institute_id:
            cursor.execute(
                """
                UPDATE institutes
                SET name = ?, address = ?, academic_year = ?,
                    total_students = ?, total_staff = ?, campus_area_sqft = ?,
                    updated_at = ?
                WHERE id = ?;
                """,
                (
                    name.strip(),
                    address.strip(),
                    academic_year.strip(),
                    int(total_students),
                    int(total_staff),
                    float(campus_area_sqft),
                    now,
                    institute_id,
                ),
            )
            return institute_id
        else:
            # Check if an institute with this name exists already to update or insert
            cursor.execute("SELECT id FROM institutes WHERE name = ? COLLATE NOCASE;", (name.strip(),))
            row = cursor.fetchone()
            if row:
                inst_id = row["id"]
                cursor.execute(
                    """
                    UPDATE institutes
                    SET name = ?, address = ?, academic_year = ?,
                        total_students = ?, total_staff = ?, campus_area_sqft = ?,
                        updated_at = ?
                    WHERE id = ?;
                    """,
                    (
                        name.strip(),
                        address.strip(),
                        academic_year.strip(),
                        int(total_students),
                        int(total_staff),
                        float(campus_area_sqft),
                        now,
                        inst_id,
                    ),
                )
                return inst_id

            cursor.execute(
                """
                INSERT INTO institutes (
                    name, address, academic_year, total_students, total_staff,
                    campus_area_sqft, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    name.strip(),
                    address.strip(),
                    academic_year.strip(),
                    int(total_students),
                    int(total_staff),
                    float(campus_area_sqft),
                    now,
                    now,
                ),
            )
            return int(cursor.lastrowid)


def list_institutes(db_path: Path | str | None = None) -> list[dict[str, Any]]:
    """List all registered institutes sorted alphabetically by name."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM institutes ORDER BY name ASC;")
        return [dict(row) for row in cursor.fetchall()]


def get_institute(institute_id: int, db_path: Path | str | None = None) -> dict[str, Any] | None:
    """Retrieve an institute profile by ID."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM institutes WHERE id = ?;", (institute_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def delete_institute(institute_id: int, db_path: Path | str | None = None) -> bool:
    """Delete an institute and cascade delete all its monthly and transport records."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM institutes WHERE id = ?;", (institute_id,))
        return cursor.rowcount > 0


def save_monthly_record(
    institute_id: int,
    month: str,
    electricity_kwh: float,
    water_kl: float,
    diesel_litres: float,
    transport_rows_data: list[dict[str, Any]],
    db_path: Path | str | None = None,
) -> int:
    """Calculate and upsert a monthly record and its transport items.

    Args:
        institute_id: ID of the institute.
        month: Month string formatted as 'YYYY-MM'.
        electricity_kwh: Grid electricity consumed in kWh.
        water_kl: Water consumed in kL.
        diesel_litres: Diesel consumed in litres.
        transport_rows_data: List of dicts with keys:
            vehicle_type, vehicle_count, distance_km.

    Returns:
        int: The monthly_record ID.
    """
    init_db(db_path)

    # Compute emissions via calculator logic
    elec_co2 = calculate_electricity_emission(electricity_kwh)
    diesel_co2 = calculate_diesel_emission(diesel_litres)
    water_co2 = calculate_water_emission(water_kl)

    processed_transport: list[dict[str, Any]] = []
    transport_co2_total = 0.0

    for item in transport_rows_data:
        v_type = item["vehicle_type"]
        v_count = int(item["vehicle_count"])
        v_dist = float(item["distance_km"])
        co2_item, factor = calculate_transport_emission(v_type, v_count, v_dist)
        transport_co2_total += co2_item
        processed_transport.append(
            {
                "vehicle_type": v_type,
                "vehicle_count": v_count,
                "distance_km": v_dist,
                "factor": factor,
                "co2_kg": co2_item,
            }
        )

    transport_co2 = round(transport_co2_total, 2)
    total_co2 = calculate_total(elec_co2, diesel_co2, water_co2, transport_co2)
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # Check existing record for (institute_id, month)
        cursor.execute(
            "SELECT id FROM monthly_records WHERE institute_id = ? AND month = ?;",
            (institute_id, month),
        )
        existing = cursor.fetchone()

        if existing:
            record_id = existing["id"]
            cursor.execute(
                """
                UPDATE monthly_records
                SET electricity_kwh = ?, water_kl = ?, diesel_litres = ?,
                    electricity_co2 = ?, diesel_co2 = ?, water_co2 = ?,
                    transport_co2 = ?, total_co2 = ?, updated_at = ?
                WHERE id = ?;
                """,
                (
                    electricity_kwh,
                    water_kl,
                    diesel_litres,
                    elec_co2,
                    diesel_co2,
                    water_co2,
                    transport_co2,
                    total_co2,
                    now,
                    record_id,
                ),
            )
            # Remove previous transport rows to replace with updated list
            cursor.execute("DELETE FROM transport_rows WHERE record_id = ?;", (record_id,))
        else:
            cursor.execute(
                """
                INSERT INTO monthly_records (
                    institute_id, month, electricity_kwh, water_kl, diesel_litres,
                    electricity_co2, diesel_co2, water_co2, transport_co2, total_co2,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    institute_id,
                    month,
                    electricity_kwh,
                    water_kl,
                    diesel_litres,
                    elec_co2,
                    diesel_co2,
                    water_co2,
                    transport_co2,
                    total_co2,
                    now,
                    now,
                ),
            )
            record_id = cursor.lastrowid

        # Insert transport rows
        for t in processed_transport:
            cursor.execute(
                """
                INSERT INTO transport_rows (
                    record_id, vehicle_type, vehicle_count, distance_km, factor, co2_kg
                ) VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    record_id,
                    t["vehicle_type"],
                    t["vehicle_count"],
                    t["distance_km"],
                    t["factor"],
                    t["co2_kg"],
                ),
            )

        return int(record_id)


def get_monthly_records(
    institute_id: int, order_desc: bool = False, db_path: Path | str | None = None
) -> list[dict[str, Any]]:
    """Retrieve all monthly records for an institute.

    Args:
        institute_id: The target institute ID.
        order_desc: If True, order by month DESC (latest first); else month ASC.
    """
    init_db(db_path)
    direction = "DESC" if order_desc else "ASC"
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT * FROM monthly_records
            WHERE institute_id = ?
            ORDER BY month {direction};
            """,
            (institute_id,),
        )
        return [dict(row) for row in cursor.fetchall()]


def get_record(
    institute_id: int, month: str, db_path: Path | str | None = None
) -> dict[str, Any] | None:
    """Retrieve a single monthly record with its transport rows attached."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM monthly_records WHERE institute_id = ? AND month = ?;",
            (institute_id, month),
        )
        rec = cursor.fetchone()
        if not rec:
            return None

        record_dict = dict(rec)
        cursor.execute(
            "SELECT * FROM transport_rows WHERE record_id = ? ORDER BY id ASC;",
            (record_dict["id"],),
        )
        record_dict["transport_rows"] = [dict(row) for row in cursor.fetchall()]
        return record_dict


def delete_month(institute_id: int, month: str, db_path: Path | str | None = None) -> bool:
    """Delete a specific monthly record for an institute."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM monthly_records WHERE institute_id = ? AND month = ?;",
            (institute_id, month),
        )
        return cursor.rowcount > 0


def export_dataframe(institute_id: int, db_path: Path | str | None = None) -> pd.DataFrame:
    """Generate a clean pandas DataFrame for CSV export including institute metadata."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        query = """
        SELECT
            i.name AS institute_name,
            i.academic_year,
            m.month,
            m.electricity_kwh,
            m.electricity_co2 AS electricity_co2_kg,
            m.diesel_litres,
            m.diesel_co2 AS diesel_co2_kg,
            m.water_kl,
            m.water_co2 AS water_co2_kg,
            m.transport_co2 AS transport_co2_kg,
            m.total_co2 AS total_co2_kg,
            m.created_at,
            m.updated_at
        FROM monthly_records m
        JOIN institutes i ON m.institute_id = i.id
        WHERE m.institute_id = ?
        ORDER BY m.month ASC;
        """
        df = pd.read_sql_query(query, conn, params=(institute_id,))
        return df
