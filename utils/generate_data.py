import pandas as pd
import numpy as np
import sqlite3
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "funnel.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

DEVICES = {
    "mobile":  dict(weight=0.55, v2s=0.28, s2c=0.42, c2p=0.31),
    "desktop": dict(weight=0.32, v2s=0.41, s2c=0.58, c2p=0.52),
    "tablet":  dict(weight=0.13, v2s=0.33, s2c=0.48, c2p=0.38),
}

TRAFFIC = {
    "organic_search": dict(weight=0.35, v2s=0.38, s2c=0.52, c2p=0.48),
    "paid_ads":       dict(weight=0.25, v2s=0.22, s2c=0.38, c2p=0.35),
    "social_media":   dict(weight=0.20, v2s=0.19, s2c=0.31, c2p=0.27),
    "email":          dict(weight=0.12, v2s=0.51, s2c=0.62, c2p=0.58),
    "direct":         dict(weight=0.08, v2s=0.45, s2c=0.60, c2p=0.55),
}

LOCATIONS = {
    "Mumbai":    dict(weight=0.22, v2s=0.37, s2c=0.51, c2p=0.46),
    "Delhi":     dict(weight=0.18, v2s=0.34, s2c=0.48, c2p=0.43),
    "Bengaluru": dict(weight=0.15, v2s=0.42, s2c=0.56, c2p=0.51),
    "Hyderabad": dict(weight=0.10, v2s=0.31, s2c=0.44, c2p=0.39),
    "Chennai":   dict(weight=0.09, v2s=0.29, s2c=0.41, c2p=0.36),
    "Pune":      dict(weight=0.08, v2s=0.38, s2c=0.50, c2p=0.45),
    "Kolkata":   dict(weight=0.07, v2s=0.27, s2c=0.39, c2p=0.33),
    "Other":     dict(weight=0.11, v2s=0.24, s2c=0.35, c2p=0.29),
}

def _blend(base_p, modifier, weight=0.5):
    return min(0.95, max(0.01, base_p * weight + modifier * (1 - weight)))

def generate_events(n_users=15000, days=90):
    start_date = datetime.today() - timedelta(days=days)
    rows = []

    dev_keys    = list(DEVICES.keys())
    dev_weights = [DEVICES[d]["weight"] for d in dev_keys]
    trf_keys    = list(TRAFFIC.keys())
    trf_weights = [TRAFFIC[t]["weight"] for t in trf_keys]
    loc_keys    = list(LOCATIONS.keys())
    loc_weights = [LOCATIONS[l]["weight"] for l in loc_keys]

    for user_id in range(1, n_users + 1):
        device   = random.choices(dev_keys, dev_weights)[0]
        traffic  = random.choices(trf_keys, trf_weights)[0]
        location = random.choices(loc_keys, loc_weights)[0]

        dv = DEVICES[device]
        tv = TRAFFIC[traffic]
        lv = LOCATIONS[location]

        p_v2s = _blend(dv["v2s"], _blend(tv["v2s"], lv["v2s"]))
        p_s2c = _blend(dv["s2c"], _blend(tv["s2c"], lv["s2c"]))
        p_c2p = _blend(dv["c2p"], _blend(tv["c2p"], lv["c2p"]))


        session_start = start_date + timedelta(
            days=random.randint(0, days - 1),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )

        ts = session_start
        rows.append(dict(
            user_id=user_id, event="visit",
            timestamp=ts.isoformat(),
            device=device, traffic_source=traffic, location=location,
            session_duration_s=random.randint(5, 300),
        ))

        if random.random() > p_v2s:
            continue

        ts += timedelta(seconds=random.randint(15, 180))
        rows.append(dict(
            user_id=user_id, event="signup",
            timestamp=ts.isoformat(),
            device=device, traffic_source=traffic, location=location,
            session_duration_s=random.randint(30, 600),
        ))

        if random.random() > p_s2c:
            continue

        ts += timedelta(seconds=random.randint(30, 300))
        rows.append(dict(
            user_id=user_id, event="add_to_cart",
            timestamp=ts.isoformat(),
            device=device, traffic_source=traffic, location=location,
            session_duration_s=random.randint(60, 900),
        ))

        if random.random() > p_c2p:
            continue

        ts += timedelta(seconds=random.randint(30, 600))
        order_value = round(np.random.lognormal(mean=7.5, sigma=0.8), 2)
        rows.append(dict(
            user_id=user_id, event="purchase",
            timestamp=ts.isoformat(),
            device=device, traffic_source=traffic, location=location,
            session_duration_s=random.randint(120, 1200),
            order_value=order_value,
        ))

        df = pd.DataFrame(rows)
    df["timestamp"]   = pd.to_datetime(df["timestamp"])
    df["date"]        = df["timestamp"].dt.date.astype(str)
    df["hour"]        = df["timestamp"].dt.hour
    df["order_value"] = df["order_value"].fillna(0)

    print(f"[data] Generated {len(df):,} events for {n_users:,} users over {days} days.")
    return df

def save_to_db(df):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS events")
    df.to_sql("events", conn, index=False)
    conn.commit()
    conn.close()
    print(f"[db] Saved to {DB_PATH}")

if __name__ == "__main__":
    df=generate_events(n_users=15000, days=90)
    save_to_db(df)
    