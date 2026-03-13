import uuid
import base64
from router import GreenRouter
from nova_client import NovaClient
from carbon_api import get_carbon_data
from database import save_green_log, ensure_table_exists

def run_green_route(user_prompt, image_path=None):
    """
    Orchestrates the full GreenRouting workflow.
    """
    # 1. Setup & Initialization
    router = GreenRouter()
    client = NovaClient()
    ensure_table_exists() # Ensure AWS environment is ready
    
    prompt_id = str(uuid.uuid4())[:8]
    image_b64 = None
    
    # 2. Handle Multimodal Input if image exists
    if image_path:
        with open(image_path, "rb") as f:
            image_b64 = f.read() # nova_client expects bytes from router logic

    # 3. Fetch Environmental Context
    # Returns (normalized_score, raw_gCO2)
    carbon_score, raw_co2 = get_carbon_data()
    print(f"Current Grid Carbon Intensity: {raw_co2} gCO2/kWh (Score: {carbon_score})")

    # 4. Routing Decision
    # Decides between Nova Lite (Eco) and Nova Pro (Reasoning)
    selected_model, decision_reason = router.route_request(
        user_prompt, 
        carbon_score, 
        image_base64=image_b64
    )
    print(f"Decision: {decision_reason}")

    # 5. Execute AI Inference
    response = client.invoke_nova(selected_model, user_prompt, image_base64=image_b64)

    # 6. 10/10 Feature: Self-Healing Check
    # If using Lite, verify if the answer is sufficient
    if "lite" in selected_model:
        is_sufficient = client.self_healing_check(response, user_prompt)
        if not is_sufficient:
            print("Self-Healing Triggered: Lite response insufficient. Re-routing to Nova Pro...")
            selected_model = router.PRO_MODEL
            response = client.invoke_nova(selected_model, user_prompt, image_base64=image_b64)

    # 7. Calculate & Log Savings
    # Simple heuristic: Pro uses ~2x the carbon of Lite for the same task
    carbon_saved = 15.5 if "lite" in selected_model else 0.0 
    save_green_log(prompt_id, selected_model, carbon_saved, router.analyze_complexity(user_prompt, image_b64))
    
    return {
        "model": selected_model,
        "response": response,
        "carbon_saved": carbon_saved,
        "intensity": raw_co2
    }

if __name__ == "__main__":
    # Test Case 1: Simple Greeting (Should route to Nova Lite)
    print("--- Test 1: Simple Task ---")
    res1 = run_green_route("Hi there! How can you help me save energy?")
    print(f"Model Used: {res1['model']}\nResponse: {res1['response']}\n")

    # Test Case 2: Complex Multimodal (Should route to Nova Pro)
    # Note: Ensure you have a 'test_image.png' in your folder to run this
    # print("--- Test 2: Multimodal Task ---")
    # res2 = run_green_route("Analyze the data in this chart.", "test_image.png")
    # print(f"Model Used: {res2['model']}\nResponse: {res2['response']}")
