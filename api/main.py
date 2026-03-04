from fastapi import FastAPI
from intelligence.anomaly import anomaly_score
from intelligence.forecast import run_forecast
from intelligence.risk_score import compute_risk

app = FastAPI()

@app.get("/")
def root():
    return {"message": "SupplierSense Backend API running"}

@app.get("/risk/{supplier_id}")
def get_risk(supplier_id: str):
    anomaly_ratio = anomaly_score()

    risk_score, tier = compute_risk(
        financial_status="YELLOW",
        anomaly_ratio=anomaly_ratio,
        forecast_trend="UP"
    )

    return {
        "supplier_id": supplier_id,
        "risk_score": risk_score,
        "tier": tier
    }

@app.get("/anomaly")
def get_anomaly():
    return {"anomaly_ratio": anomaly_score()}

@app.get("/forecast")
def get_forecast():
    forecast = run_forecast()
    return forecast.to_dict(orient="records")
