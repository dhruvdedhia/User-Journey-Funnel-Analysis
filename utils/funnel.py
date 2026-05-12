
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "funnel.db"

STAGES      = ["visit", "signup", "add_to_cart", "purchase"]
STAGE_NAMES = ["Visit", "Sign Up", "Add to Cart", "Purchase"]
STAGE_ORDER = {s: i for i, s in enumerate(STAGES)}

def _q(sql):
    conn = sqlite3.connect(DB_PATH)
    df   = pd.read_sql_query(sql, conn)
    conn.close()
    return df

def overall_funnel():
    df = _q("""
        SELECT event, COUNT(DISTINCT user_id) AS users
        FROM events GROUP BY event
    """)

    df["stage_order"] = df["event"].map(STAGE_ORDER)
    df = df.sort_values("stage_order").reset_index(drop=True)
    df["stage_name"]  = df["event"].map(
        dict(zip(STAGES, STAGE_NAMES))
    )

    total = df.loc[df["event"] == "visit", "users"].values[0]

    df["pct_of_total"]   = (df["users"] / total * 100).round(1)
    df["dropoff_pct"]    = (
        1 - df["users"] / df["users"].shift(1)
    ).mul(100).round(1)
    df["conversion_pct"] = (
        df["users"] / df["users"].shift(1) * 100
    ).round(1)

    df.loc[0, ["dropoff_pct", "conversion_pct"]] = [0.0, 100.0]
    return df

def segmented_funnel(segment):
    assert segment in ("device", "traffic_source", "location")

    df = _q(f"""
        SELECT {segment} AS seg, event,
               COUNT(DISTINCT user_id) AS users
        FROM events
        GROUP BY {segment}, event
    """)

    df["stage_order"] = df["event"].map(STAGE_ORDER)
    df = df.sort_values(["seg", "stage_order"])

    visits    = df[df["event"] == "visit"   ].set_index("seg")["users"]
    purchases = df[df["event"] == "purchase"].set_index("seg")["users"]
    conv      = (purchases / visits * 100).round(1).rename("overall_conv_pct")

    pivot = df.pivot_table(
        index="seg", columns="event",
        values="users", fill_value=0
    ).reset_index()
    pivot.columns.name = None

    for s in STAGES:
        if s not in pivot.columns:
            pivot[s] = 0

    pivot = pivot[["seg"] + STAGES]
    pivot = pivot.merge(
        conv.reset_index(), on="seg", how="left"
    )

    for i in range(1, len(STAGES)):
        prev, curr = STAGES[i-1], STAGES[i]
        col = f"drop_{prev}_to_{curr}"
        pivot[col] = (
            (1 - pivot[curr] / pivot[prev].replace(0, np.nan)) * 100
        ).round(1)

    return pivot.sort_values(
        "overall_conv_pct", ascending=False
    ).reset_index(drop=True)

def significance_test(segment, stage_from="add_to_cart", stage_to="purchase"):
    df = _q(f"""
        SELECT {segment} AS seg, event,
               COUNT(DISTINCT user_id) AS users
        FROM events
        WHERE event IN ('{stage_from}', '{stage_to}')
        GROUP BY {segment}, event
    """)

    pivot = df.pivot_table(
        index="seg", columns="event",
        values="users", fill_value=0
    ).reset_index()
    pivot.columns.name = None

    total_from = pivot[stage_from].sum()
    total_to   = pivot[stage_to].sum()
    baseline   = total_to / total_from

    results = []
    for _, row in pivot.iterrows():
        if row[stage_from] < 30:
            continue

        expected_conv     = row[stage_from] * baseline
        expected_not_conv = row[stage_from] - expected_conv
        observed = [row[stage_to],
                    row[stage_from] - row[stage_to]]
        expected = [expected_conv, expected_not_conv]

        chi2, p = stats.chisquare(observed, expected)

        results.append({
            "segment":     row["seg"],
            "users":       int(row[stage_from]),
            "conv_rate":   round(row[stage_to] / row[stage_from] * 100, 1),
            "baseline":    round(baseline * 100, 1),
            "p_value":     round(p, 4),
            "significant": "YES" if p < 0.05 else "no",
            "vs_baseline": round(
                row[stage_to] / row[stage_from] * 100 - baseline * 100, 1
            ),
        })

    return pd.DataFrame(results).sort_values(
        "conv_rate", ascending=False
    ).reset_index(drop=True)

def kpi_snapshot():
    overall = overall_funnel()

    visits    = overall.loc[overall["event"] == "visit",
                            "users"].values[0]
    purchases = overall.loc[overall["event"] == "purchase",
                            "users"].values[0]

    revenue = _q("""
        SELECT SUM(order_value) as r
        FROM events WHERE event='purchase'
    """)["r"].values[0]

    return {
        "total_visitors":      int(visits),
        "total_purchases":     int(purchases),
        "overall_conv_pct":    round(purchases / visits * 100, 2),
        "total_revenue":       round(revenue, 0),
        "avg_order_value":     round(revenue / purchases, 0),
        "revenue_per_visitor": round(revenue / visits, 2),
    }

