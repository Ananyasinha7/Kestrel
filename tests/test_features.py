import numpy as np
import pytest

from src import config, data, evaluate, features, model


def test_dedupe_keeps_one_row_per_order(raw_orders):
    deduped = features.dedupe(raw_orders)
    assert deduped[config.ID].is_unique
    assert len(deduped) < len(raw_orders)


def test_october_values_are_repaired(prepared, prices):
    october = prepared[(prepared[config.DATE].dt.year == 2025) & (prepared[config.DATE].dt.month == 10)]
    assert october["value_corrected"].all()
    expected = october["sku"].map(prices).astype(float) * (1 - october["discount_pct"] / 100) * october["qty"]
    assert np.allclose(october["order_value_inr"], expected)
    assert not prepared.drop(october.index)["value_corrected"].any()


def test_default_pincode_becomes_missing(prepared):
    flagged = prepared[prepared["delivery_pincode"] == config.DEFAULT_PINCODE]
    assert len(flagged) > 0
    assert (flagged["pincode_missing"] == 1).all()
    assert flagged["pincode_region"].isna().all()


def test_banned_columns_are_rejected():
    with pytest.raises(ValueError):
        features.assert_allowed(("net_value", "last_service_event_type"))


@pytest.mark.parametrize("name", list(model.CANDIDATES))
def test_candidates_use_no_banned_columns(name):
    assert not set(model.candidate(name).columns) & set(config.BANNED)


def test_leaky_model_beats_honest_model(prepared):
    fit, valid = data.split_forward(prepared)
    leaky_auc, honest_auc = evaluate.leakage(fit, valid)
    assert leaky_auc > honest_auc + 0.1
    assert 0.5 < honest_auc < 0.95


def test_scores_are_probabilities(engine, prepared):
    scores = engine.scorer.predict(prepared.head(200))
    assert scores.min() >= 0 and scores.max() <= 1
    assert not np.isnan(scores).any()
