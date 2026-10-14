import pandas as pd

RETURN_COST = 1150.0
CALL_COST = 45.0
CALL_EFFECT = 0.35
OPERATING_EFFECT = 0.25
HOLD_CANCEL_RATE = 0.12
HOLD_MARGIN = 0.20
CALL_EFFECTS = (0.15, 0.25, 0.35)
HOLD_MARGINS = (0.10, 0.20, 0.30)

ACTIONS = {
    "CALL": "Call the customer before dispatch",
    "COURTESY_CALL": "Courtesy call before dispatch. Never hold a Shield order",
    "WATCH": "Dispatch normally. Call if capacity allows and the pilot effect is confirmed",
    "OK": "No action needed",
}


def break_even(effect=CALL_EFFECT):
    return CALL_COST / (effect * RETURN_COST)


def thresholds():
    return {"call": break_even(OPERATING_EFFECT), "watch": break_even(CALL_EFFECT)}


def tier(score):
    limits = thresholds()
    if score >= limits["call"]:
        return "CALL"
    if score >= limits["watch"]:
        return "WATCH"
    return "OK"


def action(tier_name, shield):
    if tier_name == "CALL" and shield:
        return ACTIONS["COURTESY_CALL"]
    return ACTIONS[tier_name]


def net_call(y, score, threshold, effect=CALL_EFFECT):
    called = score >= threshold
    gain = effect * RETURN_COST * y - CALL_COST
    return float((gain * called).sum() / len(y) * 1000)


def net_hold(y, score, value, threshold, margin=HOLD_MARGIN):
    held = score >= threshold
    gain = HOLD_CANCEL_RATE * (y * RETURN_COST - (1 - y) * margin * value)
    return float((gain * held).sum() / len(y) * 1000)


def policy_table(y, score, value):
    limits = thresholds()
    call, watch = limits["call"], limits["watch"]
    rows = [
        ("Do nothing", 0.0, 0.0),
        ("Call everyone", net_call(y, score, 0.0), 100.0),
        (f"Call when risk is at least {watch:.0%} (break-even if the pilot effect is 35%)", net_call(y, score, watch), float((score >= watch).mean() * 100)),
        (f"Call when risk is at least {call:.0%} (operating threshold, break-even at 25%)", net_call(y, score, call), float((score >= call).mean() * 100)),
        (f"Hold when risk is at least {call:.0%}", net_hold(y, score, value, call), float((score >= call).mean() * 100)),
    ]
    return pd.DataFrame(rows, columns=["policy", "net_rs_per_1000_orders", "percent_of_orders_actioned"])


def sensitivity_table(y, score, value):
    call = thresholds()["call"]
    rows = [("True call effect, calling at the operating threshold", f"{e:.0%}", net_call(y, score, call, e)) for e in CALL_EFFECTS]
    rows += [("Hold margin", f"{m:.0%}", net_hold(y, score, value, call, m)) for m in HOLD_MARGINS]
    return pd.DataFrame(rows, columns=["assumption", "value", "net_rs_per_1000_orders"])
