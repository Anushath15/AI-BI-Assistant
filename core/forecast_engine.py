import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression


class ForecastEngine:

    def forecast(
        self,
        df: pd.DataFrame,
        date_col: str,
        metric_col: str,
        periods: int = 3,
    ) -> pd.DataFrame:
        """
        Forecast the next N periods using Linear Regression.

        Parameters
        ----------
        df          : DataFrame with date_col and metric_col columns
        date_col    : Name of the date/period column (e.g. 'Order Date')
        metric_col  : Name of the numeric metric (e.g. 'Sales')
        periods     : Number of future months to forecast (default 3)

        Returns
        -------
        DataFrame with columns: date_col, metric_col, type
        type is either 'historical' or 'forecast'
        """

        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col]).sort_values(date_col)

        # Create numeric index for regression (months since start)
        df["_index"] = range(len(df))
        X = df[["_index"]].values
        y = df[metric_col].values

        # Fit Linear Regression
        model = LinearRegression()
        model.fit(X, y)

        # Generate future month indices
        last_date = df[date_col].max()
        future_dates = pd.date_range(
            start=last_date + pd.DateOffset(months=1),
            periods=periods,
            freq="MS",
        )
        future_indices = np.array(
            range(len(df), len(df) + periods)
        ).reshape(-1, 1)
        future_values = model.predict(future_indices)

        # Historical rows
        historical = df[[date_col, metric_col]].copy()
        historical[date_col] = historical[date_col].dt.strftime("%Y-%m")
        historical["type"] = "historical"

        # Forecast rows
        forecast = pd.DataFrame({
            date_col: future_dates.strftime("%Y-%m"),
            metric_col: future_values.round(2),
            "type": "forecast",
        })

        return pd.concat([historical, forecast], ignore_index=True)

    def get_model_info(
        self,
        df: pd.DataFrame,
        date_col: str,
        metric_col: str,
    ) -> dict:
        """
        Returns model coefficients for explainability.
        """
        df = df.copy()
        df["_index"] = range(len(df))
        X = df[["_index"]].values
        y = df[metric_col].values

        model = LinearRegression()
        model.fit(X, y)

        return {
            "slope": round(float(model.coef_[0]), 2),
            "intercept": round(float(model.intercept_), 2),
            "trend": "increasing" if model.coef_[0] > 0 else "decreasing",
        }