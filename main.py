import sys
import os
import uuid
import base64

# --- THE FIX: Force Python to look in the current folder for imports ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Now we can safely import your local modules
try:
    from router import GreenRouter
    from nova_client import NovaClient
    from carbon_api import get_carbon_data
    from database import save_green_log, ensure_table_exists
except ImportError as e:
    print(f"❌ Critical Import Error: {e}")
    print("Ensure all .py files (router, nova_client, carbon_api, database) are in the same folder.")
    sys.exit(1)

def run_green_route(user_prompt, image_path=None):
    """
    Orchestrates the full GreenRouting workflow.
    Ensures data types are UI-compatible.
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
        
        # --- FIX: Ensure raw_co2 is a number before it leaves main.py ---
        if isinstance(raw_co2, str):
            # If it's a string like "450", convert it. If "Unknown", use fallback.
            raw_co2 = int(raw_co2) if raw_co2.isdigit() else 450
            
        print(f"\n🌱 Grid Intensity: {raw_co2} gCO2/kWh (Score: {carbon_score})")
    except Exception as e:
        print(f"⚠️ Carbon API failed: {e}. Using neutral fallback.")
        carbon_score, raw_co2 = 0.5, 450 # Use a numeric fallback

    # 4. Routing Decision
    selected_model, decision_reason = router.route_request(
        user_prompt, 
        carbon_score, 
        image_base64=image_b64
    )
    print(f"🤖 Decision: {decision_reason}")

    # 5. Execute AI Inference
    response = client.invoke_nova(selected_model, user_prompt, image_base64=image_b64)

    # 6. Self-Healing Check
    if "lite" in selected_model.lower():
        is_sufficient = client.self_healing_check(response, user_prompt)
        if not is_sufficient:
            print("🔄 Self-Healing Triggered...")
            selected_model = "us.amazon.nova-pro-v1:0"
            response = client.invoke_nova(selected_model, user_prompt, image_base64=image_b64)

    # 7. Metrics & Logging
    carbon_saved = 15.5 if "lite" in selected_model.lower() else 0.0 
    
    try:
        complexity = router.analyze_complexity(user_prompt, image_b64)
        save_green_log(prompt_id, selected_model, carbon_saved, complexity)
    except Exception as e:
        print(f"⚠️ Logging failed: {e}")
    
    # --- FINAL RETURN: UI SAFETY CHECK ---
    return {
        "model": selected_model,
        "response": response,
        "carbon_saved": carbon_saved,
        "intensity": int(raw_co2) # Force integer here
    }

if __name__ == "__main__":
    test_prompt = "How can AI help in reducing the carbon footprint of data centers?"
    result = run_green_route(test_prompt)
    print(f"Result for UI check: {result['intensity']}")
