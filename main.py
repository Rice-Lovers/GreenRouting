import sys
import os
import uuid
import base64
from datetime import datetime
from rapidfuzz import process, fuzz # Ensure you: pip install rapidfuzz

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
    from database import save_green_log, ensure_table_exists, get_recent_logs
except ImportError as e:
    print(f"❌ Critical Import Error: {e}")
    sys.exit(1)

def check_semantic_cache(user_prompt):
    """
    Checks historical logs for a 90% match.
    Returns the cached response if found, saving 100% of inference energy.
    """
    try:
        recent_logs = get_recent_logs(limit=50) # Fetch from DynamoDB via database.py
        if not recent_logs:
            return None

        # Extract only the prompts for matching
        past_prompts = [log['prompt_text'] for log in recent_logs]
        
        # Fuzzy match logic
        match = process.extractOne(user_prompt, past_prompts, scorer=fuzz.token_set_ratio)
        
        if match and match[1] > 90: # 90% Similarity Threshold
            matched_text = match[0]
            for log in recent_logs:
                if log['prompt_text'] == matched_text:
                    print(f"♻️ Semantic Cache Hit ({match[1]}%): Reusing answer.")
                    return log['response_text']
    except Exception as e:
        print(f"⚠️ Cache Check Failed: {e}")
    return None

def calculate_sci_score(model_key, grid_intensity, e_proxies):
    """
    Implements SCI = ((E * I) + M) / R
    """
    tier = "POWER" if "pro" in model_key.lower() else "ECO"
    e = e_proxies.get(tier, 0.0025)
    i = grid_intensity
    operational = e * i
    
    # Embodied Carbon (M)
    m = 0.0075 if tier == "ECO" else 0.0850
    if model_key == "SEMANTIC_CACHE":
        return 0.0001 # Minimal disk-read energy only
        
    sci_total = operational + m
    return round(sci_total * 1000, 4)

# --- CRITICAL FIX: Added session_id parameter here ---
def run_green_route(user_prompt, image_path=None, session_id="GLOBAL"):
    """
    Orchestrates workflow with Cache-First logic, SCI Math, and Session Isolation.
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

    # 1. Semantic Cache Check
    cached_response = check_semantic_cache(user_prompt)
    
    # 2. Fetch Environmental Context
    try:
        raw_co2, e_proxies = get_carbon_data()
        raw_co2 = int(raw_co2) if str(raw_co2).isdigit() else 450
    except Exception as e:
        raw_co2, e_proxies = 450, {"ECO": 0.0002, "POWER": 0.0025}

    # 3. IF CACHE HIT: Bypass Bedrock
    if cached_response:
        current_sci = calculate_sci_score("SEMANTIC_CACHE", raw_co2, e_proxies)
        baseline_sci = calculate_sci_score("claude_pro", raw_co2, e_proxies)
        carbon_saved = round(baseline_sci - current_sci, 2)
        
        # Log with session_id
        save_green_log(prompt_id, "SEMANTIC_CACHE", carbon_saved, 0.05, user_prompt, cached_response, session_id=session_id)
        
        return {
            "model": "♻️ SEMANTIC CACHE",
            "response": cached_response,
            "carbon_saved": carbon_saved,
            "intensity": raw_co2,
            "sci_score": current_sci
        }

    # 4. Routing & Inference (Standard Path)
    selected_key, decision_reason = router.route_request(user_prompt, raw_co2, image_b64)
    model_id = MODEL_MAP.get(selected_key, MODEL_MAP["nova_lite"])
    
    response = client.invoke_nova(model_id, user_prompt, image_base64=image_b64)

    # 5. Self-Healing
    if "lite" in selected_key.lower():
        if not client.self_healing_check(response, user_prompt):
            selected_key = "claude_pro"
            model_id = MODEL_MAP[selected_key]
            response = client.invoke_nova(model_id, user_prompt, image_base64=image_b64)

    # 6. Final Metrics
    current_sci = calculate_sci_score(selected_key, raw_co2, e_proxies)
    baseline_sci = calculate_sci_score("claude_pro", raw_co2, e_proxies)
    carbon_saved = max(0, round(baseline_sci - current_sci, 2))
    complexity = router.analyze_complexity(user_prompt, image_b64)
    
    # 7. Log to DB with session_id
    save_green_log(prompt_id, selected_key, carbon_saved, complexity, user_prompt, response, session_id=session_id)
    
    return {
        "model": selected_key.upper().replace("_", " "),
        "response": response,
        "carbon_saved": carbon_saved,
        "intensity": int(raw_co2),
        "sci_score": current_sci
    }
