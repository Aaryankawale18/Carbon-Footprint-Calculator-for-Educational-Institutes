"""Automated End-to-End Verification Suite for Carbon Footprint Calculator."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules.calculator import (
    calculate_diesel_emission,
    calculate_electricity_emission,
    calculate_total,
    calculate_transport_emission,
    calculate_water_emission,
)
from modules.charts import (
    create_breakdown_donut,
    create_category_bar,
    create_monthly_trend_chart,
    create_stacked_monthly_bar,
)
from modules.chatbot import build_system_prompt
from modules.database import (
    delete_institute,
    delete_month,
    export_dataframe,
    get_institute,
    get_monthly_records,
    get_record,
    init_db,
    list_institutes,
    save_institute,
    save_monthly_record,
)
from modules.emission_factors import get_all_factors, get_factor, list_subcategories


def run_all_tests():
    print("=== STARTING COMPREHENSIVE E2E VERIFICATION ===")

    # 1. Emission Factors Verification
    print("\n[1] Testing Emission Factors...")
    df = get_all_factors()
    assert len(df) == 7, f"Expected 7 emission factors, got {len(df)}"
    assert get_factor("Electricity", "Grid") == 0.82
    assert get_factor("Diesel Generator", "DG Set") == 2.68
    assert get_factor("Water", "Supply+Treatment") == 0.298
    assert get_factor("Transportation", "Bus") == 0.90
    assert get_factor("Transportation", "Two-wheeler") == 0.05
    assert get_factor("Transportation", "Car Petrol") == 0.12
    assert get_factor("Transportation", "Car Diesel") == 0.14
    print("-> Emission factors verified successfully.")

    # 2. Calculator Formulas Verification
    print("\n[2] Testing Calculator Formulas...")
    e_co2 = calculate_electricity_emission(1000)
    assert e_co2 == 820.0, f"Expected 820.0, got {e_co2}"
    d_co2 = calculate_diesel_emission(100)
    assert d_co2 == 268.0, f"Expected 268.0, got {d_co2}"
    w_co2 = calculate_water_emission(500)
    assert w_co2 == 149.0, f"Expected 149.0, got {w_co2}"
    t_co2, factor = calculate_transport_emission("Bus", 10, 50)
    assert t_co2 == 450.0, f"Expected 450.0, got {t_co2}"
    assert factor == 0.90
    tot = calculate_total(e_co2, d_co2, w_co2, t_co2)
    assert tot == 1687.0, f"Expected 1687.0, got {tot}"
    print("-> Calculator logic verified successfully.")

    # 3. Multi-Institute Creation & Isolation
    print("\n[3] Testing Multi-Institute Creation...")
    inst1_id = save_institute(
        name="Institute Alpha Technical University",
        address="Sector 14, Academic City",
        academic_year="2026-2027",
        total_students=8000,
        total_staff=600,
        campus_area_sqft=550000.0,
    )
    inst2_id = save_institute(
        name="Institute Beta Medical College",
        address="Ring Road, Healthcare Hub",
        academic_year="2026-2027",
        total_students=3500,
        total_staff=400,
        campus_area_sqft=320000.0,
    )
    assert inst1_id != inst2_id

    inst1 = get_institute(inst1_id)
    inst2 = get_institute(inst2_id)
    assert inst1["name"] == "Institute Alpha Technical University"
    assert inst2["name"] == "Institute Beta Medical College"
    print(f"-> Created Institute 1 (ID {inst1_id}) and Institute 2 (ID {inst2_id}) successfully.")

    # 4. Save Different Monthly Data for Each Institute
    print("\n[4] Testing Distinct Monthly Records for Each Institute...")
    rec1_id = save_monthly_record(
        institute_id=inst1_id,
        month="2026-08",
        electricity_kwh=40000,
        water_kl=2000,
        diesel_litres=800,
        transport_rows_data=[
            {"vehicle_type": "Bus", "vehicle_count": 5, "distance_km": 1000},
            {"vehicle_type": "Two-wheeler", "vehicle_count": 50, "distance_km": 200},
        ],
    )
    rec2_id = save_monthly_record(
        institute_id=inst2_id,
        month="2026-09",
        electricity_kwh=25000,
        water_kl=1500,
        diesel_litres=400,
        transport_rows_data=[
            {"vehicle_type": "Car Petrol", "vehicle_count": 20, "distance_km": 300},
        ],
    )

    inst1_recs = get_monthly_records(inst1_id)
    inst2_recs = get_monthly_records(inst2_id)
    assert len(inst1_recs) == 1 and inst1_recs[0]["month"] == "2026-08"
    assert len(inst2_recs) == 1 and inst2_recs[0]["month"] == "2026-09"
    assert inst1_recs[0]["institute_id"] == inst1_id
    assert inst2_recs[0]["institute_id"] == inst2_id
    print("-> Verified complete isolation between institutes.")

    # 5. Overwrite Existing Record
    print("\n[5] Testing Overwrite of Existing Record...")
    rec1_updated_id = save_monthly_record(
        institute_id=inst1_id,
        month="2026-08",
        electricity_kwh=45000,  # increased from 40000
        water_kl=2000,
        diesel_litres=800,
        transport_rows_data=[
            {"vehicle_type": "Bus", "vehicle_count": 5, "distance_km": 1000},
        ],
    )
    assert rec1_updated_id == rec1_id, "Overwrite must update same record ID"
    rec1_fetched = get_record(inst1_id, "2026-08")
    assert rec1_fetched["electricity_kwh"] == 45000
    assert len(rec1_fetched["transport_rows"]) == 1
    print("-> Overwrite verified: Record ID preserved, values and transport rows updated.")

    # 6. CSV Export Verification
    print("\n[6] Testing CSV Export...")
    df_exp = export_dataframe(inst1_id)
    assert not df_exp.empty
    assert "institute_name" in df_exp.columns
    assert df_exp.iloc[0]["institute_name"] == "Institute Alpha Technical University"
    assert "total_co2_kg" in df_exp.columns
    print(f"-> Export DataFrame verified ({len(df_exp)} rows).")

    # 7. Record Deletion & Cascade Verification
    print("\n[7] Testing Record & Transport Row Cascade Deletion...")
    # Add a second month for institute 1 to delete
    save_monthly_record(
        institute_id=inst1_id,
        month="2026-09",
        electricity_kwh=30000,
        water_kl=1000,
        diesel_litres=500,
        transport_rows_data=[{"vehicle_type": "Bus", "vehicle_count": 2, "distance_km": 500}],
    )
    assert len(get_monthly_records(inst1_id)) == 2
    deleted = delete_month(inst1_id, "2026-09")
    assert deleted is True
    assert len(get_monthly_records(inst1_id)) == 1
    assert get_record(inst1_id, "2026-09") is None
    print("-> delete_month verified successfully.")

    # Delete institute and cascade
    deleted_inst = delete_institute(inst1_id)
    assert deleted_inst is True
    assert get_institute(inst1_id) is None
    assert len(get_monthly_records(inst1_id)) == 0
    print("-> delete_institute and cascade verified successfully.")

    # Clean up test institute 2
    delete_institute(inst2_id)
    assert get_institute(inst2_id) is None
    print("-> Test Institute 2 cleaned up.")

    # 8. Plotly Charts Generation
    print("\n[8] Testing Plotly Figure Builders...")
    sample_breakdown = {"Electricity": 5000.0, "Diesel Generator": 1200.0, "Water": 300.0, "Transportation": 800.0}
    fig1 = create_breakdown_donut(sample_breakdown)
    fig2 = create_category_bar(sample_breakdown)
    sample_records = [
        {"month": "2026-08", "total_co2": 7300.0, "electricity_co2": 5000.0, "diesel_co2": 1200.0, "water_co2": 300.0, "transport_co2": 800.0},
        {"month": "2026-09", "total_co2": 6900.0, "electricity_co2": 4700.0, "diesel_co2": 1100.0, "water_co2": 300.0, "transport_co2": 800.0},
    ]
    fig3 = create_monthly_trend_chart(sample_records)
    fig4 = create_stacked_monthly_bar(sample_records)
    assert fig1 is not None and fig2 is not None and fig3 is not None and fig4 is not None
    print("-> All 4 Plotly charts generated successfully.")

    # 9. Chatbot System Prompt Construction
    print("\n[9] Testing Chatbot System Prompt Generation...")
    demo_inst = list_institutes()[0]  # Greenfield demo institute
    demo_recs = get_monthly_records(demo_inst["id"])
    prompt = build_system_prompt(demo_inst, demo_recs)
    assert demo_inst["name"] in prompt
    assert "CEA 2023" in prompt
    assert "IPCC" in prompt
    assert "2026-08" in prompt or "2026-10" in prompt
    print("-> Chatbot system prompt dynamically generated and grounded in real data.")

    # 10. Multi-Provider & Analytical Advisor Engine Verification
    print("\n[10] Testing Multi-Provider & Analytical Advisor Engine...")
    from modules.chatbot import detect_provider, run_analytical_advisor, stream_advisor_response

    provider, _, status = detect_provider()
    print(f"-> Detected provider: {provider} ({status})")

    # Test top emitter inquiry
    q1_resp = run_analytical_advisor("Which category emits the most?", demo_inst, demo_recs)
    assert "Electricity" in q1_resp or "Primary Emission" in q1_resp
    assert "kg CO2" in q1_resp

    # Test transport inquiry
    q2_resp = run_analytical_advisor("How can we reduce transport emissions?", demo_inst, demo_recs)
    assert "Bus" in q2_resp or "Transportation" in q2_resp

    # Test streaming generator
    stream_chunks = list(stream_advisor_response([{"role": "user", "content": "Which category emits the most?"}], demo_inst, demo_recs))
    assert len(stream_chunks) > 0
    full_stream_text = "".join(stream_chunks)
    assert len(full_stream_text) > 50
    print("-> Analytical advisor stream successfully generated.")

    print("\n=== ALL E2E VERIFICATIONS PASSED SUCCESSFULLY ===")


if __name__ == "__main__":
    run_all_tests()
