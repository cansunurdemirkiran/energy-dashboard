"""
Global Energy Transition Dashboard
====================================
Author : Cansu Nur Demirkıran
Dataset: Our World in Data — Energy Dataset
Run    : python app.py  →  http://127.0.0.1:8050

Six interactive visualisations:
    1. Time Series Plot      — Renewable share over time (multi-country)
    2. Choropleth Map        — Renewable share by country (year slider)
    3. Scatter Plot          — GDP per capita vs energy intensity
    4. Heatmap               — Energy source mix by region
    5. Violin / Distribution — CO₂ per capita by continent
    6. Sunburst              — Energy generation hierarchy
"""

import os
import warnings

import dash
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────
# 1.  LOAD DATA
# ─────────────────────────────────────────
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "owid-energy-cleaned.csv")
df = pd.read_csv(DATA_PATH)
df_countries = df[df["country"] != "World"].copy()
df_world = df[df["country"] == "World"].copy()

COUNTRIES = sorted(df_countries["country"].unique().tolist())
YEARS = sorted(df["year"].unique().tolist())
CONTINENTS = sorted(df_countries["continent"].unique().tolist())

# ─────────────────────────────────────────
# 2.  PLOTLY TEMPLATE / COLOUR PALETTE
# ─────────────────────────────────────────
TEMPLATE = "plotly_white"
FOSSIL_COLORS = {
    "Coal":    "#2c3e50",
    "Gas":     "#7f8c8d",
    "Oil":     "#95a5a6",
    "Hydro":   "#2980b9",
    "Wind":    "#27ae60",
    "Solar":   "#f39c12",
    "Nuclear": "#8e44ad",
}

# ─────────────────────────────────────────
# 3.  STATIC FIGURES  (built once at startup)
# ─────────────────────────────────────────

def build_heatmap():
    """Heatmap of energy source mix per continent (2022, static)."""
    source_cols = [
        "coal_share_energy", "oil_share_energy", "gas_share_energy",
        "hydro_share_energy", "wind_share_energy", "solar_share_energy",
    ]
    labels = ["Coal", "Oil", "Gas", "Hydro", "Wind", "Solar"]

    d = (
        df_countries[df_countries["year"] == 2022]
        .groupby("continent")[source_cols]
        .mean()
        .round(1)
    )
    d.columns = labels

    fig = go.Figure(
        go.Heatmap(
            z=d.values,
            x=labels,
            y=d.index.tolist(),
            colorscale="RdYlGn_r",
            zmin=0,
            zmax=50,
            text=d.values,
            texttemplate="%{text:.1f}%",
            textfont={"size": 11},
            hovertemplate="<b>%{y}</b><br>%{x}: %{z:.1f}%<extra></extra>",
            colorbar=dict(title="Share %"),
        )
    )
    fig.update_layout(
        template=TEMPLATE,
        title="Energy Source Mix by Region (2022)",
        xaxis_title="Energy Source",
        yaxis_title="",
        margin=dict(l=20, r=20, t=50, b=20),
        height=320,
    )
    return fig


def build_sunburst():
    """Sunburst: Continent → Country → Energy Source (2022, top-5 per continent, static)."""
    source_map = {
        "coal_electricity":    "Coal",
        "gas_electricity":     "Gas",
        "oil_electricity":     "Oil",
        "solar_electricity":   "Solar",
        "wind_electricity":    "Wind",
        "hydro_electricity":   "Hydro",
        "nuclear_electricity": "Nuclear",
    }

    df_2022 = df_countries[df_countries["year"] == 2022].copy()
    # Top 5 countries per continent by electricity_generation
    top5 = (
        df_2022.sort_values("electricity_generation", ascending=False)
        .groupby("continent")
        .head(5)
    )

    rows = []
    for _, row in top5.iterrows():
        for col, label in source_map.items():
            val = row.get(col, 0)
            if pd.notna(val) and val > 0:
                rows.append(
                    {
                        "continent": row["continent"],
                        "country": row["country"],
                        "source": label,
                        "value": val,
                    }
                )

    long_df = pd.DataFrame(rows)

    fig = px.sunburst(
        long_df,
        path=["continent", "country", "source"],
        values="value",
        color="source",
        color_discrete_map=FOSSIL_COLORS,
        title="Electricity Generation Hierarchy: Continent → Country → Source (2022)",
        template=TEMPLATE,
    )
    fig.update_traces(textfont_size=11)
    fig.update_layout(
        margin=dict(l=10, r=10, t=50, b=10),
        height=580,
    )
    return fig


