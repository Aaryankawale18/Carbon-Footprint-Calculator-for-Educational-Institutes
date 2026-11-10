"""Plotly figure builders for institutional carbon accounting.

Shared across the Calculator and Data modules to maintain visual consistency.
Implements a clean light theme, categorical chronological month axes,
and standardized categorical color palettes:
  - Electricity: #2E7D32 (Green)
  - Diesel Generator: #EF6C00 (Amber/Orange)
  - Water: #0288D1 (Blue)
  - Transportation: #7B1FA2 (Purple)
"""

from datetime import datetime
from typing import Any
import plotly.graph_objects as go

# Canonical category color palette
CATEGORY_COLORS = {
    "Electricity": "#2E7D32",
    "Diesel Generator": "#EF6C00",
    "Water": "#0288D1",
    "Transportation": "#7B1FA2",
}

DEFAULT_FONT = dict(family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif", size=12, color="#1B2A1F")


def format_month_label(month_str: str) -> str:
    """Convert 'YYYY-MM' to formatted label e.g., 'Aug 2026'.

    Falls back to original string if parse fails.
    """
    try:
        dt = datetime.strptime(month_str, "%Y-%m")
        return dt.strftime("%b %Y")
    except Exception:
        return month_str


def apply_standard_layout(fig: go.Figure, title: str | None = None, height: int = 380) -> go.Figure:
    """Apply uniform publication-grade styling to any Plotly figure."""
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>" if title else "",
            font=dict(size=14, color="#1B2A1F", family=DEFAULT_FONT["family"]),
            x=0.02,
            y=0.96,
        ),
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=DEFAULT_FONT,
        height=height,
        margin=dict(l=45, r=30, t=55 if title else 25, b=45),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11),
        ),
        hoverlabel=dict(
            bgcolor="#1B2A1F",
            font_size=12,
            font_family=DEFAULT_FONT["family"],
            font_color="#FFFFFF",
        ),
    )
    return fig


def create_breakdown_donut(breakdown: dict[str, float]) -> go.Figure:
    """Generate a donut chart of carbon emissions breakdown (only non-zero values).

    Args:
        breakdown: Mapping of category name to emissions in kg CO2.
    """
    # Filter out categories with zero emissions
    filtered = {k: v for k, v in breakdown.items() if v > 0}

    if not filtered:
        # Empty fallback chart
        fig = go.Figure()
        fig.add_annotation(
            text="No emissions recorded for this period",
            showarrow=False,
            font=dict(size=13, color="#666666"),
        )
        return apply_standard_layout(fig, title="Emissions Breakdown by Category")

    labels = list(filtered.keys())
    values = list(filtered.values())
    colors = [CATEGORY_COLORS.get(cat, "#4B6351") for cat in labels]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.58,
                marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
                textinfo="percent+label",
                textposition="outside",
                hovertemplate="<b>%{label}</b><br>Emissions: %{value:,.2f} kg CO2<br>Share: %{percent}<extra></extra>",
                showlegend=False,
            )
        ]
    )

    total_val = sum(values)
    fig.add_annotation(
        text=f"<b>Total</b><br>{total_val:,.1f} kg",
        showarrow=False,
        font=dict(size=13, color="#1B2A1F"),
        x=0.5,
        y=0.5,
    )

    return apply_standard_layout(fig, title="Emissions Breakdown by Category", height=350)


def create_category_bar(breakdown: dict[str, float]) -> go.Figure:
    """Generate a category comparison bar chart with value labels above bars."""
    categories = list(breakdown.keys())
    values = [breakdown[c] for c in categories]
    colors = [CATEGORY_COLORS.get(c, "#4B6351") for c in categories]

    fig = go.Figure(
        data=[
            go.Bar(
                x=categories,
                y=values,
                marker=dict(color=colors, line=dict(color="#FFFFFF", width=1)),
                text=[f"{v:,.1f}" for v in values],
                textposition="outside",
                cliponaxis=False,
                hovertemplate="<b>%{x}</b><br>Emissions: %{y:,.2f} kg CO2<extra></extra>",
                width=0.45,
            )
        ]
    )

    fig.update_xaxes(showgrid=False, linecolor="#E0EBE2", tickfont=dict(size=11))
    fig.update_yaxes(
        title="Emissions (kg CO2)",
        showgrid=True,
        gridcolor="#F0F4F1",
        zeroline=True,
        zerolinecolor="#E0EBE2",
    )

    return apply_standard_layout(fig, title="Emissions Comparison by Category", height=350)


