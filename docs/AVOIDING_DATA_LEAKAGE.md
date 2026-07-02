# Avoiding Data Leakage — Required Reading Before Training Any Model

This document exists because we hit this bug in this exact codebase. It is the single most important thing to understand before you train or evaluate any model.

## Table of contents

- [What happened](#what-happened)
- [Why EEG makes this dangerous](#why-eeg-makes-this-dangerous)
- [Two concrete bugs](#two-concrete-bugs)
  - [Bug 1: wrong train/test split](#bug-1-wrong-train-test-split)
  - [Bug 2: wrong feature selection order](#bug-2-wrong-feature-selection-order)
- [The general rule](#the-general-rule)
- [Sanity-check checklist](#sanity-check-checklist)

---

## What happened

Early in this project, `ml/train_depression.py` reported:

```text
CV accuracy : 0.996 ± 0.004
```

That number was **fake**.
The model had not learned depression. It had learned to recognize *which of the 7 specific subjects* each window came from.
Because labels were correlated with subject identity, recognizing the person looked identical to recognizing the label.

After fixing the bug, the honest result became:

```text
CV accuracy : 0.378 ± 0.175
```

That is worse than chance (50% for binary classification), but it is informative. With only 7 subjects, individual differences overwhelm any depression signal, and the dataset is too small for stable cross-validation. The bad number told us the real fix: get more subjects.

---

## Why EEG makes this dangerous

EEG varies enormously between people due to:

- skull shape and thickness
- electrode placement
- baseline cortical activity
- hair and contact quality

> **A classifier can often tell two people apart more easily than it can tell two conditions apart.**

If the model sees a subject during training and the same subject again during testing, it can cheat by learning the person’s EEG signature instead of the condition.

This is not unique to EEG. It applies whenever multiple samples come from the same small set of sources. EEG is just an especially sharp example.

---

## Two concrete bugs

### Bug 1 — wrong train/test split

**Wrong approach:**

```python
from sklearn.model_selection import StratifiedKFold

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scores = cross_val_score(model, X, y, cv=cv)
```

`StratifiedKFold` only knows the class label `y`. It does not know that windows 1–99 came from `sub-001` and windows 100–171 came from `sub-002`. It may put the same subject into both training and test sets, letting the model cheat.

**Correct fix:**

```python
from sklearn.model_selection import GroupKFold

# groups[i] = subject ID for window X[i]
cv = GroupKFold(n_splits=5)
scores = cross_val_score(model, X, y, groups=groups, cv=cv)
```

`GroupKFold` ensures all windows from one subject stay in the same fold. Each test fold contains only subjects the model has never seen during training.

> Where this lives: `ml/train_depression.py` builds `groups` in `build_dataset()` and passes it to `GroupKFold`.

### Bug 2 — wrong feature selection order

**Wrong approach:**

```python
mask = anova_select(X, y)        # uses all data, including future test rows
X_selected = X[:, mask]
scores = cross_val_score(model, X_selected, y, cv=cv)
```

Here, feature selection looks at the entire dataset before cross-validation. That leaks information from the test folds into the selected feature set, inflating accuracy.

**Correct fix:**

Put selection and scaling inside an `sklearn.Pipeline`.

```python
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import SelectFpr, f_classif

pipeline = Pipeline([
    ("select", SelectFpr(f_classif, alpha=0.05)),
    ("scale",  StandardScaler()),
    ("clf",    SVC(kernel="linear")),
])
scores = cross_val_score(pipeline, X, y, groups=groups, cv=cv)
```

`cross_val_score` fits the pipeline separately on each fold. `SelectFpr` only sees the training rows for that fold, so it cannot peek at the test data.

**Also:** scaling must live inside the pipeline too. If you compute `StandardScaler` statistics on all data before splitting, the test fold leaks into normalization.

---

## The general rule

> Anything that “looks at the data” to make a decision — selecting features, computing normalization statistics, tuning hyperparameters — must only ever look at the current training fold.

If any of these steps touches a row that will later be evaluated as test data, the reported accuracy is not trustworthy.

The `Pipeline` + `cross_val_score(..., groups=...)` pattern used in `ml/` is how this repo enforces that rule.

If you write a new training script, copy that pattern. Do not write a manual “select features, then split” sequence.

---

## Sanity-check checklist

If accuracy looks too good, ask yourself:

1. Could a test row share information with a training row? (same subject, same session, same augmented image, overlapping text)
2. Did I select features, scale data, or tune parameters using the full dataset before splitting? If yes, move it inside a `Pipeline`.
3. Does the result match published numbers for a similar setup? If published work reports 75–85% and you have 99%+, leakage is likely.

This sequence caught the bug in this repo, and it is the same one you should follow for every new model.
