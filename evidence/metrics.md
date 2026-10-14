Validation window: Apr to Jun 2026, 2126 orders, return rate 0.115

| model | auc | pr_auc | accuracy | majority_accuracy | precision_top_5pct | precision_top_10pct | precision_top_25pct |
|---|---|---|---|---|---|---|---|
| logreg | 0.784 | 0.413 | 0.896 | 0.885 | 0.57 | 0.423 | 0.278 |
| gbm | 0.746 | 0.337 | 0.889 | 0.885 | 0.477 | 0.408 | 0.256 |
| gbm_note | 0.74 | 0.336 | 0.889 | 0.885 | 0.486 | 0.413 | 0.246 |

Chosen model: logreg

Majority-class accuracy 0.885 versus model accuracy 0.896

Errors at the call threshold

| threshold | called | false_positives | false_negatives | true_positives | true_negatives | precision_of_calls |
|---|---|---|---|---|---|---|
| 0.157 | 468 | 331 | 108 | 137 | 1550 | 0.293 |

Calibration

| mean_predicted | observed_rate | orders |
|---|---|---|
| 0.015 | 0.019 | 213 |
| 0.028 | 0.019 | 213 |
| 0.04 | 0.047 | 212 |
| 0.052 | 0.038 | 213 |
| 0.066 | 0.047 | 212 |
| 0.084 | 0.103 | 213 |
| 0.108 | 0.118 | 212 |
| 0.143 | 0.141 | 213 |
| 0.209 | 0.198 | 212 |
| 0.419 | 0.423 | 213 |
