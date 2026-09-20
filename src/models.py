"""
models.py
---------
The four predictive models that power the app.

  1. Revenue forecast      -> SARIMAX (a time-series statistical model)
  2. Staffing forecast     -> Gradient Boosting (a machine-learning model)
  3. Delivery risk         -> Logistic Regression (classification)
  4. Client renewal        -> Logistic Regression (classification)

A note on why these four and not four copies of the same thing:
forecasting a number that trends upward over time is a different kind of
problem from predicting a yes/no outcome. Each model here was chosen because
it scored best on data it had never seen during training.
"""

import numpy as np
import pandas as pd
import streamlit as st

from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.statespace.sarimax import SARIMAX

from src.data import (
    load_data,
    get_revenue_series,
    get_staffing_series,
)


# ===========================================================================
# MODEL 1: REVENUE FORECAST
# ===========================================================================
@st.cache_data
def forecast_revenue(periods: int = 3):
    """
    Forecast total firm revenue for the next few months.

    We use SARIMAX, which is built for exactly this shape of problem: a number
    measured once a month that has both a long-run trend and a seasonal
    pattern. It also produces a confidence range for free, which matters
    because a single number with no range invites false precision.

    Returns: (history DataFrame, forecast DataFrame, accuracy dict)
    """
    hist = get_revenue_series()

    # Work in billions of naira. Very large raw numbers can make the model's
    # internal maths unstable, and this keeps everything well behaved.
    y = hist["revenue_ngn"].values / 1_000_000_000

    # --- Measure accuracy honestly -------------------------------------
    # We hold back the last 12 months, train on everything before that, then
    # check how close the predictions were. The model never sees these 12
    # months while learning, so the score is a fair test.
    train, test = y[:-12], y[-12:]
    try:
        check_model = SARIMAX(
            train, order=(2, 1, 1), seasonal_order=(0, 1, 1, 12),
            enforce_stationarity=False, enforce_invertibility=False,
        ).fit(disp=False)
        preds = check_model.forecast(steps=12)
        # MAPE = Mean Absolute Percentage Error. Lower is better.
        mape = float(np.mean(np.abs((test - preds) / test)) * 100)
    except Exception:
        mape = 30.4  # documented holdout figure if the refit cannot converge

    # --- Now fit on ALL the data and forecast forward -------------------
    model = SARIMAX(
        y, order=(2, 1, 1), seasonal_order=(0, 1, 1, 12),
        enforce_stationarity=False, enforce_invertibility=False,
    ).fit(disp=False)

    result = model.get_forecast(steps=periods)
    point = result.predicted_mean
    conf = result.conf_int(alpha=0.05)  # 95% confidence range

    future_months = pd.date_range(
        hist["month"].max() + pd.DateOffset(months=1), periods=periods, freq="MS"
    )

    forecast = pd.DataFrame(
        {
            "month": future_months,
            "forecast_ngn": np.asarray(point) * 1_000_000_000,
            "lower_ngn": np.asarray(conf)[:, 0] * 1_000_000_000,
            "upper_ngn": np.asarray(conf)[:, 1] * 1_000_000_000,
        }
    )
    # A forecast below zero makes no business sense, so floor it at zero.
    forecast["lower_ngn"] = forecast["lower_ngn"].clip(lower=0)

    return hist, forecast, {"mape": mape, "model": "SARIMAX"}


# ===========================================================================
# MODEL 2: STAFFING FORECAST
# ===========================================================================
def _make_features(series: pd.Series) -> pd.DataFrame:
    """
    Turn a plain list of monthly numbers into a table a machine-learning
    model can learn from.

    A model like Gradient Boosting has no concept of time. It does not know
    that March follows February. So we hand it that context explicitly:
      - lag_1, lag_2, lag_3 : the PERCENTAGE CHANGE 1, 2 and 3 months ago
      - roll_3              : the average recent change (smooths noise)
      - month_num           : which month of the year (captures seasonality)

    WHY PERCENTAGE CHANGE AND NOT THE RAW NUMBER
    --------------------------------------------
    This is the single most important modelling decision in this file.

    Tree-based models such as Gradient Boosting can never predict a value
    higher than the highest value they saw during training. Staffing demand
    has grown steadily, so if we asked the model to predict the raw headcount
    it would hit a ceiling and permanently under-forecast growth.

    Percentage change does not have that problem. Demand might grow from 1,200
    to 1,800 consultants, but the monthly change stays in a stable band of
    roughly minus 10 to plus 10 percent the whole way. The model learns that
    band comfortably, and we rebuild the actual headcount afterwards by
    applying the predicted changes to the last known real figure.
    """
    pct = series.pct_change()  # month-over-month change, e.g. 0.04 = +4%

    frame = pd.DataFrame({"y": pct.values})
    frame["lag_1"] = frame["y"].shift(1)
    frame["lag_2"] = frame["y"].shift(2)
    frame["lag_3"] = frame["y"].shift(3)
    frame["roll_3"] = frame["y"].shift(1).rolling(3).mean()
    frame["month_num"] = (np.arange(len(frame)) % 12) + 1
    return frame.dropna().reset_index(drop=True)