HEATMAP_FIG = build_heatmap()
SUNBURST_FIG = build_sunburst()

# ─────────────────────────────────────────
# 4.  APP LAYOUT
# ─────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    title="Global Energy Transition Dashboard",
    suppress_callback_exceptions=True,
)

NAVBAR = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                dbc.Row(
                    [
                        dbc.Col(html.I(className="bi bi-lightning-charge-fill me-2",
                                       style={"fontSize": "1.4rem", "color": "#f39c12"})),
                        dbc.Col(dbc.NavbarBrand("Global Energy Transition Dashboard",
                                                className="ms-1 fw-bold")),
                    ],
                    align="center",
                ),
                href="/",
                style={"textDecoration": "none"},
            ),
            dbc.Nav(
                [
                    dbc.NavItem(dbc.NavLink("Time Series", href="#chart-timeseries", external_link=True)),
                    dbc.NavItem(dbc.NavLink("World Map",   href="#chart-map",        external_link=True)),
                    dbc.NavItem(dbc.NavLink("Scatter",     href="#chart-scatter",    external_link=True)),
                    dbc.NavItem(dbc.NavLink("Heatmap",     href="#chart-heatmap",    external_link=True)),
                    dbc.NavItem(dbc.NavLink("Distribution",href="#chart-violin",     external_link=True)),
                    dbc.NavItem(dbc.NavLink("Hierarchy",   href="#chart-sunburst",   external_link=True)),
                ],
                className="ms-auto",
                navbar=True,
            ),
        ],
        fluid=True,
    ),
    color="dark",
    dark=True,
    sticky="top",
    className="mb-3",
)

FOOTER = html.Footer(
    dbc.Container(
        html.P(
            "Built by Cansu Nur Demirkıran "
            "with Plotly Dash & Python",
            className="text-center text-muted small py-3",
        )
    )
)


def card(title, children, anchor_id=""):
    """Wrap content in a styled dbc.Card."""
    return html.Div(
        dbc.Card(
            [
                dbc.CardHeader(html.H6(title, className="mb-0 fw-semibold text-dark")),
                dbc.CardBody(children, className="p-2"),
            ],
            className="shadow-sm mb-4",
        ),
        id=anchor_id,
    )


# ── Chart 1: Time Series ──────────────────────────────────────
CHART1 = card(
    "Renewable Energy Share Over Time",
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label("Select Countries:", className="small fw-semibold"),
                        dcc.Dropdown(
                            id="ts-country-dd",
                            options=[{"label": c, "value": c} for c in COUNTRIES],
                            value=["World", "Germany", "China", "United States", "Brazil"],
                            multi=True,
                            clearable=False,
                        ),
                    ],
                    md=8,
                ),
                dbc.Col(
                    [
                        html.Label("Year Range:", className="small fw-semibold"),
                        dcc.RangeSlider(
                            id="ts-year-slider",
                            min=1990, max=2022, step=1,
                            value=[1990, 2022],
                            marks={y: str(y) for y in range(1990, 2023, 4)},
                            tooltip={"placement": "bottom"},
                        ),
                    ],
                    md=4,
                ),
            ],
            className="mb-2",
        ),
        dcc.Graph(id="ts-chart", config={"displayModeBar": False}, style={"height": "370px"}),
    ],
    anchor_id="chart-timeseries",
)

