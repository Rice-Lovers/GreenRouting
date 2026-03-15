import sys
import os
import uuid
import base64

# --- THE FIX: Force Python to look in the current folder for imports ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# --- THE MULTI-AGENT REGISTRY ---
# Central source of truth for all models. 
# Ensure these IDs match the updated Bedrock Inference IDs.
MODEL_MAP = {
    # ECO TIER (Lite/Small)
    "nova_lite": "us.amazon.nova-lite-v1:0",
    "llama_lite": "us.meta.llama3-2-3b-instruct-v1:0",
    "claude_lite": "us.anthropic.claude-3-haiku-20240307-v1:0",
    "mistral_lite": "mistral.mistral-small-2402-v1:0",

    # POWER TIER (Pro/Large)
    "nova_pro": "us.amazon.nova-pro-v1:0",
    "llama_pro": "us.meta.llama3-1-70b-instruct-v1:0",
    "claude_pro": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    "mistral_pro": "mistral.mistral-large-2402-v1:0"
}

# Now we can safely import your local modules
try:
    from router import GreenRouter
    from nova_client import NovaClient # This is now our Universal Bedrock Client
    from carbon_api import get_carbon_data
    from database import save_green_log, ensure_table_exists
except ImportError as e:
    print(f"❌ Critical Import Error: {e}")
    sys.exit(1)

def run_green_route(user_prompt, image_path=None):
    """
    Orchestrates the Multi-Agent GreenRouting workflow.
    """
    # 1. Initialization
    router = GreenRouter()
    client = NovaClient()
    
    try:
        ensure_table_exists()
    except Exception as e:
        print(f"⚠️ DynamoDB Note: {e}")

    prompt_id = str(uuid.uuid4())[:8]
    image_b64 = None
    
    # 2. Handle Multimodal Input
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as f:
            image_b64 = f.read()

    # 3. Fetch Environmental Context
    try:
        carbon_score, raw_co2 = get_carbon_data()
        
        # Ensure raw_co2 is a number before processing
        if isinstance(raw_co2, str):
            raw_co2 = int(raw_co2) if raw_co2.isdigit() else 450
            
    except Exception as e:
        print(f"⚠️ Carbon API failed: {e}. Using neutral fallback.")
        carbon_score, raw_co2 = 0.5, 450 

    # 4. Multi-Agent Routing Decision
    # The router now returns a KEY from our MODEL_MAP (e.g., 'mistral_pro')
    selected_key, decision_reason = router.route_request(
        user_prompt, 
        raw_co2, 
        image_base64=image_b64
    )
    
    model_id = MODEL_MAP.get(selected_key, MODEL_MAP["nova_lite"])
    print(f"\n🌱 Grid Intensity: {raw_co2} gCO2/kWh")
    print(f"🤖 Decision: {decision_reason} -> Using {selected_key}")

    # 5. Execute AI Inference via Universal Converse API
    response = client.invoke_nova(model_id, user_prompt, image_base64=image_b64)

    # 6. Self-Healing Check
    # If a Lite model struggles with reasoning, we trigger a high-capacity fallback
    if "lite" in selected_key.lower():
        is_sufficient = client.self_healing_check(response, user_prompt)
        if not is_sufficient:
            print("🔄 Self-Healing Triggered: Moving to Intelligence-Tier (Claude Pro)...")
            selected_key = "claude_pro"
            model_id = MODEL_MAP[selected_key]
            response = client.invoke_nova(model_id, user_prompt, image_base64=image_b64)

    # 7. Metrics & Logging
    # Dynamic carbon savings based on model architecture
    carbon_saved = calculate_comparative_savings(selected_key)
    
    try:
        complexity = router.analyze_complexity(user_prompt, image_b64)
        save_green_log(prompt_id, selected_key, carbon_saved, complexity)
    except Exception as e:
        print(f"⚠️ Logging failed: {e}")
    
    # 8. Return UI-Compatible Data
    return {
        "model": selected_key.upper().replace("_", " "),
        "response": response,
        "carbon_saved": carbon_saved,
        "intensity": int(raw_co2) 
    }

def calculate_comparative_savings(model_key):
    """
    Estimates mg of CO2 saved compared to a baseline Pro run.
    """
    savings_map = {
        "nova_lite": 18.5,
        "llama_lite": 16.2,
        "claude_lite": 14.8,
        "mistral_lite": 12.0,
        "nova_pro": 5.5,
        "mistral_pro": 4.0,
        "llama_pro": 2.0,
        "claude_pro": 0.0 # Our baseline for maximum carbon cost
    }
    return savings_map.get(model_key.lower(), 0.0)

if __name__ == "__main__":
    test_prompt = "Compare the energy efficiency of small vs large language models."
    result = run_green_route(test_prompt)
    print(f"\n✅ Execution Finished")
    print(f"Final Model: {result['model']}")
    print(f"Impact Saved: {result['carbon_saved']}mg")
