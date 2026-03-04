def compute_risk(financial_status, anomaly_ratio, forecast_trend):

    financial_score = {
        "GREEN": 0,
        "YELLOW": 50,
        "RED": 100
    }[financial_status]

    forecast_score = 100 if forecast_trend == "UP" else 0
    anomaly_score = anomaly_ratio * 100

    risk_score = (
        0.4 * financial_score +
        0.3 * forecast_score +
        0.3 * anomaly_score
    )

    if risk_score < 40:
        tier = "GREEN"
    elif risk_score < 70:
        tier = "YELLOW"
    else:
        tier = "RED"

    return round(risk_score, 2), tier