# ── Chart 2: Choropleth ───────────────────────────────────────
CHART2 = card(
    "Renewable Energy Share by Country",
    [
        html.Label("Select Year:", className="small fw-semibold"),
        dcc.Slider(
            id="map-year-slider",
            min=1990, max=2022, step=1,
            value=2022,
            marks={y: str(y) for y in range(1990, 2023, 4)},
            tooltip={"placement": "bottom"},
        ),
        dcc.Graph(id="map-chart", config={"displayModeBar": False}, style={"height": "360px"}),
    ],
    anchor_id="chart-map",
)

# ── Chart 3: Scatter ──────────────────────────────────────────
CHART3 = card(
    "GDP per Capita vs. Energy Intensity",
    [
        html.Label("Filter by Continent:", className="small fw-semibold"),
        dcc.Checklist(
            id="scatter-continent-check",
            options=[{"label": f"  {c}", "value": c} for c in CONTINENTS],
            value=CONTINENTS,
            inline=True,
            className="mb-2 small",
            labelStyle={"marginRight": "14px"},
        ),
        dcc.Graph(id="scatter-chart", config={"displayModeBar": False}, style={"height": "380px"}),
    ],
    anchor_id="chart-scatter",
)

# ── Chart 4: Heatmap (static) ─────────────────────────────────
CHART4 = card(
    "Energy Source Mix by Region (2022)",
    dcc.Graph(figure=HEATMAP_FIG, config={"displayModeBar": False}, style={"height": "320px"}),
    anchor_id="chart-heatmap",
)

# ── Chart 5: Violin ───────────────────────────────────────────
CHART5 = card(
    "CO₂ Per Capita Distribution by Continent",
    [
        html.Label("Select Decade:", className="small fw-semibold"),
        dcc.RadioItems(
            id="violin-decade-radio",
            options=[
                {"label": "  2000s (year 2000)", "value": 2000},
                {"label": "  2010s (year 2010)", "value": 2010},
                {"label": "  2020s (year 2022)", "value": 2022},
            ],
            value=2022,
            inline=True,
            className="mb-2 small",
            labelStyle={"marginRight": "18px"},
        ),
        dcc.Graph(id="violin-chart", config={"displayModeBar": False}, style={"height": "370px"}),
    ],
    anchor_id="chart-violin",
)

# ── Chart 6: Sunburst (static) ────────────────────────────────
CHART6 = card(
    "Electricity Generation Hierarchy: Continent → Country → Source (2022)",
    dcc.Graph(figure=SUNBURST_FIG, config={"displayModeBar": False}, style={"height": "580px"}),
    anchor_id="chart-sunburst",
)

app.layout = html.Div(
    [
        NAVBAR,
        dbc.Container(
            [
                # Row 1: Time series (full width)
                dbc.Row(dbc.Col(CHART1, width=12)),
                # Row 2: Map (8) + Heatmap (4)
                dbc.Row([dbc.Col(CHART2, md=8), dbc.Col(CHART4, md=4)]),
                # Row 3: Scatter (6) + Violin (6)
                dbc.Row([dbc.Col(CHART3, md=6), dbc.Col(CHART5, md=6)]),
                # Row 4: Sunburst (full width)
                dbc.Row(dbc.Col(CHART6, width=12)),
            ],
            fluid=True,
            className="px-3",
        ),
        FOOTER,
    ],
    style={"backgroundColor": "#f8f9fa", "minHeight": "100vh"},
)

# ─────────────────────────────────────────
# 5.  CALLBACKS
# ─────────────────────────────────────────


@app.callback(
    Output("ts-chart", "figure"),
    Input("ts-country-dd", "value"),
    Input("ts-year-slider", "value"),
)
def update_timeseries(selected_countries, year_range):
    """
    Update the time-series line chart.

    Parameters
    ----------
    selected_countries : list[str]
    year_range         : [int, int]

    Returns
    -------
    plotly.graph_objects.Figure
    """
    if not selected_countries:
        selected_countries = ["World"]

    mask = (
        df["country"].isin(selected_countries)
        & df["year"].between(year_range[0], year_range[1])
    )
    filtered = df[mask].sort_values(["country", "year"])

    fig = px.line(
        filtered,
        x="year",
        y="renewables_share_energy",
        color="country",
        markers=True,
        labels={"renewables_share_energy": "Renewables Share (%)", "year": "Year", "country": "Country"},
        template=TEMPLATE,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )

    # Paris Agreement vertical line
    fig.add_vline(
        x=2015,
        line_dash="dash",
        line_color="gray",
        opacity=0.6,
        annotation_text="Paris Agreement",
        annotation_position="top right",
        annotation_font_size=10,
    )

    fig.update_traces(marker=dict(size=4))
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=10, t=40, b=40),
        hovermode="x unified",
    )
    return fig


