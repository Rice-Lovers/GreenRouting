import sys
import os
import uuid
import base64
from datetime import datetime

# --- THE FIX: Force Python to look in the current folder for imports ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# --- THE MULTI-AGENT REGISTRY ---
MODEL_MAP = {
    "nova_lite": "us.amazon.nova-lite-v1:0",
    "llama_lite": "us.meta.llama3-2-3b-instruct-v1:0",
    "claude_lite": "us.anthropic.claude-3-haiku-20240307-v1:0",
    "mistral_lite": "mistral.mistral-small-2402-v1:0",
    "nova_pro": "us.amazon.nova-pro-v1:0",
    "llama_pro": "us.meta.llama3-1-70b-instruct-v1:0",
    "claude_pro": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    "mistral_pro": "mistral.mistral-large-2402-v1:0"
}

# Now we can safely import local modules
try:
    from router import GreenRouter
    from nova_client import NovaClient 
    from carbon_api import get_carbon_data
    from database import save_green_log, ensure_table_exists
except ImportError as e:
    print(f"❌ Critical Import Error: {e}")
    sys.exit(1)

def calculate_sci_score(model_key, grid_intensity, e_proxies):
    """
    Implements the SCI Formula: SCI = ((E * I) + M) / R
    E = Energy per request (kWh)
    I = Grid Intensity (gCO2eq/kWh)
    M = Embodied Carbon (gCO2eq)
    R = Functional Unit (1 Request)
    """
    # 1. Operational Emissions (E * I)
    tier = "POWER" if "pro" in model_key.lower() else "ECO"
    e = e_proxies.get(tier, 0.0025)  # kWh/request
    i = grid_intensity  # gCO2/kWh
    operational_emissions = e * i
    
    # 2. Embodied Carbon (M)
    # Assume 1,500kg CO2eq per server / 4 year lifespan
    # Amortized to hourly: ~42.8g/hour per server
    # AI models use large GPU clusters. We estimate M per request:
    # Eco models use ~1/16th of a server's resources for ~500ms
    # Power models use ~1/4th of a server's resources for ~2000ms
    if tier == "ECO":
        m = 0.0075  # Estimated gCO2 per request for Lite models
    else:
        m = 0.0850  # Estimated gCO2 per request for Pro models
        
    # 3. SCI Calculation (R = 1 request)
    sci_total = operational_emissions + m
    return round(sci_total * 1000, 4) # Returning in milligrams (mg)

def run_green_route(user_prompt, image_path=None):
    """
    Orchestrates the Multi-Agent GreenRouting workflow with SCI Math.
    """
    router = GreenRouter()
    client = NovaClient()
    
    try:
        ensure_table_exists()
    except Exception as e:
        print(f"⚠️ DynamoDB Note: {e}")

    prompt_id = str(uuid.uuid4())[:8]
    image_b64 = None
    
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as f:
            image_b64 = f.read()

    # 3. Fetch Environmental Context
    try:
        raw_co2, e_proxies = get_carbon_data()
        if isinstance(raw_co2, str):
            raw_co2 = int(raw_co2) if raw_co2.isdigit() else 450
    except Exception as e:
        print(f"⚠️ Carbon API failed: {e}. Using fallback.")
        raw_co2, e_proxies = 450, {"ECO": 0.0002, "POWER": 0.0025}

    # 4. Multi-Agent Routing Decision
    selected_key, decision_reason = router.route_request(
        user_prompt, 
        raw_co2, 
        image_base64=image_b64
    )
    
    model_id = MODEL_MAP.get(selected_key, MODEL_MAP["nova_lite"])
    print(f"\n🌱 Grid Intensity: {raw_co2} gCO2/kWh")

    # 5. Execute AI Inference
    response = client.invoke_nova(model_id, user_prompt, image_base64=image_b64)

    # 6. Self-Healing
    if "lite" in selected_key.lower():
        is_sufficient = client.self_healing_check(response, user_prompt)
        if not is_sufficient:
            print("🔄 Self-Healing Triggered...")
            selected_key = "claude_pro"
            model_id = MODEL_MAP[selected_key]
            response = client.invoke_nova(model_id, user_prompt, image_base64=image_b64)

    # 7. SCI Metrics (The scientific approach)
    # Calculate SCI for the chosen model vs. a baseline Pro model
    current_sci = calculate_sci_score(selected_key, raw_co2, e_proxies)
    baseline_sci = calculate_sci_score("claude_pro", raw_co2, e_proxies)
    
    # Carbon saved is the delta between baseline and selected
    carbon_saved = max(0, round(baseline_sci - current_sci, 2))
    
    try:
        complexity = router.analyze_complexity(user_prompt, image_b64)
        save_green_log(prompt_id, selected_key, carbon_saved, complexity)
    except Exception as e:
        print(f"⚠️ Logging failed: {e}")
    
    return {
        "model": selected_key.upper().replace("_", " "),
        "response": response,
        "carbon_saved": carbon_saved,
        "intensity": int(raw_co2),
        "sci_score": current_sci # New field for UI
    }

if __name__ == "__main__":
    test_prompt = "How does embodied carbon impact AI infrastructure?"
    result = run_green_route(test_prompt)
    print(f"\n✅ SCI Execution Finished")
    print(f"SCI Score (Total Footprint): {result['sci_score']} mg")
    print(f"Carbon Avoided (vs Baseline): {result['carbon_saved']} mg")
