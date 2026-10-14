import math

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

from . import config, data, economics, features, model

TOP_FRACTIONS = (0.05, 0.10, 0.25)


def precision_at(y, score, fraction):
    k = math.ceil(fraction * len(y))
    return float(y[np.argsort(-score)[:k]].mean())


def metrics(y, score):
    out = {
        "auc": roc_auc_score(y, score),
        "pr_auc": average_precision_score(y, score),
        "accuracy": float(((score >= 0.5) == y).mean()),
        "majority_accuracy": float(max(y.mean(), 1 - y.mean())),
    }
    for fraction in TOP_FRACTIONS:
        out[f"precision_top_{int(fraction * 100)}pct"] = precision_at(y, score, fraction)
    return out


def choose(pr_auc):
    best = max(pr_auc.values())
    return next(name for name in model.CANDIDATES if pr_auc[name] >= best - config.SELECTION_TOLERANCE)


def compare(fit, valid):
    return {name: model.candidate(name).fit(fit).predict(valid) for name in model.CANDIDATES}


def mistakes(y, score, threshold):
    called = score >= threshold
    return pd.DataFrame(
        [
            {
                "threshold": threshold,
                "called": int(called.sum()),
                "false_positives": int((called & (y == 0)).sum()),
                "false_negatives": int((~called & (y == 1)).sum()),
                "true_positives": int((called & (y == 1)).sum()),
                "true_negatives": int((~called & (y == 0)).sum()),
                "precision_of_calls": float(y[called].mean()) if called.any() else 0.0,
            }
        ]
    )


def calibration(y, score, bins=10):
    frame = pd.DataFrame({"y": y, "p": score})
    frame["bin"] = pd.qcut(frame["p"], bins, duplicates="drop")
    return frame.groupby("bin", observed=True).agg(
        mean_predicted=("p", "mean"), observed_rate=("y", "mean"), orders=("y", "size")
    ).reset_index(drop=True)


def with_leaks(df):
    out = df.copy()
    out["service_event"] = df["last_service_event_type"].astype("string")
    out["pickup_present"] = df["pickup_scheduled_at"].notna().astype(int)
    return out


def leakage(fit, valid):
    leaky = model.Scorer(
        "gbm", features.NUMERIC + ("pickup_present",), features.CATEGORICAL + ("service_event",), "leaky"
    )
    y = valid[config.LABEL].to_numpy()
    leaky_auc = roc_auc_score(y, leaky.fit(with_leaks(fit)).predict(with_leaks(valid)))
    honest_auc = roc_auc_score(y, model.candidate("gbm").fit(fit).predict(valid))
    return leaky_auc, honest_auc


def shield_lift(fit, valid):
    y = valid[config.LABEL].to_numpy()
    without = tuple(c for c in features.NUMERIC if c != "is_shield")
    rows = []
    for label, numeric in (("without Shield", without), ("with Shield", features.NUMERIC)):
        score = model.Scorer("logreg", numeric, features.CATEGORICAL).fit(fit).predict(valid)
        rows.append({"model": label, "auc": roc_auc_score(y, score), "pr_auc": average_precision_score(y, score)})
    return pd.DataFrame(rows)


def shield_split(df):
    shield = df["is_shield"] == 1
    return pd.DataFrame(
        [
            {
                "segment": label,
                "orders": int(mask.sum()),
                "return_rate": float(df.loc[mask, config.LABEL].mean()),
                "share_of_returns": float(df.loc[mask, config.LABEL].sum() / df[config.LABEL].sum()),
            }
            for label, mask in (("Shield", shield), ("Not Shield", ~shield))
        ]
    )


def md_table(df, digits=3):
    df = df.round(digits)
    lines = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(lines)


def plot_calibration(table, path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    top = float(max(table["mean_predicted"].max(), table["observed_rate"].max())) * 1.1
    ax.plot([0, top], [0, top], color="#888888", linewidth=1)
    ax.plot(table["mean_predicted"], table["observed_rate"], marker="o", color="#1f4e79")
    ax.set_xlabel("Predicted return rate")
    ax.set_ylabel("Observed return rate")
    ax.set_title("Calibration, Apr to Jun 2026")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def write(name, text):
    config.EVIDENCE.mkdir(parents=True, exist_ok=True)
    (config.EVIDENCE / name).write_text(text + "\n")


def run():
    fit, valid = data.split_forward(data.load_train())
    y = valid[config.LABEL].to_numpy(float)
    value = valid["order_value_inr"].to_numpy(float)
    scores = compare(fit, valid)
    table = pd.DataFrame({name: metrics(y, s) for name, s in scores.items()}).T
    chosen = choose(table["pr_auc"].to_dict())
    best = scores[chosen]
    threshold = economics.thresholds()["call"]

    cal = calibration(y, best)
    plot_calibration(cal, config.EVIDENCE / "calibration.png")
    leaky_auc, honest_auc = leakage(fit, valid)
    full = data.load_train()

    write(
        "metrics.md",
        "\n\n".join(
            [
                f"Validation window: Apr to Jun 2026, {len(valid)} orders, return rate {y.mean():.3f}",
                md_table(table.reset_index(names="model")),
                f"Chosen model: {chosen}",
                f"Majority-class accuracy {table.loc[chosen, 'majority_accuracy']:.3f} "
                f"versus model accuracy {table.loc[chosen, 'accuracy']:.3f}",
                "Errors at the call threshold",
                md_table(mistakes(y, best, threshold)),
                "Calibration",
                md_table(cal),
            ]
        ),
    )
    write(
        "reference_data.md",
        "\n\n".join(
            [
                "Shield membership from customers.csv, forward validation Apr to Jun 2026",
                md_table(shield_lift(fit, valid)),
                "Return rates by segment, all training orders",
                md_table(shield_split(full)),
            ]
        ),
    )
    write(
        "leakage.md",
        md_table(
            pd.DataFrame(
                [{"model": "with service columns", "auc": leaky_auc}, {"model": "honest", "auc": honest_auc}]
            )
        ),
    )
    write(
        "rupees.md",
        "\n\n".join(
            [
                f"Call threshold {threshold:.3f}, from a 25 percent call effect. "
                f"The 35 percent pilot effect would justify {economics.thresholds()['watch']:.3f}. "
                "Both effects, the 12 percent hold cancel rate and the 20 percent margin are assumptions, not measurements.",
                md_table(economics.policy_table(y, best, value), 1),
                md_table(economics.sensitivity_table(y, best, value), 1),
            ]
        ),
    )
    print(md_table(table.reset_index(names="model")))
    print(f"chosen={chosen} leaky_auc={leaky_auc:.3f} honest_auc={honest_auc:.3f}")
    print(md_table(economics.policy_table(y, best, value), 1))


if __name__ == "__main__":
    run()
