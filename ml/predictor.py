import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")
def prepare_daily_series(transactions, category):
    """
    Convert transactions to daily totals
    for a specific category
    """
    df = pd.DataFrame(transactions)
    cat_df = df[df["category"] == category].copy()

    if cat_df.empty:
        return None
    cat_df["date"] = pd.to_datetime(
        cat_df["date"], errors="coerce"
    )
    cat_df = cat_df.dropna(subset=["date"])
    daily = cat_df.groupby("date")["amount"].sum()
    if len(daily) > 1:
        date_range = pd.date_range(
            start=daily.index.min(),
            end=daily.index.max(),
            freq="D"
        )
        daily = daily.reindex(date_range, fill_value=0)

    return daily


def predict_arima(daily_series, forecast_days=30):
    """
    Try ARIMA prediction.
    Returns forecast array or None if failed.
    """
    try:
        from statsmodels.tsa.arima.model import ARIMA
        if len(daily_series) < 30:
            return None

        model  = ARIMA(daily_series, order=(2, 1, 2))
        fitted = model.fit()
        forecast = fitted.get_forecast(steps=forecast_days)

        pred_mean = forecast.predicted_mean
        conf_int  = forecast.conf_int()

        return {
            "method":     "ARIMA",
            "forecast":   pred_mean.clip(lower=0).round(2).tolist(),
            "lower_ci":   conf_int.iloc[:, 0].clip(lower=0).round(2).tolist(),
            "upper_ci":   conf_int.iloc[:, 1].clip(lower=0).round(2).tolist(),
        }
    except:
        return None


def predict_rolling_average(daily_series, forecast_days=30):
    """
    Fallback: 3-month rolling average prediction
    Used when < 30 days of data available
    """
    if daily_series is None or len(daily_series) == 0:
        return {
            "method":   "no_data",
            "forecast": [0.0] * forecast_days,
            "lower_ci": [0.0] * forecast_days,
            "upper_ci": [0.0] * forecast_days,
        }
    mean_val = float(daily_series.mean())
    std_val  = float(daily_series.std() or 0)

    forecast = [round(mean_val, 2)] * forecast_days
    lower    = [round(max(0, mean_val - std_val), 2)] * forecast_days
    upper    = [round(mean_val + std_val, 2)] * forecast_days

    return {
        "method":   "rolling_average",
        "forecast": forecast,
        "lower_ci": lower,
        "upper_ci": upper,
    }


def predict_category(transactions, category, forecast_days=30):
    """
    Main prediction function per category.
    Tries ARIMA first, falls back to rolling average.
    """
    daily = prepare_daily_series(transactions, category)

    if daily is None or len(daily) < 7:
        return predict_rolling_average(
            pd.Series([0]), forecast_days
        )
    arima_result = predict_arima(daily, forecast_days)

    if arima_result:
        print(f"    {category}: ARIMA prediction")
        return arima_result
    else:
        print(f"  {category}: Rolling average fallback")
        return predict_rolling_average(daily, forecast_days)


def predict_all_categories(transactions, forecast_days=30):
    """
    Predict next 30 days for ALL categories
    Returns dict of category → prediction
    """
    df = pd.DataFrame(transactions)
    if df.empty:
        return {}

    categories = df["category"].unique().tolist()
    results    = {}

    print(f"  → Predicting {len(categories)} categories...")

    for cat in categories:
        result = predict_category(
            transactions, cat, forecast_days
        )
        monthly_total = round(sum(result["forecast"]), 2)

        results[cat] = {
            "method":        result["method"],
            "daily_forecast": result["forecast"],
            "lower_ci":      result["lower_ci"],
            "upper_ci":      result["upper_ci"],
            "predicted_monthly_total": monthly_total,
            "forecast_days": forecast_days,
        }

    return results