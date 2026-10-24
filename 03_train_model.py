
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    balanced_accuracy_score
)

# 1. Load engineered features
data = pd.read_csv("outputs/features.csv")

feature_columns = [
    "plays_last_7_days",
    "plays_last_24_hours",
    "total_plays_before",
    "minutes_since_last_play",
    "unique_tracks_last_7_days",
    "listening_diversity"
]

required_columns = feature_columns + [
    "target",
    "observation_time"
]

missing_columns = [
    column for column in required_columns
    if column not in data.columns
]

if missing_columns:
    raise ValueError(
        f"Missing columns in features.csv: {missing_columns}"
    )

# 2. Prepare the data
data["observation_time"] = pd.to_datetime(
    data["observation_time"],
    errors="coerce"
)

data = data.dropna(
    subset=["observation_time", "target"]
).sort_values("observation_time")

# 3. Split chronologically
split_time = data["observation_time"].quantile(0.8)

train = data[data["observation_time"] < split_time]
test = data[data["observation_time"] >= split_time]

if train.empty or test.empty:
    raise ValueError("Training or testing data is empty.")

X_train = train[feature_columns]
X_test = test[feature_columns]

y_train = train["target"].astype(int)
y_test = test["target"].astype(int)

if y_train.nunique() < 2:
    raise ValueError(
        "Training data must contain both target classes."
    )

# 4. Create the model pipeline
model = make_pipeline(
    SimpleImputer(strategy="median"),
    RandomForestClassifier(
        n_estimators=100,
        max_depth=12,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
)

# 5. Train
model.fit(X_train, y_train)

# 6. Predict
predictions = model.predict(X_test)

print("Training records:", len(train))
print("Testing records:", len(test))

print(
    "\nBalanced accuracy:",
    round(balanced_accuracy_score(y_test, predictions), 4)
)

print("\nClassification report:")
print(
    classification_report(
        y_test,
        predictions,
        zero_division=0
    )
)

print("\nConfusion matrix:")
print(confusion_matrix(y_test, predictions))

# 7. Feature importance
forest = model.named_steps["randomforestclassifier"]

importance = pd.Series(
    forest.feature_importances_,
    index=feature_columns
).sort_values(ascending=False)

print("\nFeature importance:")
print(importance)
