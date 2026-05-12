import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc

from utils.generate_data import generate_events, save_to_db, DB_PATH
from utils.funnel import (
    overall_funnel, segmented_funnel,
    leakage_heatmap, daily_trend,
    revenue_by_segment, hourly_conversion,
    fix_recommendations, significance_test,
    kpi_snapshot
)

BG     = "#080b10"
SURF   = "#0e1218"
SURF2  = "#141920"
SURF3  = "#1c2330"
ACC    = "#00d9a3"
ACC2   = "#4f8bff"
DANGER = "#ff5e5e"
WARN   = "#ffc44d"
TEXT   = "#eef0f6"
MUTED  = "#7a849a"
BORDER = "rgba(255,255,255,0.06)"

STAGE_COLORS = [ACC, ACC2, WARN, "#fa8b8b"]
SEG_COLORS   = [ACC, ACC2, DANGER, WARN, "#fa8be9", "#34d399"]

def base_layout(fig, title=""):
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=14, color=TEXT),
            x=0
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=MUTED, size=11),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11, color=MUTED)
        ),
        margin=dict(l=8, r=8, t=38, b=8),
        xaxis=dict(gridcolor=BORDER, zeroline=False),
        yaxis=dict(gridcolor=BORDER, zeroline=False),
    )
    return fig


def kpi_card(label, value, sub="", positive=True):
    return html.Div([
        html.P(
            label,
            style={
                "fontSize": "11px",
                "color": MUTED,
                "margin": "0 0 6px",
                "letterSpacing": ".07em"
            }
        ),
        html.H3(
            value,
            style={
                "fontSize": "22px",
                "fontWeight": "700",
                "color": TEXT,
                "margin": "0"
            }
        ),
        html.P(
            sub,
            style={
                "fontSize": "11px",
                "color": ACC if positive else DANGER,
                "margin": "4px 0 0"
            }
        ),
    ], style={
        "background": SURF,
        "border": f"1px solid {BORDER}",
        "borderRadius": "10px",
        "padding": "16px 18px",
    })

if not DB_PATH.exists():
    print("[app] No database found — generating data...")
    df = generate_events(15000, 90)
    save_to_db(df)

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Funnel Analysis | Dhruv Dedhia",
    suppress_callback_exceptions=True
)

SEGS = [
    {"label": "Device",         "value": "device"},
    {"label": "Traffic Source", "value": "traffic_source"},
    {"label": "Location",       "value": "location"},
]