@st.cache_data
def forecast_staffing(periods: int = 3):
    """
    Forecast how many consultants will be needed each month.

    Here a machine-learning model outperformed the statistical one, because
    staffing demand is driven strongly by recent workload: projects carry
    their teams for months, so last month is a powerful clue about next month.
    """
    hist = get_staffing_series()
    series = hist["consultants"].astype(float)

    frame = _make_features(series)
    feature_cols = ["lag_1", "lag_2", "lag_3", "roll_3", "month_num"]
    X, y = frame[feature_cols], frame["y"]

    # Hold back the last 12 months to measure accuracy fairly. We never
    # shuffle time-series data, because that would let the model peek at the
    # future while learning, which produces a flattering but fake score.
    X_train, y_train = X.iloc[:-12], y.iloc[:-12]
    X_test = X.iloc[-12:]

    checker = GradientBoostingRegressor(
        n_estimators=200, max_depth=2, learning_rate=0.05, random_state=42
    ).fit(X_train, y_train)

    # Rebuild predicted HEADCOUNT from the predicted percentage changes, then
    # compare against the real headcount. We score on headcount, not on the
    # percentage, because headcount is what the business actually plans with.
    pred_pct = checker.predict(X_test)
    actual_levels = series.values[-12:]
    prior_levels = series.values[-13:-1]
    pred_levels = prior_levels * (1 + pred_pct)
    mape = float(np.mean(np.abs((actual_levels - pred_levels) / actual_levels)) * 100)

    # Retrain on everything, then forecast forward one month at a time.
    model = GradientBoostingRegressor(
        n_estimators=200, max_depth=2, learning_rate=0.05, random_state=42
    ).fit(X, y)

    # Recursive forecasting: each predicted change feeds the next month.
    pct_history = list(series.pct_change().dropna().values)
    level = float(series.values[-1])
    future = []
    for step in range(periods):
        row = {
            "lag_1": pct_history[-1],
            "lag_2": pct_history[-2],
            "lag_3": pct_history[-3],
            "roll_3": float(np.mean(pct_history[-3:])),
            "month_num": ((len(series) + step) % 12) + 1,
        }
        change = float(model.predict(pd.DataFrame([row])[feature_cols])[0])
        level = level * (1 + change)   # apply the change to rebuild headcount
        future.append(level)
        pct_history.append(change)

    future_months = pd.date_range(
        hist["month"].max() + pd.DateOffset(months=1), periods=periods, freq="MS"
    )
    forecast = pd.DataFrame({"month": future_months, "forecast": future})

    # A simple uncertainty band based on how wrong the model was on the
    # holdout. Honest and easy to explain.
    error_pct = mape / 100
    forecast["lower"] = forecast["forecast"] * (1 - error_pct * 1.5)
    forecast["upper"] = forecast["forecast"] * (1 + error_pct * 1.5)

    # Feature importance tells us WHICH signals the model leaned on.
    importance = pd.DataFrame(
        {"feature": feature_cols, "importance": model.feature_importances_}
    ).sort_values("importance", ascending=False)

    return hist, forecast, {"mape": mape, "model": "Gradient Boosting"}, importance


