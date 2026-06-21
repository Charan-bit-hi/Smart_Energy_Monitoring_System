# Apex Energy — Smart Energy Monitoring System

This is a small full-stack app for keeping an eye on electricity usage across different sites — think factory floors, warehouses, that kind of thing. It pulls in live readings from smart meters (or a simulator standing in for real ones), shows you what's going on in a dashboard, warns you when something looks off, works out what it's costing you, and even tries to guess what usage will look like tomorrow.

It's a working prototype, not a polished production app — there are a few rough edges noted near the bottom.

## What it's built with

The backend is **FastAPI** (Python), talking to a **MongoDB** database. Auth is handled with JWTs. The frontend is **React** (built with Vite), using Recharts for the graphs. There's also a little Python script that pretends to be a bunch of smart meters, so you can see the system actually doing something without needing real hardware.

Worth flagging: an earlier planning doc for this project sketched out a .NET + SQL Server stack, but what actually got built is the FastAPI/MongoDB/React combo described here. This README reflects the real thing.

## What it actually does

- **Logging in** — three accounts exist out of the box: an Admin, a Manager, and an Engineer, each seeing slightly different things.
- **Meters** — you can register meters, see which ones are active, and each one gets its own security token so it can authenticate when it sends data.
- **Dashboard** — shows current load, how much energy's been used, how many meters are online, and how many alerts are sitting unresolved, plus a chart of the last 24 hours.
- **Alerts** — if a meter reports something outside normal range (too much current, voltage too high or low), it shows up here as a Warning or Critical, and someone can acknowledge it.
- **Billing** — punch in a date range and it'll calculate the cost based on standard and peak-hour tariff rates, broken down per meter.
- **Analytics** — shows you which hours of the day usage peaks, and which meters or sites are using the most energy.
- **ML Forecast** — trains a simple regression model on a meter's history and tries to predict the next 24 hours of power draw, with a rough confidence score attached. If there's not enough history yet, it falls back to a generic baseline guess instead of pretending to be confident.
- **Reports** — generate a daily/weekly/monthly summary as a PDF, Excel file, or CSV, and download it later.

When you start the backend for the first time, it automatically creates a demo company, two sites, three meters, two tariff rates, and the three demo logins — so there's no manual setup needed just to look around.

## How the project is laid out

```
Smart_Energy_Monitoring_System/
├── backend/
│   ├── app/
│   │   ├── main.py            # starts the API, wires up all the routes
│   │   ├── config.py          # reads settings from environment variables
│   │   ├── db.py              # connects to MongoDB, sets indexes, seeds demo data
│   │   ├── auth.py            # handles logins, JWTs, password hashing, role checks
│   │   ├── ml/forecaster.py   # the forecasting logic
│   │   └── routes/            # one file per feature area (meters, alerts, billing, etc.)
│   └── static/reports/        # where generated reports get saved
├── frontend/
│   └── src/App.jsx            # basically the whole UI lives in this one file
├── simulator/
│   └── simulator.py           # pretends to be smart meters sending live data
└── Smart_Energy_Monitoring_System.pdf   # the original project write-up
```

## Running it yourself

You'll need Python 3.10+, Node 18+, and a MongoDB instance running somewhere (local is fine).

**Backend:**

```bash
cd backend
python -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Then make a `.env` file in the `backend/` folder:

```env
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=smart_energy_db
JWT_SECRET_KEY=replace_with_something_long_and_random
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

And start it up:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8091 --reload
```

One thing to know: the code has a small inconsistency where `main.py` defaults to port 8090 if you run it directly, but the frontend and simulator are both hardcoded to talk to port 8091. So run uvicorn with `--port 8091` like above, or it won't connect.

Once it's running, you can poke around the auto-generated API docs at `http://localhost:8091/docs`.

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

It'll print a local address, usually `http://localhost:5173`.

**Simulator (optional, but makes the dashboard actually interesting):**

```bash
cd simulator
pip install requests
python simulator.py
```

This sends fake readings for the three demo meters every 5 seconds, and every so often throws in a deliberate voltage spike or overload so you can watch the Alert system catch it.

## Logging in

| Role | Email | Password |
|---|---|---|
| Admin | admin@apex.com | admin123 |
| Manager | manager@apex.com | manager123 |
| Engineer | engineer@apex.com | engineer123 |

There are also quick-login buttons for all three right on the sign-in screen, so you don't have to type these out.

## A few things I noticed that could use a fix

I went through the screenshots alongside the actual code, and a few things stood out:

- **The port mismatch mentioned above** — easy fix, just needs the default in `main.py` to match what everything else expects.
- **A leftover test meter** shows up called `DET-KVR_Sg0T`, labeled just "Active" — it's showing up in the meters list, the billing breakdown, and skewing the analytics chart. Looks like test data that never got cleaned out of the seed.
- **The forecast chart's x-axis shows "NaN:00"** instead of actual times — there's a date formatting bug in the frontend chart somewhere.
- **The forecast confidence score is sitting at 10%**, which is pretty low — probably needs more historical readings before it's trustworthy, or the model could use better features.
- **136 unresolved alerts** in the demo is a lot — either the simulator is injecting anomalies too aggressively for a clean demo, or acknowledged alerts aren't being excluded from that count properly.

None of these are big problems, just things worth tidying up before this goes anywhere near real use.

## Ideas for what's next

- Wrap it all in Docker Compose so it's a one-command startup instead of three separate terminals.
- Add some real tests around the alert thresholds and cost math.
- Get the JWT secret and Mongo connection string out of plaintext config before this touches anything real.
- Feed the forecasting model more data and fix that chart bug.
- Add pagination to the Alerts table now that it's clearly going to fill up fast.
