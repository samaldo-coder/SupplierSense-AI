# SupplierSense-AI
SupplierSense AI (Backend)

Run:
pip install -r requirements.txt
python data/generate_data.py
uvicorn api.main:app --reload

API:
GET /health
GET /risk/{supplier_id}
GET /anomaly
GET /forecast
GET /supplier/{supplier_id}