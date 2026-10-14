import pytest

from src import features, train
from src.engine import Engine
from tests.synthetic import LIST_PRICE, make_orders


@pytest.fixture(scope="session")
def raw_orders():
    return make_orders()


@pytest.fixture(scope="session")
def prices():
    return LIST_PRICE


@pytest.fixture(scope="session")
def prepared(raw_orders, prices):
    return features.prepare(features.dedupe(raw_orders), prices)


@pytest.fixture(scope="session")
def engine(prepared, tmp_path_factory):
    directory = tmp_path_factory.mktemp("models")
    train.fit_final(prepared, "gbm", {}, LIST_PRICE, directory)
    return Engine.load(directory)
