import boto3
import json
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

class GreenRouter:
    def __init__(self):
        # Using Credentials from Mikhael_Dev_accessKeys.csv
        self.bedrock = boto3.client(
            service_name='bedrock-runtime', 
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )
        self.EMBED_MODEL = os.getenv("NOVA_EMBED_ID")
        self.LITE_MODEL = os.getenv("NOVA_LITE_ID")
        self.PRO_MODEL = os.getenv("NOVA_PRO_ID")
        self.threshold = float(os.getenv("COMPLEXITY_THRESHOLD", 0.65))

    def analyze_complexity(self, prompt: str, image_base64: str = None) -> float:
        """
        Calculates complexity. Images add a base complexity multiplier.
        """
        score = 0.0
        
        # 1. Base complexity for text length
        if prompt:
            score += min(len(prompt) / 500, 0.5)
            
        # 2. Add complexity for images
        if image_base64:
            # Vision tasks are inherently higher complexity
            score += 0.4 
            
        return round(min(score, 1.0), 2)

    def route_request(self, prompt: str, carbon_intensity: int, image_base64: str = None):
        """
        Routes based on Complexity and Carbon Grid Health.
        """
        complexity = self.analyze_complexity(prompt, image_base64)
        
        # LOGIC: If grid is dirty OR complexity is high, optimize for eco-lite
        if carbon_intensity > 80:
            return self.LITE_MODEL, "Grid High Intensity: Forcing Nova Lite"
        
        if complexity < self.threshold:
            return self.LITE_MODEL, f"Low Complexity ({complexity}): Using Nova Lite"
        
        return self.PRO_MODEL, f"High Complexity ({complexity}): Using Nova Pro"
