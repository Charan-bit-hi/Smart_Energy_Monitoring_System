import time
import requests
import random
import math
from datetime import datetime

API_URL = "http://localhost:8091/api/readings"

# Default meters matching the seeded DB
METERS = [
    {
        "meterId": "mtr_detroit_hvac",
        "label": "Detroit Main Plant HVAC",
        "deviceToken": "token_det_hvac_01",
        "baseLoad": 20.0,      # kW
        "peakVariation": 8.0,  # kW
        "energyAccumulator": 12450.0 # Start baseline kWh
    },
    {
        "meterId": "mtr_detroit_assembly",
        "label": "Assembly Line B Power Meter",
        "deviceToken": "token_det_asm_02",
        "baseLoad": 35.0,
        "peakVariation": 12.0,
        "energyAccumulator": 48900.0
    },
    {
        "meterId": "mtr_chicago_light",
        "label": "Warehouse Lighting Meter",
        "deviceToken": "token_chi_lgt_01",
        "baseLoad": 8.0,
        "peakVariation": 3.0,
        "energyAccumulator": 3100.0
    }
]

def simulate():
    print("[INFO] Starting Smart Meter IoT Simulator...")
    print("Press Ctrl+C to terminate.")
    
    interval_seconds = 5 # send readings every 5 seconds
    interval_hours = interval_seconds / 3600.0
    
    step_count = 0
    
    while True:
        step_count += 1
        current_time = datetime.utcnow()
        # Normal UTC hour decimal for cyclical sine wave variation
        hour_decimal = current_time.hour + current_time.minute / 60.0 + current_time.second / 3600.0
        
        print(f"\n--- [Telemetry Cycle #{step_count}] ---")
        
        for m in METERS:
            # 1. Calculate realistic load with sine wave peaking at 15:00 (3 PM)
            # Sine wave oscillates between -1 and 1
            time_factor = math.sin((hour_decimal - 9.0) * 2.0 * math.pi / 24.0)
            
            # Normal power draw
            load = m["baseLoad"] + m["peakVariation"] * time_factor + random.uniform(-1.5, 1.5)
            
            # 2. Occasional anomaly injections to test the Alert Engine
            voltage = random.uniform(216.0, 224.0) # standard 220V grid
            
            # Inject voltage anomaly once in 20 cycles
            if step_count % 20 == 0 and m["meterId"] == "mtr_detroit_hvac":
                # Undervoltage spike
                voltage = 195.5
                print(f"[ANOMALY INJECTED] Under-voltage grid surge simulated on {m['label']}!")
            elif step_count % 25 == 0 and m["meterId"] == "mtr_chicago_light":
                # Over-voltage spike
                voltage = 254.2
                print(f"[ANOMALY INJECTED] Over-voltage spike simulated on {m['label']}!")
                
            # Inject load threshold breach (exceed 50 kW) once in 30 cycles
            if step_count % 30 == 0 and m["meterId"] == "mtr_detroit_assembly":
                load = 54.8
                print(f"[ANOMALY INJECTED] Critical load peak load spike simulated on {m['label']}!")

            # Ensure load remains positive
            load = max(0.5, load)
            
            # Calculate current (Amps) = (kW * 1000) / V
            current = (load * 1000.0) / voltage
            
            # Increment cumulative energy
            energy_increment = load * interval_hours
            m["energyAccumulator"] += energy_increment
            
            # Format payload
            payload = {
                "meterId": m["meterId"],
                "voltage": round(voltage, 2),
                "current": round(current, 2),
                "powerKw": round(load, 2),
                "energyKwh": round(m["energyAccumulator"], 4),
                "timestamp": current_time.isoformat() + "Z"
            }
            
            # Setup headers with Authentication token
            headers = {
                "X-Meter-Token": m["deviceToken"]
            }
            
            try:
                response = requests.post(API_URL, json=payload, headers=headers)
                if response.status_code == 201:
                    print(f"[SUCCESS] {m['label']}: Posted - {payload['powerKw']} kW, {payload['voltage']}V, Total: {payload['energyKwh']:.2f} kWh")
                else:
                    print(f"[ERROR] {m['label']}: Ingestion error - Code {response.status_code}: {response.text}")
            except Exception as e:
                print(f"[WARNING] {m['label']}: Connection failed - {str(e)}")
                
        time.sleep(interval_seconds)

if __name__ == "__main__":
    try:
        simulate()
    except KeyboardInterrupt:
        print("\n[INFO] IoT Simulator terminated.")
