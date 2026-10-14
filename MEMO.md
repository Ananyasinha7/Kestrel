# Memo: returns, what to do next week

To: Ritu Deshpande. From: [your name]. Cc: Farhan, Meenal, Tanmay.

## The decision

Do not hold flagged orders. Call the customer before dispatch instead.

The model works, but not at the level of the 95% promised to the board. Only 1 order in 9 is returned, so a model that says "no return" every time is already right 88.5% of the time. Ours is right 89.6% of the time. Reaching 95% is not possible with the information we have at dispatch, and no model built on this data will get there. Accuracy is the wrong yardstick here. The right one is rupees.

## The number

The model ranks orders well. Among the 10% of orders it scores riskiest, 42% really came back, against 11.5% overall. We checked this on April to June 2026 orders that the model had never seen.

It is not a crystal ball. If we call every order scoring above 16%, about 1 in 5 of all orders, then 3 in 10 of those calls reach a customer who would have returned the order. The other 7 are false alarms, and we also miss about 4 in 10 of the returns. That is acceptable for a Rs 45 call. It is not acceptable for a hold.

## The rupees

Using Finance's Rs 1,150 per return (not Rs 600), Rs 45 per call and the spring pilot's 35% prevention rate:

- **Calling flagged orders:** about Rs 16,000 saved for every 1,000 orders. If the pilot effect is really only 25%, about Rs 8,600. If it is only 15%, still about Rs 1,200, so it does not lose money.
- **Holding flagged orders:** about Rs 36,000 lost for every 1,000 orders. A hold loses 12% of the orders to cancellation, and most flagged orders would not have come back anyway. Even on a thin 10% margin, holding loses money.
- At about 700 orders a month, calling is worth roughly Rs 18,000 to Rs 34,000 a quarter. It is a modest gain, and a hold would reverse it.

The Rs 16,000 and the hold loss rest on two things we have not measured: the 35% pilot effect, and a 20% margin we assumed for lost sales.

## Shield

Shield members return more often (18.6% against 9.4%), but they are about a third of returns (36%), not most of them. They are 22% of orders and 45% of the call list. They should get a courtesy call, and never a hold. The model uses Shield status and is better for it.

## What to do next week

1. Stop the plan to hold dispatch. Start confirmation calls on orders scoring 16% or more, about 38 calls a week, around Rs 1,700.
2. Randomly leave one in four flagged orders uncalled. After 6 to 8 weeks we will know the true effect of a call, which is the number everything above depends on.
3. Tell the board the target is net rupees saved per 1,000 orders, not accuracy.
4. Farhan: send us the margin on a cancelled order, so the hold cost stops being an assumption.
5. Tanmay: check the October payment-gateway values (they were 100 times too high) and the signup dates in the customer file, where 1 in 5 orders predates the customer's signup.
