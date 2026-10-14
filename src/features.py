import numpy as np
import pandas as pd

from . import config

NUMERIC = (
    "discount_pct",
    "qty",
    "order_value_inr",
    "promised_delivery_days",
    "customer_prior_orders",
    "customer_prior_returns",
    "prior_return_rate",
    "is_gift",
    "is_shield",
    "pincode_missing",
)
CATEGORICAL = ("sku_family", "sku", "sales_channel", "payment_mode", "pincode_region")
NOTE = ("note_kind",)

RAW_NUMERIC = (
    "discount_pct",
    "qty",
    "order_value_inr",
    "promised_delivery_days",
    "customer_prior_orders",
    "customer_prior_returns",
)
RAW_TEXT = ("sku", "sales_channel", "payment_mode", "delivery_pincode", "delivery_note")


def assert_allowed(columns):
    leaked = sorted(set(columns) & set(config.BANNED))
    if leaked:
        raise ValueError(f"Banned columns used as features: {', '.join(leaked)}")


def dedupe(df):
    return df.drop_duplicates(config.ID, keep="first").reset_index(drop=True)


def _column(df, name, default=np.nan):
    return df[name] if name in df else pd.Series(default, index=df.index)


def _flag(series):
    text = series.astype(str).str.strip().str.lower()
    return text.isin({"1", "1.0", "true", "yes", "y"}).astype(int)


def prepare(df, prices):
    out = df.copy()
    for name in RAW_NUMERIC:
        out[name] = pd.to_numeric(_column(out, name), errors="coerce")
    for name in config.FLAGS:
        out[name] = _flag(_column(out, name, 0))
    for name in RAW_TEXT:
        out[name] = _column(out, name, pd.NA).astype("string").str.strip()
    out[config.DATE] = pd.to_datetime(_column(out, config.DATE), errors="coerce")
    out["customer_prior_orders"] = out["customer_prior_orders"].fillna(0)
    out["customer_prior_returns"] = out["customer_prior_returns"].fillna(0)
    out["discount_pct"] = out["discount_pct"].fillna(0)
    out["qty"] = out["qty"].fillna(1)

    unit = out["sku"].map(prices).astype(float)
    expected = unit * (1 - out["discount_pct"] / 100) * out["qty"]
    scaled = (out["order_value_inr"] / expected / config.VALUE_SCALE - 1).abs() < 0.01
    value = out["order_value_inr"].where(~scaled, out["order_value_inr"] / config.VALUE_SCALE)
    out["order_value_inr"] = value.fillna(expected)
    out["value_corrected"] = scaled.fillna(False).astype(bool)

    pin = out["delivery_pincode"].str.replace(r"\.0$", "", regex=True)
    valid = (pin.str.fullmatch(r"\d{6}") & (pin != config.DEFAULT_PINCODE)).fillna(False).astype(bool)
    out["pincode_missing"] = (~valid).astype(int)
    out["pincode_region"] = pin.str[:3].where(valid)

    out["sku_family"] = out["sku"].str.split("-").str[1]
    out["note_kind"] = (
        out["delivery_note"].str.replace(r"\d+", "#", regex=True).str.split(". ", n=1, regex=False).str[0]
    )
    out["prior_return_rate"] = out["customer_prior_returns"] / out["customer_prior_orders"].replace(0, np.nan)
    return out


def build(prepared, numeric, categorical):
    X = prepared[list(numeric)].astype(float)
    for name in categorical:
        column = prepared[name]
        X[name] = column.astype(object).where(column.notna(), np.nan)
    return X
