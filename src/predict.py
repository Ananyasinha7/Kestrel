import pandas as pd

from . import config, data
from .engine import Engine


def main():
    engine = Engine.load()
    test = data.load_test(engine.meta["list_prices"])
    scores = engine.scorer.predict(test)
    if config.SAMPLE_FILE.exists():
        sample = pd.read_csv(config.SAMPLE_FILE, dtype=str)
    else:
        sample = pd.DataFrame({config.ID: test[config.ID].astype(str), "score": ""})
    id_column, score_column = sample.columns[:2]
    frame = pd.DataFrame({id_column: test[config.ID].astype(str), score_column: scores})
    out = sample[[id_column]].merge(frame, on=id_column, how="left")
    assert len(out) == len(sample) and out[id_column].is_unique
    assert out[score_column].notna().all() and out[score_column].between(0, 1).all()
    out.to_csv(config.PREDICTIONS_FILE, index=False)
    validation = engine.meta["validation"]
    expectation = (
        f"Expected on the test set, from the Apr to Jun 2026 forward validation: "
        f"AUC {validation['auc']:.3f}, PR-AUC {validation['pr_auc']:.3f}, "
        f"precision in the top 10 percent {validation['precision_top_10pct']:.3f}."
    )
    config.EVIDENCE.mkdir(parents=True, exist_ok=True)
    (config.EVIDENCE / "expected_score.md").write_text(expectation + "\n")
    print(expectation)
    print(f"Wrote {len(out)} rows to {config.PREDICTIONS_FILE}")


if __name__ == "__main__":
    main()
