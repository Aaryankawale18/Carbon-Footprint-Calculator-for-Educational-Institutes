"""Emission factors loader and query utilities.

Reads standardized emission factors from data/emission_factors.csv
and provides lookup utilities for carbon footprint calculations.
"""

from pathlib import Path
import pandas as pd

# Locate data/emission_factors.csv relative to this module
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "emission_factors.csv"

_FACTORS_DF: pd.DataFrame | None = None


def load_emission_factors() -> pd.DataFrame:
    """Load and cache emission factors CSV into a pandas DataFrame."""
    global _FACTORS_DF
    if _FACTORS_DF is None:
        if not DATA_PATH.exists():
            raise FileNotFoundError(f"Emission factors file not found at: {DATA_PATH}")
        _FACTORS_DF = pd.read_csv(DATA_PATH)
    return _FACTORS_DF


def get_factor(category: str, subcategory: str) -> float:
    """Retrieve factor_value for given category and subcategory.

    Args:
        category: Emission category (e.g., 'Electricity', 'Transportation')
        subcategory: Emission subcategory (e.g., 'Grid', 'Bus')

    Returns:
        float: Factor value in kg CO2 per unit.

    Raises:
        ValueError: If category or subcategory is not found.
    """
    df = load_emission_factors()
    match = df[(df["category"] == category) & (df["subcategory"] == subcategory)]
    if match.empty:
        raise ValueError(f"Emission factor not found for category='{category}', subcategory='{subcategory}'")
    return float(match.iloc[0]["factor_value"])


def list_subcategories(category: str) -> list[str]:
    """Return all subcategories under a given category."""
    df = load_emission_factors()
    return df[df["category"] == category]["subcategory"].tolist()


def get_all_factors() -> pd.DataFrame:
    """Return a copy of the entire emission factors table."""
    return load_emission_factors().copy()
