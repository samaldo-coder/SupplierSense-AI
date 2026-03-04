import pandas as pd
import numpy as np

def anomaly_score():
    df = pd.read_csv("timeseries.csv")
    z = (df["delay_days"] - df["delay_days"].mean()) / df["delay_days"].std()
    df["anomaly"] = (np.abs(z) > 2.5).astype(int)
    return float(df["anomaly"].mean())