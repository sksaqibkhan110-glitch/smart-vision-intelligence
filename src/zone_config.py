import json
import os

ZONE_FILE = "data/zone_config.json"

DEFAULT_ZONES = {
    "zone1_caution": {"x_min": 0.0, "x_max": 0.40},
    "zone2_critical": {"x_min": 0.60, "x_max": 1.0}
}

def load_zones():
    if os.path.exists(ZONE_FILE):
        try:
            with open(ZONE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_ZONES

def save_zones(caution_max, critical_min):
    os.makedirs("data", exist_ok=True)
    config = {
        "zone1_caution": {"x_min": 0.0, "x_max": float(caution_max)},
        "zone2_critical": {"x_min": float(critical_min), "x_max": 1.0}
    }
    with open(ZONE_FILE, "w") as f:
        json.dump(config, f, indent=4)
    return config