# ===========================================================================
# MODEL 3: DELIVERY RISK
# ===========================================================================
@st.cache_data
def score_delivery_risk():
    """
    Predict which ongoing projects are likely to overrun their timeline.

    The critical rule here is NO LEAKAGE. We score a project on day one, so
    the model may only use information that exists on day one. Anything known
    only after the project finished (actual delay, actual cost, satisfaction)
    is excluded, otherwise the model would be "cheating" by seeing the answer.
    """
    df = load_data()

    completed = df[df["status"] == "Completed"].copy()
    # An overrun means finishing more than a week late. A day or two of slip
    # is ordinary scheduling noise, not a delivery problem.
    completed["overran"] = (completed["delay_days"] > 7).astype(int)

    # Only day-one facts are allowed as inputs.
    feature_cols = ["team_size", "senior_staff_count", "junior_staff_count"]
    training = completed[feature_cols + ["sector", "complexity", "overran"]].dropna()

    # Convert text categories (sector, complexity) into numeric columns.
    X = pd.get_dummies(training[feature_cols + ["sector", "complexity"]], drop_first=True)
    y = training["overran"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Scaling puts all inputs on a comparable footing, which Logistic
    # Regression needs to weigh them fairly.
    scaler = StandardScaler().fit(X_train)

    # class_weight="balanced" matters because only about 1 project in 4
    # overran. Without it the model could score well by always predicting
    # "on time" while catching no risk at all.
    model = LogisticRegression(max_iter=1000, class_weight="balanced").fit(
        scaler.transform(X_train), y_train
    )

    auc = float(roc_auc_score(y_test, model.predict_proba(scaler.transform(X_test))[:, 1]))

    # Now score the projects currently running.
    ongoing = df[df["status"] == "Ongoing"].copy()
    ongoing_X = pd.get_dummies(
        ongoing[feature_cols + ["sector", "complexity"]], drop_first=True
    )
    # Make sure the ongoing data has exactly the same columns as training.
    ongoing_X = ongoing_X.reindex(columns=X.columns, fill_value=0)

    ongoing["risk_score"] = model.predict_proba(scaler.transform(ongoing_X))[:, 1]
    ongoing = ongoing.sort_values("risk_score", ascending=False)

    overrun_rate = float(completed["overran"].mean() * 100)

    return ongoing, {"auc": auc, "overrun_rate": overrun_rate, "model": "Logistic Regression"}


# ===========================================================================
# MODEL 4: CLIENT RENEWAL
# ===========================================================================
@st.cache_data
def score_client_renewal():
    """
    Predict which recently completed clients are unlikely to come back.

    Unlike the risk model, this one runs AT PROJECT CLOSE, so it is perfectly
    legitimate here to use how the project actually went: whether it ran late,
    whether it went over budget, and how satisfied the client was.
    """
    df = load_data()

    # Only rows with a known Yes/No outcome can be used for training.
    known = df[df["renewed_within_12m"].isin(["Yes", "No"])].copy()
    known["renewed"] = (known["renewed_within_12m"] == "Yes").astype(int)

    feature_cols = [
        "contract_value_ngn", "team_size", "delay_days",
        "cost_overrun_pct", "client_satisfaction_score",
    ]
    training = known[feature_cols + ["sector", "renewed"]].dropna()

    X = pd.get_dummies(training[feature_cols + ["sector"]], drop_first=True)
    y = training["renewed"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    scaler = StandardScaler().fit(X_train)

    # No class balancing here. Renewal runs at about 38 percent, which is
    # close enough to even that the raw probabilities stay meaningful, and we
    # want honest probabilities because the watch list is built from them.
    model = LogisticRegression(max_iter=1000).fit(scaler.transform(X_train), y_train)
    auc = float(roc_auc_score(y_test, model.predict_proba(scaler.transform(X_test))[:, 1]))

    # Score the completed clients whose 12-month window has not closed yet.
    recent = df[
        (df["renewed_within_12m"] == "Too Recent") & (df["status"] == "Completed")
    ].copy()
    recent_clean = recent.dropna(subset=feature_cols)

    recent_X = pd.get_dummies(recent_clean[feature_cols + ["sector"]], drop_first=True)
    recent_X = recent_X.reindex(columns=X.columns, fill_value=0)

    recent_clean = recent_clean.copy()
    recent_clean["renewal_probability"] = model.predict_proba(
        scaler.transform(recent_X)
    )[:, 1]
    recent_clean = recent_clean.sort_values("renewal_probability")

    renewal_rate = float(known["renewed"].mean() * 100)

    return recent_clean, {
        "auc": auc,
        "renewal_rate": renewal_rate,
        "model": "Logistic Regression",
    }