app.layout = html.Div(
    style={
        "backgroundColor": BG,
        "minHeight": "100vh",
        "fontFamily": "'DM Sans', sans-serif",
        "color": TEXT
    },
    children=[

        # ── Navigation bar ──
        html.Div([
            html.Div([
                html.H1(
                    "User Journey Funnel Analysis",
                    style={
                        "fontSize": "19px",
                        "fontWeight": "700",
                        "color": TEXT,
                        "margin": "0"
                    }
                ),
                html.Span(
                    "Dhruv Dedhia · MSc Data Science",
                    style={"fontSize": "11px", "color": MUTED}
                ),
            ]),
            html.Div([
                html.Label(
                    "Segment by",
                    style={
                        "fontSize": "12px",
                        "color": MUTED,
                        "marginRight": "8px"
                    }
                ),
                dcc.Dropdown(
                    id="seg-select",
                    options=SEGS,
                    value="device",
                    clearable=False,
                    style={"width": "160px", "fontSize": "13px"},
                ),
            ], style={"display": "flex", "alignItems": "center"}),
        ], style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "padding": "14px 28px",
            "borderBottom": f"1px solid {BORDER}",
            "background": SURF
        }),

        # ── Main content ──
        html.Div(style={"padding": "20px 28px"}, children=[

            # KPI row — 4 cards
            html.Div(
                id="kpi-row",
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(4, 1fr)",
                    "gap": "14px",
                    "marginBottom": "20px"
                }
            ),

            # Row 1 — Main funnel + segmented bar
            html.Div([
                html.Div(
                    [dcc.Graph(
                        id="funnel-main",
                        config={"displayModeBar": False},
                        style={"height": "360px"}
                    )],
                    style={
                        "flex": "1",
                        "background": SURF,
                        "borderRadius": "10px",
                        "border": f"1px solid {BORDER}",
                        "padding": "8px"
                    }
                ),
                html.Div(
                    [dcc.Graph(
                        id="funnel-seg",
                        config={"displayModeBar": False},
                        style={"height": "360px"}
                    )],
                    style={
                        "flex": "1.2",
                        "background": SURF,
                        "borderRadius": "10px",
                        "border": f"1px solid {BORDER}",
                        "padding": "8px"
                    }
                ),
            ], style={
                "display": "flex",
                "gap": "16px",
                "marginBottom": "16px"
            }),

            # Row 2 — Drop-off bar + leakage heatmap
            html.Div([
                html.Div(
                    [dcc.Graph(
                        id="dropoff-chart",
                        config={"displayModeBar": False},
                        style={"height": "280px"}
                    )],
                    style={
                        "flex": "1",
                        "background": SURF,
                        "borderRadius": "10px",
                        "border": f"1px solid {BORDER}",
                        "padding": "8px"
                    }
                ),
                html.Div(
                    [dcc.Graph(
                        id="heatmap-chart",
                        config={"displayModeBar": False},
                        style={"height": "280px"}
                    )],
                    style={
                        "flex": "1",
                        "background": SURF,
                        "borderRadius": "10px",
                        "border": f"1px solid {BORDER}",
                        "padding": "8px"
                    }
                ),
            ], style={
                "display": "flex",
                "gap": "16px",
                "marginBottom": "16px"
            }),

            # Row 3 — Recommendations panel
            html.Div([
                html.P(
                    "Fix Recommendations",
                    style={
                        "fontSize": "13px",
                        "fontWeight": "600",
                        "color": TEXT,
                        "marginBottom": "14px"
                    }
                ),
                html.Div(id="recs-panel"),
            ], style={
                "background": SURF,
                "borderRadius": "10px",
                "border": f"1px solid {BORDER}",
                "padding": "20px"
            }),
        ]),
    ]
)


