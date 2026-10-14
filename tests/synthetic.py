import numpy as np
import pandas as pd

FAMILIES = ["AF", "CF", "IC", "MG", "RH", "RV", "WP"]
SKUS = [f"KH-{f}-0{v}" for f in FAMILIES for v in (1, 2, 3)]
LIST_PRICE = {sku: 2000.0 + 150.0 * i for i, sku in enumerate(SKUS)}


def make_orders(n=4000, seed=0):
    rng = np.random.default_rng(seed)
    placed = pd.Timestamp("2025-04-01") + pd.to_timedelta(rng.integers(0, 457 * 1440, n), unit="m")
    sku = rng.choice(SKUS, n)
    payment = rng.choice(["cod", "emi", "prepaid_card", "prepaid_upi"], n, p=[0.3, 0.12, 0.2, 0.38])
    channel = rng.choice(["app", "marketplace", "partner_outlet", "web"], n)
    prior_orders = rng.integers(0, 6, n)
    prior_returns = np.minimum(prior_orders, rng.binomial(prior_orders, 0.25))
    promised = rng.integers(1, 12, n)
    gift = rng.random(n) < 0.07
    shield = rng.random(n) < 0.22
    discount = rng.integers(0, 30, n)
    qty = rng.choice([1, 2], n, p=[0.94, 0.06])
    rate = prior_returns / np.maximum(prior_orders, 1)
    logit = (
        -3.4
        + 0.9 * (payment == "cod")
        + 2.0 * rate
        + 0.12 * promised
        + 0.5 * gift
        + 0.3 * (channel == "marketplace")
        + 0.8 * shield
        + 0.5 * np.char.startswith(sku.astype(str), "KH-RV")
    )
    returned = rng.random(n) < 1 / (1 + np.exp(-logit))
    event = np.where(
        returned,
        rng.choice(["REVERSE_PICKUP", "TECH_VISIT"], n),
        rng.choice(["INSTALL_DONE", "DEMO_DONE", "NONE"], n),
    )
    pickup = np.where(returned & (rng.random(n) < 0.9), "2026-07-01 10:00", None)
    pincode = np.where(rng.random(n) < 0.08, "000000", rng.choice(["440365", "110891", "400151", "560034"], n))
    value = np.round(np.array([LIST_PRICE[s] for s in sku]) * (1 - discount / 100) * qty, 2)
    value = np.where((placed.year == 2025) & (placed.month == 10), value * 100, value)
    df = pd.DataFrame(
        {
            "order_id": [f"KO{i:07d}" for i in range(n)],
            "order_placed_at": placed.strftime("%Y-%m-%d %H:%M"),
            "customer_id": [f"KC{i:06d}" for i in rng.integers(100000, 101500, n)],
            "sku": sku,
            "sales_channel": channel,
            "payment_mode": payment,
            "discount_pct": discount,
            "qty": qty,
            "order_value_inr": value,
            "promised_delivery_days": promised,
            "delivery_pincode": pincode,
            "is_gift": np.where(gift, "Y", "N"),
            "is_shield": np.where(shield, "Y", "N"),
            "customer_prior_orders": prior_orders,
            "customer_prior_returns": prior_returns,
            "delivery_note": rng.choice(["Gate code 4421, call before delivery", "Ring twice", "Leave with security", None], n),
            "last_service_event_type": event,
            "pickup_scheduled_at": pickup,
            "source": "crm",
            "returned": returned.astype(int),
        }
    )
    dup = df.sample(frac=0.05, random_state=seed).assign(source="partner_feed")
    return pd.concat([df, dup], ignore_index=True)
