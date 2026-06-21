from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.db import get_db
from app.routes import auth, meters, readings, dashboard, alerts, cost, analytics, predictions, reports

app = FastAPI(
    title="Smart Energy Monitoring & Analytics API",
    description="Backend API for monitoring, analyzing, and forecasting electricity consumption.",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In development, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(meters.router)
app.include_router(readings.router)
app.include_router(dashboard.router)
app.include_router(alerts.router)
app.include_router(cost.router)
app.include_router(analytics.router)
app.include_router(predictions.router)
app.include_router(reports.router)

@app.on_event("startup")
def on_startup():
    print("[INFO] Smart Energy API is starting up...")
    # Trigger DB connection and seeding
    db = get_db()
    print("[INFO] MongoDB connection initialized and database seeded.")

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Smart Energy Monitoring & Analytics System API",
        "version": "1.0.0",
        "documentation": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8090, reload=True)
