import os #allows script to interact with OS and read environmental variables
import requests #library for http requests
from dotenv import load_dotenv 

load_dotenv() #loads secret keys from .env file in encrypted text

def get_carbon_data():
    """
    Fetches intensity and returns both raw and normalized values.
    Returns: (normalized_score, raw_gCO2)
    """
    api_key = os.getenv("EMAPS_API_KEY")
    if not api_key:
        return 50, 400 # Fallback values
    zone = "US-PJM"  # Specifies Power Grid Zone = Virginia / us-east-1 grid
    url = f"https://api.electricitymaps.com/v3/carbon-intensity/latest?zone={zone}"
    #url constructs the specific web address needed to ask Electricity Maps for the latest carbon data for that zone.
    
    headers = {"auth-token": api_key} #prepares password for for API access
    
    try:
        response = requests.get(url, headers=headers) #sends request to the server
        response.raise_for_status() #checks if request was successful
        data = response.json() 
        raw_intensity = data.get('carbonIntensity', 0)
        
        # Assume 0-800 gCO2eq/kWh range for US-PJM
        # Normalize: (Current / Max Expected) * 100 
        # 0 = Very Green, 100 = Very Dirty
        
        normalized = min((raw_intensity / 800) * 100, 100)
        return int(normalized), raw_intensity
    except Exception as e:
        print(f"Carbon API Error: {e}")
        return 50, 400  # Fallback to mid-range intensity
