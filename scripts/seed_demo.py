"""Seed script for populating realistic demo data for the Carbon Footprint Calculator.

Creates a sample institute ('Greenfield Institute of Technology') and seeds
three consecutive months of realistic utility consumption and campus fleet activity.
"""

from pathlib import Path
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules.database import (
    get_record,
    init_db,
    save_institute,
    save_monthly_record,
)


def seed_demo_data() -> None:
    """Populate database with demo institute and 3 months of activity records."""
    print("Initializing database...")
    init_db()

    inst_name = "Greenfield Institute of Technology"
    address = "42 Eco Knowledge Park, Sector 12, Bengaluru, Karnataka 560100"
    academic_year = "2026-2027"
    students = 6400
    staff = 520
    campus_area_sqft = 480000.0

    print(f"Creating / updating demo institute: '{inst_name}'...")
    inst_id = save_institute(
        name=inst_name,
        address=address,
        academic_year=academic_year,
        total_students=students,
        total_staff=staff,
        campus_area_sqft=campus_area_sqft,
    )
    print(f"Institute ID: {inst_id}")

    # 3 consecutive months of realistic data
    demo_months = [
        {
            "month": "2026-08",
            "electricity_kwh": 54200.0,
            "diesel_litres": 1450.0,
            "water_kl": 3850.0,
            "transport": [
                {"vehicle_type": "Bus", "vehicle_count": 12, "distance_km": 1400.0},
                {"vehicle_type": "Two-wheeler", "vehicle_count": 180, "distance_km": 240.0},
                {"vehicle_type": "Car Petrol", "vehicle_count": 35, "distance_km": 380.0},
                {"vehicle_type": "Car Diesel", "vehicle_count": 15, "distance_km": 450.0},
            ],
        },
        {
            "month": "2026-09",
            "electricity_kwh": 49800.0,
            "diesel_litres": 1200.0,
            "water_kl": 3600.0,
            "transport": [
                {"vehicle_type": "Bus", "vehicle_count": 12, "distance_km": 1350.0},
                {"vehicle_type": "Two-wheeler", "vehicle_count": 175, "distance_km": 240.0},
                {"vehicle_type": "Car Petrol", "vehicle_count": 32, "distance_km": 360.0},
                {"vehicle_type": "Car Diesel", "vehicle_count": 14, "distance_km": 420.0},
            ],
        },
        {
            "month": "2026-10",
            "electricity_kwh": 45600.0,
            "diesel_litres": 920.0,
            "water_kl": 3400.0,
            "transport": [
                {"vehicle_type": "Bus", "vehicle_count": 12, "distance_km": 1300.0},
                {"vehicle_type": "Two-wheeler", "vehicle_count": 170, "distance_km": 230.0},
                {"vehicle_type": "Car Petrol", "vehicle_count": 30, "distance_km": 350.0},
                {"vehicle_type": "Car Diesel", "vehicle_count": 12, "distance_km": 400.0},
            ],
        },
    ]

    for m in demo_months:
        rec_id = save_monthly_record(
            institute_id=inst_id,
            month=m["month"],
            electricity_kwh=m["electricity_kwh"],
            water_kl=m["water_kl"],
            diesel_litres=m["diesel_litres"],
            transport_rows_data=m["transport"],
        )
        rec = get_record(inst_id, m["month"])
        total_co2 = rec["total_co2"] if rec else 0.0
        print(f"Saved record for {m['month']} (Record ID: {rec_id}) - Total CO2: {total_co2:,.2f} kg")

    print("\nDemo seeding completed successfully.")


if __name__ == "__main__":
    seed_demo_data()