@app.callback(
    Output("map-chart", "figure"),
    Input("map-year-slider", "value"),
)
def update_choropleth(selected_year):
    """
    Update the choropleth world map.

    Parameters
    ----------
    selected_year : int

    Returns
    -------
    plotly.graph_objects.Figure
    """
    filtered = df_countries[df_countries["year"] == selected_year].copy()

    fig = px.choropleth(
        filtered,
        locations="iso_code",
        color="renewables_share_energy",
        hover_name="country",
        hover_data={
            "iso_code": False,
            "renewables_share_energy": ":.1f",
            "gdp_per_capita": ":,.0f",
            "co2_per_capita": ":.2f",
        },
        color_continuous_scale="YlGn",
        range_color=(0, 100),
        labels={
            "renewables_share_energy": "Renewables %",
            "gdp_per_capita": "GDP/capita (USD)",
            "co2_per_capita": "CO₂/capita (t)",
        },
        title=f"Renewable Energy Share by Country — {selected_year}",
        template=TEMPLATE,
    )
    fig.update_layout(
        coloraxis_colorbar=dict(title="Renew %", len=0.7),
        geo=dict(showframe=False, showcoastlines=True, projection_type="natural earth"),
        margin=dict(l=0, r=0, t=40, b=0),
    )
    return fig


@app.callback(
    Output("scatter-chart", "figure"),
    Input("scatter-continent-check", "value"),
)
def update_scatter(selected_continents):
    """
    Update the GDP vs energy intensity scatter plot.

    Parameters
    ----------
    selected_continents : list[str]

    Returns
    -------
    plotly.graph_objects.Figure
    """
    filtered = df_countries[
        (df_countries["year"] == 2022)
        & (df_countries["continent"].isin(selected_continents))
    ].dropna(subset=["gdp_per_capita", "energy_per_gdp", "population"])

    fig = px.scatter(
        filtered,
        x="gdp_per_capita",
        y="energy_per_gdp",
        size="population",
        color="continent",
        hover_name="country",
        hover_data={
            "gdp_per_capita": ":,.0f",
            "energy_per_gdp": ":.4f",
            "population": ":,.0f",
            "renewables_share_energy": ":.1f",
        },
        size_max=55,
        log_x=True,
        trendline="ols",
        labels={
            "gdp_per_capita": "GDP per Capita (USD, log scale)",
            "energy_per_gdp": "Energy Intensity (energy / GDP)",
            "continent": "Continent",
        },
        template=TEMPLATE,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=10, t=50, b=40),
    )
    return fig


@app.callback(
    Output("violin-chart", "figure"),
    Input("violin-decade-radio", "value"),
)
def update_violin(selected_year):
    """
    Update the CO₂ per capita violin/box plot.

    Parameters
    ----------
    selected_year : int  (2000, 2010, or 2022)

    Returns
    -------
    plotly.graph_objects.Figure
    """
    filtered = df_countries[df_countries["year"] == selected_year].dropna(
        subset=["co2_per_capita"]
    )

    fig = px.violin(
        filtered,
        x="continent",
        y="co2_per_capita",
        color="continent",
        box=True,
        points="outliers",
        hover_name="country",
        labels={
            "continent": "Continent",
            "co2_per_capita": "CO₂ per Capita (tonnes)",
        },
        title=f"CO₂ per Capita Distribution by Continent ({selected_year})",
        template=TEMPLATE,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(
        showlegend=False,
        margin=dict(l=40, r=10, t=50, b=40),
        xaxis_title="",
    )
    return fig


# ─────────────────────────────────────────
# 6.  ENTRY POINT
# ─────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=8050)
