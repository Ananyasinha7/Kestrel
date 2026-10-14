import pytest
from fastapi.testclient import TestClient

from app.main import app, get_engine

ORDER = {
    "order_id": "T-1",
    "customer_id": "KC100001",
    "sku": "KH-RV-03",
    "sales_channel": "marketplace",
    "payment_mode": "cod",
    "discount_pct": 10,
    "qty": 1,
    "promised_delivery_days": 9,
    "delivery_pincode": "440365",
    "customer_prior_orders": 4,
    "customer_prior_returns": 2,
    "is_shield": False,
}


@pytest.fixture
def client(engine):
    app.dependency_overrides[get_engine] = lambda: engine
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health(client, engine):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["model_version"] == engine.version


def test_valid_order_is_scored(client):
    response = client.post("/score", json=ORDER)
    body = response.json()
    assert response.status_code == 200
    assert 0 <= body["score"] <= 1
    assert body["risk_tier"] in {"CALL", "WATCH", "OK"}
    assert body["order_id"] == "T-1"
    assert all(set(r) == {"factor", "direction", "text"} for r in body["reasons"])


def test_invalid_order_returns_422(client):
    response = client.post("/score", json={**ORDER, "discount_pct": -5})
    body = response.json()
    assert response.status_code == 422
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["details"][0]["field"] == "discount_pct"


def test_missing_field_returns_422(client):
    payload = {k: v for k, v in ORDER.items() if k != "sku"}
    assert client.post("/score", json=payload).status_code == 422


def test_malformed_json_returns_422(client):
    response = client.post("/score", content="{not json", headers={"Content-Type": "application/json"})
    assert response.status_code == 422


def test_unknown_sku_warns(client):
    response = client.post("/score", json={**ORDER, "sku": "NOPE"})
    assert response.status_code == 200
    assert any("SKU" in w for w in response.json()["data_warnings"])


def test_missing_customer_history_warns(client):
    payload = {k: v for k, v in ORDER.items() if not k.startswith("customer_prior")}
    response = client.post("/score", json=payload)
    assert response.status_code == 200
    assert any("history" in w for w in response.json()["data_warnings"])


def test_known_sku_history_and_shield_give_no_warnings(client):
    assert client.post("/score", json=ORDER).json()["data_warnings"] == []


def test_missing_shield_status_warns(client):
    payload = {k: v for k, v in ORDER.items() if k != "is_shield"}
    assert any("Shield" in w for w in client.post("/score", json=payload).json()["data_warnings"])


def test_service_fields_are_ignored_with_warning(client):
    plain = client.post("/score", json=ORDER).json()
    leaky = client.post("/score", json={**ORDER, "last_service_event_type": "REVERSE_PICKUP"}).json()
    assert leaky["score"] == plain["score"]
    assert any("Ignored" in w for w in leaky["data_warnings"])


def test_shield_order_is_never_held(client):
    body = client.post("/score", json={**ORDER, "is_shield": True}).json()
    assert "hold" not in body["action"].lower() or "never hold" in body["action"].lower()


def test_library_version_mismatch_is_reported(prepared, tmp_path):
    import json

    from src import train
    from src.engine import Engine
    from tests.synthetic import LIST_PRICE

    train.fit_final(prepared, "logreg", {}, LIST_PRICE, tmp_path)
    meta = json.loads((tmp_path / "meta.json").read_text())
    meta["versions"]["scikit-learn"] = "0.0.1"
    (tmp_path / "meta.json").write_text(json.dumps(meta))
    with pytest.raises(RuntimeError, match="pip install -r requirements.txt"):
        Engine.load(tmp_path)


def test_screen_is_served(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Return risk" in response.text
