import json

import joblib
import pandas as pd
import sklearn

from . import config, economics, explain, features


class Engine:
    def __init__(self, scorer, meta):
        self.scorer = scorer
        self.meta = meta
        self.version = meta["version"]
        self.prices = meta["list_prices"]

    @classmethod
    def load(cls, directory=config.MODELS):
        meta = json.loads((directory / "meta.json").read_text())
        built = meta.get("versions", {})
        installed = {"scikit-learn": sklearn.__version__, "pandas": pd.__version__}
        mismatched = {k: (built[k], installed[k]) for k in built if built[k] != installed[k]}
        if mismatched:
            detail = ", ".join(f"{k} {b} needed, {i} installed" for k, (b, i) in mismatched.items())
            raise RuntimeError(f"Model files need different library versions ({detail}). Run: pip install -r requirements.txt")
        return cls(joblib.load(directory / "model.joblib"), meta)

    def warnings(self, row, record):
        out = []
        ignored = [c for c in config.BANNED if record.get(c) not in (None, "")]
        if ignored:
            out.append(f"Ignored fields that are not known at dispatch: {', '.join(ignored)}")
        if row["pincode_missing"]:
            out.append("Pincode is missing or invalid, so location was not used")
        if row["value_corrected"]:
            out.append("Order value looked 100 times too large and was corrected")
        if any(record.get(c) is None for c in config.HISTORY):
            out.append("Customer history not supplied, so the customer is treated as new")
        if record.get("is_shield") is None:
            out.append("Shield status not supplied, so the customer is treated as a non-member")
        if not pd.isna(row["sku"]) and row["sku"] not in self.prices:
            out.append("Unknown SKU, so the score is less reliable")
        for key in config.KNOWN_CATEGORICAL:
            value = row[key]
            if not pd.isna(value) and value not in self.meta["categories"][key]:
                out.append(f"Unseen {key.replace('_', ' ')} '{value}', so the score is less reliable")
        return out

    def score(self, records):
        prepared = features.prepare(pd.DataFrame(records), self.prices)
        X = features.build(prepared, self.scorer.numeric, self.scorer.categorical)
        scores = self.scorer.predict_features(X)
        why = explain.reasons(self.scorer, X, prepared)
        results = []
        for i, record in enumerate(records):
            row = prepared.iloc[i]
            tier = economics.tier(scores[i])
            results.append(
                {
                    "order_id": record.get(config.ID),
                    "score": round(float(scores[i]), 4),
                    "risk_tier": tier,
                    "action": economics.action(tier, bool(row["is_shield"])),
                    "reasons": why[i],
                    "data_warnings": self.warnings(row, record),
                    "model_version": self.version,
                }
            )
        return results
