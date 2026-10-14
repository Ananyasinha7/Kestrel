import numpy as np


def _label(value):
    return str(value).replace("_", " ")


def _payment_up(r):
    if r["payment_mode"] == "cod":
        return "Cash on delivery orders are returned more often"
    return f"Payment by {_label(r['payment_mode'])} is linked to more returns"


def _history_up(r):
    if r["customer_prior_orders"] == 0:
        return "New customer with no order history to judge by"
    return f"Customer returned {r['customer_prior_returns']:.0f} of {r['customer_prior_orders']:.0f} earlier orders"


def _location_up(r):
    if r["pincode_missing"]:
        return "Delivery pincode is missing or invalid"
    return "Delivery area has higher return rates"


FACTORS = (
    ("payment", ("payment_mode",), _payment_up, lambda r: f"Payment by {_label(r['payment_mode'])} is linked to fewer returns"),
    (
        "channel",
        ("sales_channel",),
        lambda r: f"Orders from the {_label(r['sales_channel'])} channel are returned more often",
        lambda r: f"Orders from the {_label(r['sales_channel'])} channel are returned less often",
    ),
    ("history", ("customer_prior_orders", "customer_prior_returns", "prior_return_rate"), _history_up, lambda r: "Customer has a clean return history"),
    (
        "delivery",
        ("promised_delivery_days",),
        lambda r: "Long promised delivery time",
        lambda r: "Short promised delivery time",
    ),
    ("gift", ("is_gift",), lambda r: "Order is marked as a gift", lambda r: "Order is not a gift"),
    (
        "shield",
        ("is_shield",),
        lambda r: "Shield members return more often because returns are free for them",
        lambda r: "Not a Shield member",
    ),
    (
        "product",
        ("sku_family", "sku"),
        lambda r: f"{r['sku']} orders are returned more often than average",
        lambda r: f"{r['sku']} orders are returned less often than average",
    ),
    (
        "price",
        ("order_value_inr", "discount_pct", "qty"),
        lambda r: "Order value and discount point to higher risk",
        lambda r: "Order value and discount point to lower risk",
    ),
    ("location", ("pincode_region", "pincode_missing"), _location_up, lambda r: "Delivery area has low return rates"),
    (
        "note",
        ("note_kind",),
        lambda r: "Delivery note suggests a harder delivery",
        lambda r: "Delivery note is routine",
    ),
)


def reasons(scorer, X, prepared, limit=3, minimum=0.01):
    active = [(name, [c for c in cols if c in scorer.columns], up, down) for name, cols, up, down in FACTORS]
    active = [item for item in active if item[1]]
    base = scorer.predict_features(X)
    deltas = []
    for _, cols, _, _ in active:
        variant = X.copy()
        for column in cols:
            variant[column] = scorer.baseline[column]
        deltas.append(base - scorer.predict_features(variant))
    deltas = np.column_stack(deltas)
    results = []
    for i in range(len(X)):
        row = prepared.iloc[i]
        items = []
        for j in np.argsort(-np.abs(deltas[i]))[:limit]:
            delta = deltas[i, j]
            if abs(delta) < minimum:
                break
            name, _, up, down = active[j]
            text = up(row) if delta > 0 else down(row)
            items.append({"factor": name, "direction": "up" if delta > 0 else "down", "text": text})
        results.append(items)
    return results
