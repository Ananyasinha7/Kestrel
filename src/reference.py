import pandas as pd

from . import config


def list_prices():
    products = pd.read_csv(config.PRODUCTS_FILE)
    return dict(zip(products["sku"], products["list_price_inr"].astype(float)))


def attach_shield(df):
    customers = pd.read_csv(config.CUSTOMERS_FILE, dtype={"customer_id": "string"})
    shield = customers.set_index("customer_id")["shield_member"]
    out = df.copy()
    out["is_shield"] = out["customer_id"].astype("string").map(shield).fillna("N")
    return out
