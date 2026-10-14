import pandas as pd

from . import config, features, reference

TEXT = {config.ID: "string", "delivery_pincode": "string", "sku": "string", "customer_id": "string"}


def _read(path):
    return pd.read_csv(path, dtype=TEXT)


def load_train():
    raw = reference.attach_shield(features.dedupe(_read(config.TRAIN_FILE)))
    df = features.prepare(raw, reference.list_prices())
    df[config.LABEL] = pd.to_numeric(df[config.LABEL]).astype(int)
    return df


def load_test(prices):
    return features.prepare(reference.attach_shield(_read(config.TEST_FILE)), prices)


def split_forward(df):
    date = df[config.DATE]
    fit = df[date < config.VALID_START].reset_index(drop=True)
    valid = df[(date >= config.VALID_START) & (date < config.VALID_END)].reset_index(drop=True)
    return fit, valid
