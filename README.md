# Apex Energy — Smart Energy Monitoring & Analytics System

A full-stack platform for real-time monitoring, alerting, billing, analytics, and ML-based forecasting of electricity consumption across industrial sites, warehouses, and facilities.

![Status](https://img.shields.io/badge/status-prototype-blue) ![Backend](https://img.shields.io/badge/backend-FastAPI-009688) ![DB](https://img.shields.io/badge/database-MongoDB-47A248) ![Frontend](https://img.shields.io/badge/frontend-React%2019%20%2B%20Vite-61DAFB)

---

## Overview

Apex Energy ingests live telemetry (voltage, current, power, cumulative energy) from smart meters or simulated IoT devices, stores it in MongoDB, and surfaces it through a React dashboard. It detects threshold breaches in real time, calculates electricity costs against configurable tariffs, runs peak-usage analytics, forecasts future load with a scikit-learn regression model, and generates downloadable PDF/Excel/CSV reports.

| Layer | Tech |
|---|---|
| Backend API | FastAPI (Python) |
| Database | MongoDB (PyMongo) |
| Auth | JWT (python-jose) + bcrypt password hashing |
| ML Forecasting | scikit-learn (Linear Regression) + pandas/numpy |
| Frontend | React 19 + Vite, Recharts, lucide-react icons |
| IoT Simulation | Python script posting synthetic telemetry over HTTP |

---

## Features

- **Authentication & RBAC** — JWT login with three roles: `Admin`, `Manager`, `Engineer`, each with scoped permissions.
- **Meter registry** — register/manage smart meters per site, each with a unique device token used to authenticate ingestion requests.
- **Real-time ingestion** — `POST /api/readings` accepts voltage/current/power/energy payloads from meters or the simulator.
- **Live dashboard** — active load, cumulative energy, meter status, and unresolved alert counts, plus a 24-hour power draw chart and per-site distribution breakdown.
- **Alert engine** — flags overcurrent, over/under-voltage, and threshold breaches as `Warning` or `Critical`, with an acknowledge workflow.
- **Tariff-based billing** — calculates cost over a custom date range using standard + peak-surcharge tariff rates, broken down per meter.
- **Analytics** — daily peak-hour usage profile and top energy-consuming meters/sites over the last 7 days.
- **ML load forecasting** — trains a per-meter Linear Regression model on historical readings (hour-of-day + day-of-week features) to predict the next 24 hours of power draw, with a confidence score; falls back to a simulated baseline profile when history is insufficient.
- **Report generation** — exports Daily/Weekly/Monthly consumption + billing summaries as PDF, Excel, or CSV.
- **Auto-seeded demo data** — on first run, the database seeds a demo organization (Apex Manufacturing Corp), two sites, three meters, two tariffs, and three demo users (Admin/Manager/Engineer).

---

## Project Structure

```
Smart_Energy_Monitoring_System/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app, CORS, router registration, startup/seed hook
│   │   ├── config.py          # Env-driven config (Mongo URI, JWT secret, token expiry)
│   │   ├── db.py              # MongoDB connection, indexes, demo data seeding
│   │   ├── auth.py            # JWT issue/verify, password hashing, role-based dependency
│   │   ├── ml/
│   │   │   └── forecaster.py  # Linear Regression forecasting + simulated fallback
│   │   └── routes/
│   │       ├── auth.py        # /api/auth — login, refresh, profile
│   │       ├── meters.py      # /api/meters — CRUD
│   │       ├── readings.py    # /api/readings — ingest + fetch history
│   │       ├── dashboard.py   # /api/dashboard — summary aggregates
│   │       ├── alerts.py      # /api/alerts — list + acknowledge
│   │       ├── cost.py        # /api/cost — tariff-based cost calculation
│   │       ├── analytics.py   # /api/analytics — peak-usage, top-consumers
│   │       ├── predictions.py # /api/predictions — ML forecast per meter
│   │       └── reports.py     # /api/reports — generate + download
│   ├── static/reports/        # Generated report files (PDF/XLSX/CSV)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # Single-page app: all views (Dashboard, Meters, Alerts, Billing, Analytics, ML Forecast, Reports)
│   │   ├── main.jsx
│   │   └── index.css / App.css
│   ├── package.json
│   └── vite.config.js
├── simulator/
│   └── simulator.py           # IoT meter simulator (posts synthetic telemetry every 5s)
└── Smart_Energy_Monitoring_System.pdf   # Original project write-up
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- A running MongoDB instance (local or Atlas)

### 1. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in `backend/`:

```env
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=smart_energy_db
JWT_SECRET_KEY=replace_with_a_long_random_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

Run the API:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8091 --reload
```

> ⚠️ **Port note:** the frontend (`API_BASE` in `src/App.jsx`) and the simulator (`API_URL` in `simulator.py`) both target **port 8091**, but `main.py`'s `if __name__ == "__main__"` block defaults to **8090**. Run uvicorn explicitly with `--port 8091` (as above), or update all three to match.

On first startup, the app connects to MongoDB, creates indexes, and seeds demo data automatically — no manual migration step needed.

Interactive API docs (Swagger UI) are available at `http://localhost:8091/docs` once running.

### 2. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server will print a local URL (typically `http://localhost:5173`).

### 3. (Optional) IoT meter simulator

To populate the dashboard with live data and trigger alerts:

```bash
cd simulator
pip install requests
python simulator.py
```

The simulator posts readings for three seeded meters every 5 seconds, and periodically injects voltage/load anomalies to exercise the Alert Engine.

---

## Demo Accounts

Seeded automatically on first run:

| Role | Email | Password |
|---|---|---|
| Admin | `admin@apex.com` | `admin123` |
| Manager | `manager@apex.com` | `manager123` |
| Engineer | `engineer@apex.com` | `engineer123` |

*(Quick-access buttons for all three are available directly on the login screen.)*

---

## Seeded Demo Data

- **Organization:** Apex Manufacturing Corp (Industrial)
- **Sites:** Detroit Main Plant, Chicago Distribution Center
- **Meters:** Main Plant HVAC Meter, Assembly Line B Power Meter, Warehouse Lighting Meter
- **Tariffs:** Industrial Standard Rate ($0.12/kWh), Peak Hours Surcharge ($0.18/kWh, 14:00–18:00)

---

## API Reference (Summary)

| Module | Base Path | Key Endpoints |
|---|---|---|
| Auth | `/api/auth` | `POST /login`, `POST /login/json`, `POST /refresh`, `GET /profile` |
| Meters | `/api/meters` | `GET /`, `POST /`, `GET /{meter_id}`, `PUT /{meter_id}`, `DELETE /{meter_id}` |
| Readings | `/api/readings` | `POST /` (device token auth), `GET /{meter_id}` |
| Dashboard | `/api/dashboard` | `GET /summary` |
| Alerts | `/api/alerts` | `GET /`, `POST /{alert_id}/acknowledge` |
| Cost | `/api/cost` | `GET /calculate` |
| Analytics | `/api/analytics` | `GET /peak-usage`, `GET /top-consumers` |
| Predictions | `/api/predictions` | `GET /{meter_id}?hours=24` |
| Reports | `/api/reports` | `POST /generate`, `GET /{report_id}/download` |

Full request/response schemas are auto-generated and browsable at `/docs` (Swagger) and `/redoc`.

---

## Known Issues / Notes for Next Iteration

These were visible from the current build (screenshots + code) and are worth fixing next:

1. **Port mismatch** between `main.py`'s default (`8090`) and the frontend/simulator (`8091`) — standardize on one via the `.env`/config rather than a hardcoded default.
2. **Stray seed/test meter** — a meter labeled `DET-KVR_Sg0T` with label `"Active"` appears in the Meters table and Billing breakdown; looks like leftover test data and should be cleaned from the seed or removed via the UI.
3. **ML Forecast page** — the "Predicted Power Draw" chart axis shows `NaN:00` labels (a date/timestamp formatting bug in the frontend chart's x-axis), and the confidence score (10%) is quite low, suggesting the model needs more historical readings or better feature engineering before it's representative.
4. **Alerts volume** — 136 unresolved alerts in the demo session suggests either the simulator's anomaly injection is too aggressive for a realistic demo, or acknowledged alerts aren't being filtered/cleared from the "Unresolved" count correctly.
5. **Top 5 Energy Consumers chart** — only 3–4 bars render (one stray "Active" bar matches the stray meter above); worth re-checking the underlying aggregation once the seed data is cleaned up.

---

## Roadmap Ideas

- Containerize backend + MongoDB + frontend with Docker Compose for one-command startup.
- Add automated tests around the Alert Engine thresholds and the cost calculation logic (`test_aggregate.py` exists as a start).
- Move JWT secret and Mongo URI to a secrets manager before any real deployment.
- Improve the forecasting model (more training history, additional features, or swap in a time-series-specific model) and fix the chart x-axis formatting.
- Add pagination/filtering to the Alerts table now that volume is non-trivial.
