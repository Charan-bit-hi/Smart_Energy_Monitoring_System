import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta
import dateutil.parser

def train_and_forecast(readings, forecast_hours=24):
    """
    Trains a LinearRegression model on historical meter readings and
    generates a forecast for the next `forecast_hours` hours.
    
    If historical data is insufficient (less than 10 readings),
    returns a simulated forecast based on daily profile templates.
    """
    if len(readings) < 10:
        return generate_simulated_forecast(forecast_hours, "Insufficient historical data. Showing baseline estimate.")
        
    try:
        # Convert to Pandas DataFrame
        df = pd.DataFrame(readings)
        df["dt"] = df["timestamp"].apply(dateutil.parser.isoparse)
        df["hour"] = df["dt"].dt.hour
        df["dayofweek"] = df["dt"].dt.dayofweek
        
        # We'll use time index (seconds elapsed from start) as trend
        start_time = df["dt"].min()
        df["trend"] = (df["dt"] - start_time).dt.total_seconds() / 3600.0 # hours from start
        
        # Features and target
        # One-hot encode hour and dayofweek for better cyclical patterns
        X = pd.get_dummies(df[["hour", "dayofweek"]], columns=["hour", "dayofweek"])
        X["trend"] = df["trend"]
        y = df["powerKw"].values
        
        # Fit Linear Regression
        model = LinearRegression()
        model.fit(X, y)
        
        # Calculate R^2 score as confidence score
        r2 = model.score(X, y)
        confidence_score = max(0.1, min(0.99, r2))
        
        # Generate forecast features
        forecast_results = []
        last_dt = df["dt"].max()
        
        for h in range(1, forecast_hours + 1):
            future_dt = last_dt + timedelta(hours=h)
            
            # Construct feature row
            row_dict = {col: 0 for col in X.columns}
            row_dict["trend"] = (future_dt - start_time).total_seconds() / 3600.0
            
            hour_col = f"hour_{future_dt.hour}"
            dow_col = f"dayofweek_{future_dt.dayofweek}"
            
            if hour_col in row_dict:
                row_dict[hour_col] = 1
            if dow_col in row_dict:
                row_dict[dow_col] = 1
                
            future_X = pd.DataFrame([row_dict])
            # Reorder columns to match X
            future_X = future_X[X.columns]
            
            pred_load = model.predict(future_X)[0]
            # Clip negative predictions
            pred_load = max(1.0, float(pred_load))
            
            # Calculate predicted consumption increment (kWh = kW * 1 hour)
            pred_kwh = pred_load * 1.0
            
            forecast_results.append({
                "forecastDate": future_dt.isoformat() + "Z",
                "predictedKwh": round(pred_kwh, 2),
                "predictedLoadKw": round(pred_load, 2)
            })
            
        return forecast_results, round(confidence_score * 100, 2), "ML Model (Linear Regression)"
        
    except Exception as e:
        print(f"ML training failed: {str(e)}. Falling back to simulation.")
        return generate_simulated_forecast(forecast_hours, f"ML calculation error. Fallback. Detail: {str(e)}")

def generate_simulated_forecast(forecast_hours=24, model_run_info="Base Profile Simulator"):
    """
    Generates a standard daily load profile using sine-wave patterns.
    Useful as a fallback or for new meters.
    """
    forecast_results = []
    base_dt = datetime.utcnow()
    
    # Simple profile template: higher usage during afternoon (peak), lower at night
    for h in range(1, forecast_hours + 1):
        future_dt = base_dt + timedelta(hours=h)
        hour = future_dt.hour
        
        # Sine wave peaked at 15:00 (3 PM)
        # Shift hour by 9 so that sine peaks at 15
        sine_val = np.sin((hour - 9) * 2 * np.pi / 24) # ranges -1 to 1
        
        # Add random noise
        noise = np.random.normal(0, 0.05)
        
        # Map to load (average 15 kW, range 5 kW to 25 kW)
        pred_load = 15.0 + 8.0 * sine_val + noise
        pred_load = max(2.0, float(pred_load))
        
        pred_kwh = pred_load * 1.0 # 1 hour
        
        forecast_results.append({
            "forecastDate": future_dt.isoformat() + "Z",
            "predictedKwh": round(pred_kwh, 2),
            "predictedLoadKw": round(pred_load, 2)
        })
        
    # Baseline confidence is moderate (e.g. 70%)
    return forecast_results, 70.0, model_run_info
