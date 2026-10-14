# AI usage

## What I used

- Claude (Claude Sonnet 5.5, in the Claude chat interface) for nearly everything: reading the pack, data checks, the model and service code, the tests, the evidence and the drafts of the memo and recording script.
- No model API is called at any time by the product. Scoring is a logistic regression with fixed text templates for the reasons, so there is no per-order cost and it starts with no keys.

## What it cost

- Subscription chat usage only. I have no per-token figure.
- Fill in before submitting: plan price and hours used: ______
- The product costs nothing per order.

## What I discarded, and why

- **My first column names.** I wrote the first version of the code before seeing the data and guessed the schema. Almost all of it was wrong, and I rebuilt it on the real files.
- **Gradient boosting.** It scored lower than logistic regression (AUC 0.746 vs 0.784), so I kept the simpler model.
- **The delivery-note text.** It added nothing (AUC 0.740 vs 0.746 for the same model without it), so the chosen model ignores it.
- **Warranty length, product age, customer tenure and state.** Checked once with the logistic and boosted models. None added anything beyond Shield. Signup dates are also unreliable, since 1 in 5 orders predates the customer's signup.
- **The service-system and pickup columns.** They give 0.998 AUC but are written after a return happens, so they would be cheating. The code refuses to use them.
- **A hold flag.** The numbers say a hold loses money.
- **An LLM in the scoring path, and SHAP.** The LLM adds per-order cost, which Finance said not to do without a number. I used a simple swap-and-compare for the reasons instead of SHAP.
- **My first call threshold of 11%.** It loses money if the pilot effect is weaker than claimed, so I moved it to 16%.

## Mistakes I made and corrected

- I printed the share of orders called as 0.3 when it is 34.5%, from a rounding bug. Fixed.
- I stored hashed customer ids, which could be reversed by guessing ids. Removed, since the model does not need them.
