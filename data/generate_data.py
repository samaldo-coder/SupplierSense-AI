import pandas as pd
import numpy as np

np.random.seed(42)

suppliers = ["S1", "S2", "S3"]
dates = pd.date_range(end=pd.Timestamp.today(), periods=180)

rows = []

for supplier in suppliers:
    base = np.random.randint(2, 6)
    for date in dates:
        delay = base + np.random.normal(0, 1)
        rows.append({
            "supplier_id": supplier,
            "date": date,
            "delay_days": max(0, round(delay, 2))
        })

df = pd.DataFrame(rows)
df.to_csv("timeseries.csv", index=False)

print("Dataset generated.")