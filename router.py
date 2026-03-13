import boto3
import json
import numpy as np
from typing import Tuple

class GreenRouter:
    def __init__(self, region="us-east-1"):
        # Initialize Bedrock client
        self.bedrock = boto3.client(service_name='bedrock-runtime', region_name=region)
        
        # Model IDs for Amazon Nova
        self.EMBED_MODEL = "amazon.nova-embeddings-v1" #
        self.LITE_MODEL = "us.amazon.nova-lite-v1:0"   #
        self.PRO_MODEL = "us.amazon.nova-pro-v1:0"     #

        # Complexity threshold: 0.0 (Simple) to 1.0 (Complex)
        # Higher means it's harder to trigger Nova Pro
        self.complexity_threshold = 0.65

    def _get_embedding(self, text: str) -> np.ndarray:
        """Converts text to a vector using Nova Multimodal Embeddings"""
        body = json.dumps({"inputText": text})
        try:
            response = self.bedrock.invoke_model(
                body=body,
                modelId=self.EMBED_MODEL,
                accept="application/json",
                contentType="application/json"
            )
            response_body = json.loads(response.get("body").read())
            return np.array(response_body.get("embedding"))
        except Exception as e:
            print(f"Embedding Error: {e}")
            return np.zeros(1024) # Default fallback

    def analyze_complexity(self, user_prompt: str) -> float:
        """
        Calculates complexity based on prompt length, keyword density, 
        and semantic vector magnitude.
        """
        # 1. Simple heuristic: Length and structure
        length_score = min(len(user_prompt) / 500, 1.0) 
        
        # 2. Semantic Analysis: Use embeddings to detect 'reasoning' intent
        # For the hackathon, we look for 'weight' in the embedding vector
        embedding = self._get_embedding(user_prompt)
        vector_magnitude = np.linalg.norm(embedding)
        
        # Normalize scores to a 0.0 - 1.0 range
        complexity = (length_score * 0.4) + (min(vector_magnitude / 15, 1.0) * 0.6)
        return round(complexity, 2)

    def route_request(self, user_prompt: str, carbon_intensity: int) -> Tuple[str, str]:
        """
        Decision Engine: Routes based on Task Complexity AND Grid Health.
        carbon_intensity: 0 (Green) to 100 (Dirty)
        """
        complexity = self.analyze_complexity(user_prompt)
        
        # LOGIC:
        # If the grid is very 'dirty' (>80), force Nova Lite regardless of complexity.
        # Otherwise, use complexity threshold.
        if carbon_intensity > 80:
            decision = "Grid Alert: Routing to Eco-Friendly Nova Lite"
            selected_model = self.LITE_MODEL
        elif complexity < self.complexity_threshold:
            decision = f"Low Complexity ({complexity}): Routing to Nova Lite"
            selected_model = self.LITE_MODEL
        else:
            decision = f"High Complexity ({complexity}): Routing to Nova Pro"
            selected_model = self.PRO_MODEL
            
        return selected_model, decision

# Quick Test Logic
if __name__ == "__main__":
    router = GreenRouter()
    # Mock carbon intensity (retrieved by Teammate B's carbon_api.py)
    mock_carbon = 45 
    
    prompt = "Write a simple 'Hello World' in Python."
    model, reason = router.route_request(prompt, mock_carbon)
    print(f"Prompt: {prompt}\nResult: {reason}\n")

    complex_prompt = "Explain the quantum entanglement theory and its relation to computing."
    model, reason = router.route_request(complex_prompt, mock_carbon)
    print(f"Prompt: {complex_prompt}\nResult: {reason}")
