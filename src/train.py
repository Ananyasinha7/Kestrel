import json

import joblib
import pandas as pd
import sklearn

from . import config, data, economics, evaluate, model, reference


def fit_final(df, name, validation, prices, out_dir=config.MODELS):
    scorer = model.candidate(name).fit(df)
    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(scorer, out_dir / "model.joblib")
    meta = {
        "model": name,
        "version": f"{name}-{scorer.trained_through:%Y%m%d}",
        "validation": validation,
        "thresholds": economics.thresholds(),
        "list_prices": prices,
        "versions": {"scikit-learn": sklearn.__version__, "pandas": pd.__version__},
        "categories": {key: sorted(df[key].dropna().unique().tolist()) for key in config.KNOWN_CATEGORICAL},
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    return meta


def run(df, out_dir=config.MODELS):
    fit, valid = data.split_forward(df)
    y = valid[config.LABEL].to_numpy(float)
    scores = evaluate.compare(fit, valid)
    results = {name: evaluate.metrics(y, s) for name, s in scores.items()}
    name = evaluate.choose({n: m["pr_auc"] for n, m in results.items()})
    return fit_final(df, name, results[name], reference.list_prices(), out_dir)


if __name__ == "__main__":
    meta = run(data.load_train())
    print(pd.Series(meta["validation"]).round(3).to_string())
    print(meta["model"], meta["version"])