def fix_recommendations():
    overall    = overall_funnel()
    device_df  = segmented_funnel("device")
    traffic_df = segmented_funnel("traffic_source")
    recs       = []

    dropoffs = {
        row["event"]: row["dropoff_pct"]
        for _, row in overall.iterrows()
        if pd.notna(row["dropoff_pct"])
    }

    # Visit → Signup
    d_v2s = dropoffs.get("signup", 0)
    if d_v2s > 60:
        recs.append({
            "priority": "HIGH",
            "stage":    "Visit → Sign Up",
            "dropoff":  f"{d_v2s:.1f}%",
            "finding":  f"{d_v2s:.1f}% of visitors leave without signing up.",
            "fixes": [
                "Replace full registration with Sign up with Google",
                "Add social proof above the fold",
                "A/B test CTA — Get started free vs Create account",
                "Add exit-intent popup for abandoning visitors",
            ]
        })

    # Cart → Purchase
    d_c2p = dropoffs.get("purchase", 0)
    if d_c2p > 50:
        recs.append({
            "priority": "HIGH",
            "stage":    "Cart → Purchase",
            "dropoff":  f"{d_c2p:.1f}%",
            "finding":  f"{d_c2p:.1f}% of users abandon at checkout.",
            "fixes": [
                "Reduce checkout to a single page",
                "Add trust signals — security badges, return policy",
                "Offer UPI, EMI, COD payment options",
                "Send cart abandonment email within 30 minutes",
            ]
        })

    # Mobile gap
    mob  = device_df[
        device_df["seg"] == "mobile"
    ]["overall_conv_pct"].values[0]
    desk = device_df[
        device_df["seg"] == "desktop"
    ]["overall_conv_pct"].values[0]
    gap  = round(desk - mob, 1)
    if gap > 2:
        recs.append({
            "priority": "HIGH",
            "stage":    "Mobile Experience",
            "dropoff":  f"{gap}% gap vs desktop",
            "finding":  f"Mobile converts {mob}% vs desktop {desk}% on your largest traffic source.",
            "fixes": [
                "Audit mobile checkout on real devices",
                "Implement UPI intent for one-tap mobile payment",
                "Compress images — mobile users are speed sensitive",
                "Ensure tap targets are minimum 44x44px",
            ]
        })

    # Paid ads vs email
    paid  = traffic_df[
        traffic_df["seg"] == "paid_ads"
    ]["overall_conv_pct"].values[0]
    email = traffic_df[
        traffic_df["seg"] == "email"
    ]["overall_conv_pct"].values[0]
    if paid < email * 0.7:
        recs.append({
            "priority": "MEDIUM",
            "stage":    "Paid Ads ROI",
            "dropoff":  f"Paid {paid}% vs Email {email}%",
            "finding":  f"Paid ads convert at {paid}% vs email {email}% — budget misallocated.",
            "fixes": [
                "Match ad landing pages to ad creative",
                "Build dedicated post-click landing pages",
                "Add retargeting for visitors who did not sign up",
                "Invest more in email — highest ROI channel",
            ]
        })

    return recs

def leakage_heatmap(segment):
    sf        = segmented_funnel(segment)
    drop_cols = [c for c in sf.columns if c.startswith("drop_")]
    heatmap   = sf[["seg"] + drop_cols].copy()
    heatmap.columns = (
        ["Segment"] + [
            c.replace("drop_", "")
             .replace("_to_", " → ")
             .replace("_", " ")
             .title()
            for c in drop_cols
        ]
    )
    return heatmap


def daily_trend():
    df = _q("""
        SELECT date, event, COUNT(DISTINCT user_id) AS users
        FROM events GROUP BY date, event ORDER BY date
    """)
    return df


def revenue_by_segment(segment):
    df = _q(f"""
        SELECT {segment} AS seg,
               COUNT(DISTINCT user_id) AS purchasers,
               SUM(order_value)         AS total_revenue,
               AVG(order_value)         AS avg_order_value
        FROM events WHERE event='purchase'
        GROUP BY {segment}
        ORDER BY total_revenue DESC
    """)
    return df


def hourly_conversion():
    df = _q("""
        SELECT hour, event, COUNT(DISTINCT user_id) AS users
        FROM events GROUP BY hour, event ORDER BY hour
    """)
    visits    = df[df["event"] == "visit"   ].set_index("hour")["users"]
    purchases = df[df["event"] == "purchase"].set_index("hour")["users"]
    hourly    = pd.DataFrame({
        "visits":    visits,
        "purchases": purchases
    }).fillna(0)
    hourly["conv_rate"] = (
        hourly["purchases"] / hourly["visits"] * 100
    ).round(1)
    return hourly.reset_index()

if __name__ == "__main__":
    print("\n── OVERALL FUNNEL ──")
    df = overall_funnel()
    print(df[["stage_name", "users", "pct_of_total", "dropoff_pct"]])

    print("\n── BY DEVICE ──")
    dev = segmented_funnel("device")
    print(dev[["seg", "visit", "purchase", "overall_conv_pct"]])

    print("\n── BY TRAFFIC ──")
    trf = segmented_funnel("traffic_source")
    print(trf[["seg", "visit", "purchase", "overall_conv_pct"]])

    print("\n── KPI SNAPSHOT ──")
    kpis = kpi_snapshot()
    for k, v in kpis.items():
        print(f"  {k}: {v}")

    print("\n── SIGNIFICANCE TEST — DEVICE ──")
    sig = significance_test("device")
    print(sig)

    print("\n── RECOMMENDATIONS ──")
    recs = fix_recommendations()
    for r in recs:
        print(f"\n{r['priority']} | {r['stage']} | {r['dropoff']}")
        print(f"Finding: {r['finding']}")
        for fix in r["fixes"]:
            print(f"  • {fix}")

