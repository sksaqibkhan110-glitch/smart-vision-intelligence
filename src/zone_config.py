import json
import os

CONFIG_FILE = "data/zones.json"

DEFAULT_ZONES = {
    "zone1_caution": {
        "x_min": 0.0,
        "x_max": 0.40,
        "polygon": []
    },
    "zone2_critical": {
        "x_min": 0.60,
        "x_max": 1.0,
        "polygon": []
    }
}

def load_zones():
    if not os.path.exists(CONFIG_FILE):
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_ZONES, f, indent=4)
        return DEFAULT_ZONES
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_ZONES

def save_polygon_zones(zone1_poly, zone2_poly):
    data = load_zones()
    if zone1_poly:
        data["zone1_caution"]["polygon"] = zone1_poly
    if zone2_poly:
        data["zone2_critical"]["polygon"] = zone2_poly
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)
    return data

def save_zones(caution_max, critical_min):
    data = load_zones()
    data["zone1_caution"]["x_max"] = caution_max
    data["zone2_critical"]["x_min"] = critical_min
    # Clear previous polygon so linear sliders take immediate visual control
    data["zone1_caution"]["polygon"] = []
    data["zone2_critical"]["polygon"] = []
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)
    return data