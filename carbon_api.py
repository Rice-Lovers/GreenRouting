import os
import requests
from dotenv import load_dotenv

# Load .env with override=True to ignore global system AWS/API variables
load_dotenv(override=True)

def get_carbon_data():
    """
    Fetches real-time carbon intensity for the Mid-Atlantic (us-east-1) grid
    and returns both the raw and normalized (0-100) values.
    """
    api_key = os.getenv("EMAPS_API_KEY")
    zone = "US-MIDA-PJM" # Defaults to Virginia grid

    # Energy Proxies (E) in kWh per request ---
    # Based on parameter scale: Eco (~3B-8B) vs Power (70B+)
    E_PROXIES = {
        "ECO": 0.0002,   # Small models
        "POWER": 0.0025  # Large models
    }
    
    if not api_key:
        print("❌ Error: EMAPS_API_KEY missing from .env")
        return 420, E_PROXIES  # Returns (raw, normalized) fallbacks
      
    url = f"https://api.electricitymaps.com/v3/carbon-intensity/latest?zone={zone}"
    headers = {"auth-token": api_key}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Electricity Maps v3 uses 'carbonIntensity' as the primary key
        raw_intensity = data.get('carbonIntensity', 420)
        
        # Standard normalization: (Current / 800) * 100
        # 0-800 gCO2eq/kWh is the standard range for the US-MIDA-PJM grid
        normalized = min((raw_intensity / 800) * 100, 100)
        
        return int(raw_intensity), E_PROXIES
        
    except requests.exceptions.HTTPError as e:
        # Specifically catches 400 (Bad Zone) or 401 (Bad Key) errors
        print(f"⚠️ API Client Error: {e}")
        return 0, 50
    except Exception as e:
        print(f"⚠️ General Carbon API Error: {e}")
        return 0, 50
