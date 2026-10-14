# Kestrel Home return risk

Scores every pre-dispatch order for return risk, with plain-language reasons. Recommendation: call high-risk customers, do not hold orders. Shield members get a courtesy call, never a hold.

## Run

Python 3.11 or newer. Use a fresh virtual environment, because the saved model only loads with the exact library versions in requirements.txt.

    python -m venv .venv
    . .venv/bin/activate          (Windows PowerShell: .venv\Scripts\Activate.ps1)
    pip install -r requirements-dev.txt
    uvicorn app.main:app

To rebuild from the raw data in data/ first:

    python -m src.evaluate
    python -m src.train
    python -m src.predict

Open http://localhost:8000. No API keys are needed and nothing is called per order.

## Score an order

    curl -X POST localhost:8000/score -H 'Content-Type: application/json' -d '{
      "order_id": "A1", "customer_id": "KC104433", "sku": "KH-RV-03",
      "sales_channel": "marketplace", "payment_mode": "cod", "discount_pct": 10,
      "qty": 1, "promised_delivery_days": 9, "delivery_pincode": "440365",
      "customer_prior_orders": 4, "customer_prior_returns": 2
    }'

Response: order_id, score, risk_tier, action, reasons, data_warnings, model_version. Invalid input returns 422 with error.code, error.message and error.details. An unknown SKU, or missing customer history, returns a score with a warning. Customer ids are not stored in the model artifacts.

## Layout

    src/config.py      paths, column names, banned columns, split dates
    src/reference.py   products and customers lookups
    src/features.py    cleaning, repairs, feature build, banned-column guard
    src/model.py       candidate models and calibrated Scorer
    src/economics.py   rupee model, thresholds, tiers, actions
    src/explain.py     plain-English reasons from per-factor contributions
    src/evaluate.py    forward-split metrics, leakage demo, rupee tables, evidence
    src/train.py       model selection and final fit
    src/predict.py     writes predictions.csv
    src/engine.py      scoring used by the API
    app/               FastAPI service and single-page screen
    tests/             feature and API tests

Raw data lives in data/ and is git-ignored. Keep the repository private.

## Data

Place these in data/ (git-ignored, do not publish): train.csv, test_unlabelled.csv, customers.csv, products.csv, sample_submission.csv. Tests do not need them.

Shield membership comes from customers.csv. The service takes it as an optional is_shield field on the request, since the dispatch snapshot does not carry it. Without it the order is scored as a non-member, with a warning. Customer ids are not stored in the model files.

## Documents

MEMO.md, AI_USAGE.md, SUBMISSION.md, RECORDING.md, evidence/, tasks/.