def create_monthly_trend_chart(records: list[dict[str, Any]]) -> go.Figure:
    """Generate a chronological monthly trend line chart of total CO2 emissions.

    Ensures the month axis is treated as a clean categorical sequence.
    """
    if not records:
        fig = go.Figure()
        fig.add_annotation(
            text="Insufficient data to render monthly trend",
            showarrow=False,
            font=dict(size=13, color="#666666"),
        )
        return apply_standard_layout(fig, title="Monthly Total Emissions Trend")

    # Sort records chronologically
    sorted_recs = sorted(records, key=lambda r: r["month"])
    month_labels = [format_month_label(r["month"]) for r in sorted_recs]
    total_co2 = [r["total_co2"] for r in sorted_recs]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=month_labels,
            y=total_co2,
            mode="lines+markers",
            line=dict(color="#2E7D32", width=3),
            marker=dict(size=8, color="#2E7D32", symbol="circle"),
            name="Total CO2",
            hovertemplate="<b>%{x}</b><br>Total CO2: %{y:,.2f} kg<extra></extra>",
        )
    )

    fig.update_xaxes(
        type="category",
        categoryorder="array",
        categoryarray=month_labels,
        showgrid=False,
        linecolor="#E0EBE2",
        tickfont=dict(size=11),
    )
    fig.update_yaxes(
        title="Total Emissions (kg CO2)",
        showgrid=True,
        gridcolor="#F0F4F1",
        zeroline=True,
        zerolinecolor="#E0EBE2",
    )

    return apply_standard_layout(fig, title="Monthly Total Emissions Trend", height=360)


def create_stacked_monthly_bar(records: list[dict[str, Any]]) -> go.Figure:
    """Generate a stacked bar chart showing category-wise trend across all months."""
    if not records:
        fig = go.Figure()
        fig.add_annotation(
            text="Insufficient data to render category trend",
            showarrow=False,
            font=dict(size=13, color="#666666"),
        )
        return apply_standard_layout(fig, title="Category-wise Trend Across All Months")

    sorted_recs = sorted(records, key=lambda r: r["month"])
    month_labels = [format_month_label(r["month"]) for r in sorted_recs]

    fig = go.Figure()

    category_keys = [
        ("Electricity", "electricity_co2"),
        ("Diesel Generator", "diesel_co2"),
        ("Water", "water_co2"),
        ("Transportation", "transport_co2"),
    ]

    for cat_name, key in category_keys:
        y_vals = [r.get(key, 0.0) for r in sorted_recs]
        fig.add_trace(
            go.Bar(
                name=cat_name,
                x=month_labels,
                y=y_vals,
                marker=dict(color=CATEGORY_COLORS[cat_name]),
                hovertemplate=f"<b>{cat_name}</b><br>%{{x}}: %{{y:,.2f}} kg CO2<extra></extra>",
            )
        )

    fig.update_layout(barmode="stack", bargap=0.35)
    fig.update_xaxes(
        type="category",
        categoryorder="array",
        categoryarray=month_labels,
        showgrid=False,
        linecolor="#E0EBE2",
        tickfont=dict(size=11),
    )
    fig.update_yaxes(
        title="Emissions (kg CO2)",
        showgrid=True,
        gridcolor="#F0F4F1",
        zeroline=True,
        zerolinecolor="#E0EBE2",
    )

    return apply_standard_layout(fig, title="Category-wise Trend Across All Months", height=380)
