# Model card

**Task:** probability that an existing identified customer has at least one valid purchase in the 30 days following the cutoff. A non-purchase label is not a contractual churn label.

**Features:** recency in days, distinct historical order count, gross historical spend, tenure, average order value, distinct orders in the previous 30 days. All features use transactions strictly before the snapshot cutoff. Customer ID is not a feature.

**Observation end:** midnight following the latest transaction date. This assumes the data feed is complete through that day. Predictions relate to historical dataset time, not wall-clock time.

**Splits:** training at end−90 days, validation at end−60 days, test at end−30 days. Each has the following 30 days as its label window. Require at least 180 days of history, 30 customers per snapshot and five customers per class. The same customers may recur at successive snapshots; the task is existing-customer prediction.

**Selection:** fit Logistic Regression (standardized features) and Random Forest on the training snapshot. Select maximum validation F1 at threshold 0.5. Refit the selected model on training + validation snapshots, then evaluate once on the test snapshot. A prior-probability DummyClassifier trained on the initial snapshot is reported as a baseline. F1 can legitimately be worse than the baseline.

**Scoring:** after test metrics are recorded, refit the selected estimator on all three labelled snapshots, and score customers at observation end. Test metrics describe the evaluated model, not an independent test of this final refit. Scores are stored in SQLite; model objects are not serialized.

**Limitations:** only one temporal test window, uncalibrated probabilities, seasonality/drift risk, overlapping customer identities across time, identified purchasers only, no causality or measured campaign benefit. Synthetic results establish software function only. A production study should add more temporal backtests, probability calibration and experiments measuring actual business impact.

**Segments:** fixed business rules (not machine-learned clustering), applied in precedence order: Loyal = recency ≤30 days and ≥5 orders; Inactive = recency >90 days; New / one-time = frequency 1 among remaining; Developing = remaining.
