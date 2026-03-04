import pandas as pd
from statsforecast import StatsForecast
from statsforecast.models import AutoARIMA

def run_forecast():
    df = pd.read_csv("timeseries.csv")
    df = df.rename(columns={
        "supplier_id": "unique_id",
        "date": "ds",
        "delay_days": "y"
    })

    sf = StatsForecast(models=[AutoARIMA()], freq="D")
    forecast = sf.forecast(df=df, h=7)

    forecast.to_csv("forecast.csv", index=False)
    return forecast