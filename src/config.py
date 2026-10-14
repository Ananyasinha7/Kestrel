import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("KESTREL_DATA", ROOT / "data"))
MODELS = ROOT / "models"
EVIDENCE = ROOT / "evidence"
PREDICTIONS_FILE = ROOT / "predictions.csv"

TRAIN_FILE = DATA / "train.csv"
TEST_FILE = DATA / "test_unlabelled.csv"
SAMPLE_FILE = DATA / "sample_submission.csv"
PRODUCTS_FILE = DATA / "products.csv"
CUSTOMERS_FILE = DATA / "customers.csv"

ID = "order_id"
LABEL = "returned"
DATE = "order_placed_at"

BANNED = ("last_service_event_type", "pickup_scheduled_at")
FLAGS = ("is_gift", "is_shield")
HISTORY = ("customer_prior_orders", "customer_prior_returns")
KNOWN_CATEGORICAL = ("sales_channel", "payment_mode")

VALUE_SCALE = 100
DEFAULT_PINCODE = "000000"

VALID_START = "2026-04-01"
VALID_END = "2026-07-01"
CALIBRATION_MONTHS = 3
SELECTION_TOLERANCE = 0.005