@app.callback(
    Output("kpi-row",       "children"),
    Output("funnel-main",   "figure"),
    Output("funnel-seg",    "figure"),
    Output("dropoff-chart", "figure"),
    Output("heatmap-chart", "figure"),
    Output("recs-panel",    "children"),
    Input("seg-select",     "value"),
)
def update(segment):

    # ── Get all data ──
    kpis    = kpi_snapshot()
    overall = overall_funnel()
    seg_df  = segmented_funnel(segment)
    recs    = fix_recommendations()

    # ── KPI cards ──
    kpi_row = [
        kpi_card(
            "Total Visitors",
            f"{kpis['total_visitors']:,}",
            "90 day period",
            True
        ),
        kpi_card(
            "Overall Conversion",
            f"{kpis['overall_conv_pct']}%",
            "Visit to Purchase",
            kpis["overall_conv_pct"] > 5
        ),
        kpi_card(
            "Total Revenue",
            f"₹{kpis['total_revenue']:,.0f}",
            "90 days",
            True
        ),
        kpi_card(
            "Avg Order Value",
            f"₹{kpis['avg_order_value']:,.0f}",
            f"₹{kpis['revenue_per_visitor']} per visitor",
            True
        ),
    ]

    # ── Main funnel chart ──
    fig_funnel = go.Figure(go.Funnel(
        y=overall["stage_name"].tolist(),
        x=overall["users"].tolist(),
        textinfo="value+percent initial",
        marker=dict(
            color=STAGE_COLORS,
            line=dict(width=0)
        ),
        textfont=dict(color=TEXT, size=13),
    ))
    base_layout(fig_funnel, "Overall Funnel — Visit to Purchase")

    # ── Segmented grouped bar chart ──
    seg_keys = seg_df["seg"].tolist()
    fig_seg  = go.Figure()
    for i, stage in enumerate(["visit", "signup", "add_to_cart", "purchase"]):
        label = ["Visit", "Sign Up", "Add to Cart", "Purchase"][i]
        fig_seg.add_trace(go.Bar(
            name=label,
            x=seg_keys,
            y=seg_df[stage].tolist(),
            marker_color=STAGE_COLORS[i],
            marker_line_width=0,
        ))
    fig_seg.update_layout(barmode="group", bargap=0.2)
    base_layout(fig_seg, f"Funnel by {segment.replace('_', ' ').title()}")

    # ── Drop-off bar chart ──
    drop_col = "drop_add_to_cart_to_purchase"
    if drop_col in seg_df.columns:
        colors = [
            DANGER if v > 60
            else WARN if v > 45
            else ACC
            for v in seg_df[drop_col]
        ]
        fig_drop = go.Figure(go.Bar(
            x=seg_df["seg"],
            y=seg_df[drop_col],
            marker_color=colors,
            marker_line_width=0,
            hovertemplate="%{x}<br>Drop-off: %{y:.1f}%<extra></extra>",
        ))
        base_layout(fig_drop, "Cart → Purchase Drop-off by Segment (%)")
    else:
        fig_drop = go.Figure()

    # ── Leakage heatmap ──
    hmap      = leakage_heatmap(segment)
    hmap_cols = [c for c in hmap.columns if c != "Segment"]
    fig_heat  = go.Figure(go.Heatmap(
        z=hmap[hmap_cols].values,
        x=hmap_cols,
        y=hmap["Segment"].tolist(),
        colorscale=[
            [0,   "rgba(0,217,163,.15)"],
            [0.5, "rgba(255,196,77,.4)"],
            [1,   "rgba(255,94,94,.8)"]
        ],
        text=hmap[hmap_cols].round(1).astype(str).values,
        texttemplate="%{text}%",
        textfont=dict(size=11, color=TEXT),
        showscale=True,
    ))
    base_layout(fig_heat, "Leakage Heatmap — Drop-off % by Stage & Segment")

    # ── Recommendations panel ──
    if not recs:
        recs_panel = html.P(
            "No critical issues found.",
            style={"color": ACC}
        )
    else:
        cards = []
        for r in recs:
            cards.append(html.Div([
                html.Div([
                    html.Span(
                        r["priority"],
                        style={
                            "fontSize": "12px",
                            "fontWeight": "600",
                            "marginRight": "12px",
                            "color": DANGER if r["priority"] == "HIGH" else WARN
                        }
                    ),
                    html.Span(
                        r["stage"],
                        style={"fontSize": "13px", "fontWeight": "500", "color": TEXT}
                    ),
                    html.Span(
                        f" — {r['dropoff']} drop-off",
                        style={"fontSize": "12px", "color": MUTED}
                    ),
                ], style={"marginBottom": "8px"}),
                html.P(
                    r["finding"],
                    style={"fontSize": "13px", "color": MUTED, "marginBottom": "10px"}
                ),
                html.Ul([
                    html.Li(
                        fix,
                        style={"fontSize": "13px", "color": TEXT, "marginBottom": "5px"}
                    )
                    for fix in r["fixes"]
                ], style={"paddingLeft": "18px"}),
            ], style={
                "background": SURF2,
                "borderRadius": "10px",
                "padding": "16px 20px",
                "border": f"1px solid {BORDER}",
                "marginBottom": "12px",
            }))
        recs_panel = html.Div(cards)

    return (
        kpi_row,
        fig_funnel,
        fig_seg,
        fig_drop,
        fig_heat,
        recs_panel
    )



if __name__ == "__main__":
    app.run(debug=False, port=8050)