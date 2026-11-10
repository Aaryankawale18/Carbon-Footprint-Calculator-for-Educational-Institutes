"""Calculation functions for institutional greenhouse gas emissions.

Calculates emissions across electricity, diesel generator, water,
and transportation based on standardized emission factors.
All results are returned in kg CO2.
"""

from modules.emission_factors import get_factor


def calculate_electricity_emission(units_kwh: float) -> float:
    """Calculate emissions from grid electricity consumption.

    Formula: units_kwh * factor (kg CO2 / kWh)
    """
    factor = get_factor("Electricity", "Grid")
    return round(units_kwh * factor, 2)


def calculate_diesel_emission(litres: float) -> float:
    """Calculate emissions from diesel generator usage.

    Formula: litres * factor (kg CO2 / Litre)
    """
    factor = get_factor("Diesel Generator", "DG Set")
    return round(litres * factor, 2)


def calculate_water_emission(kilolitres: float) -> float:
    """Calculate emissions from water supply and wastewater treatment.

    Formula: kilolitres * factor (kg CO2 / kL)
    """
    factor = get_factor("Water", "Supply+Treatment")
    return round(kilolitres * factor, 2)


def calculate_transport_emission(
    vehicle_type: str, vehicle_count: int, distance_km: float
) -> tuple[float, float]:
    """Calculate emissions for a specific vehicle fleet / category.

    Formula: distance_km * vehicle_count * factor (kg CO2 / km)
    Returns:
        tuple[float, float]: (emitted_co2_kg, factor_value)
    """
    factor = get_factor("Transportation", vehicle_type)
    co2 = distance_km * vehicle_count * factor
    return round(co2, 2), factor


def calculate_total(*emissions: float) -> float:
    """Sum arbitrary emission values and return rounded to 2 decimal places."""
    return round(sum(emissions), 2)
