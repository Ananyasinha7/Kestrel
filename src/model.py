import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

from . import config, features

CANDIDATES = {
    "logreg": ("logreg", features.NUMERIC, features.CATEGORICAL),
    "gbm": ("gbm", features.NUMERIC, features.CATEGORICAL),
    "gbm_note": ("gbm", features.NUMERIC, features.CATEGORICAL + features.NOTE),
}


def _logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p)).reshape(-1, 1)


def _pipeline(kind, numeric, categorical):
    if kind == "logreg":
        preprocess = ColumnTransformer(
            [
                ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), list(numeric)),
                ("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=30), list(categorical)),
            ]
        )
        classifier = LogisticRegression(C=0.5, max_iter=1000)
    else:
        preprocess = ColumnTransformer(
            [
                ("num", "passthrough", list(numeric)),
                (
                    "cat",
                    OrdinalEncoder(
                        handle_unknown="use_encoded_value",
                        unknown_value=np.nan,
                        encoded_missing_value=np.nan,
                        min_frequency=30,
                        max_categories=200,
                    ),
                    list(categorical),
                ),
            ]
        )
        mask = [False] * len(numeric) + [True] * len(categorical)
        classifier = HistGradientBoostingClassifier(
            categorical_features=mask,
            learning_rate=0.05,
            max_iter=250,
            max_depth=4,
            l2_regularization=1.0,
            random_state=0,
        )
    return Pipeline([("pre", preprocess), ("clf", classifier)])


class Scorer:
    def __init__(self, kind, numeric, categorical, name=None):
        features.assert_allowed(tuple(numeric) + tuple(categorical))
        self.kind = kind
        self.name = name or kind
        self.numeric = tuple(numeric)
        self.categorical = tuple(categorical)

    @property
    def columns(self):
        return list(self.numeric + self.categorical)

    def fit(self, prepared):
        dates = prepared[config.DATE]
        cutoff = dates.max() - pd.DateOffset(months=config.CALIBRATION_MONTHS)
        early = (dates <= cutoff).to_numpy()
        X = features.build(prepared, self.numeric, self.categorical)
        y = prepared[config.LABEL].to_numpy()
        early_model = _pipeline(self.kind, self.numeric, self.categorical).fit(X[early], y[early])
        raw = early_model.predict_proba(X[~early])[:, 1]
        self.calibrator = LogisticRegression(C=1e6).fit(_logit(raw), y[~early])
        self.pipeline = _pipeline(self.kind, self.numeric, self.categorical).fit(X, y)
        self.baseline = {c: X[c].median() for c in self.numeric}
        for c in self.categorical:
            mode = X[c].mode()
            self.baseline[c] = mode.iat[0] if len(mode) else np.nan
        self.trained_through = dates.max()
        return self

    def predict_features(self, X):
        raw = self.pipeline.predict_proba(X[self.columns])[:, 1]
        return self.calibrator.predict_proba(_logit(raw))[:, 1]

    def predict(self, prepared):
        return self.predict_features(features.build(prepared, self.numeric, self.categorical))


def candidate(name):
    kind, numeric, categorical = CANDIDATES[name]
    return Scorer(kind, numeric, categorical, name)
