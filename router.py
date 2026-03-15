import boto3
import json
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

class GreenRouter:
    def __init__(self):
        # Initializing Bedrock Client
        self.bedrock = boto3.client(
            service_name='bedrock-runtime', 
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )
        # Threshold for deciding between Lite and Pro tiers
        self.threshold = float(os.getenv("COMPLEXITY_THRESHOLD", 0.60))

    def analyze_complexity(self, prompt: str, image_base64: str = None) -> float:
        """
        Calculates complexity. Detects coding tasks to increase reasoning priority.
        """
        score = 0.0
        
        if prompt:
            p_lower = prompt.lower()
            # 1. Base complexity for text length
            score += min(len(prompt) / 1000, 0.5)
            
            # 2. Intent-based adjustments (The 'Logic' boost)
            coding_keywords = ["html", "css", "python", "javascript", "code", "script", "program", "function"]
            if any(kw in p_lower for kw in coding_keywords):
                score += 0.35  # Coding is intellectually heavy, even if the prompt is short
                
            # 3. Filler reduction
            fillers = ["hello", "hi", "thanks", "thank you", "bye", "ok", "hey"]
            if any(filler == p_lower.strip() for filler in fillers):
                score = 0.05  # Reset to minimal for greetings
            
        if image_base64:
            score += 0.45 
            
        return round(min(score, 1.0), 2)

    def route_request(self, prompt: str, carbon_intensity: int, image_base64: str = None):
        """
        Multi-Agent Routing Logic:
        Ensures model diversity (Claude, Mistral, Llama) across different carbon zones.
        """
        complexity = self.analyze_complexity(prompt, image_base64)
        
        # --- THE GATEKEEPER ---
        # Extreme efficiency for conversational filler
        if complexity < 0.12:
            return "nova_lite", f"Routine Filler ({complexity}): Using Nova Lite"

        # --- ZONE 1: CRITICAL CARBON (> 450 gCO2) ---
        # Strategy: Use Llama and Nova for the best efficiency/performance ratio.
        if carbon_intensity > 450:
            if complexity > 0.7:
                return "llama_pro", "CRITICAL GRID: High complexity routed to Llama 3.1 70B"
            return "llama_lite", f"CRITICAL GRID ({carbon_intensity}): Using Llama 3.2 3B"

        # --- ZONE 2: BALANCED GRID (250 - 450 gCO2) ---
        # Strategy: Distribute load to Claude and Mistral.
        if 250 <= carbon_intensity <= 450:
            # Coding or high complexity gets the reasoning powerhouse
            if complexity > 0.4:
                return "claude_lite", "BALANCED GRID: Logic task routed to Claude Haiku"
            # General tasks get Mistral's balanced efficiency
            return "mistral_lite", "BALANCED GRID: General reasoning via Mistral Small"

        # --- ZONE 3: CLEAN GRID (< 250 gCO2) ---
        # Strategy: Maximum Intelligence. Unleash the flagship models.
        if carbon_intensity < 250:
            if complexity > self.threshold or image_base64:
                return "claude_pro", "CLEAN GRID: Peak Reasoning Tier (Claude 3.5 Sonnet)"
            if complexity > 0.3:
                return "mistral_pro", "CLEAN GRID: High-performance Mistral Large"
            return "nova_pro", "CLEAN GRID: Standard reasoning via Nova Pro"

        # Default Fallback
        return "nova_lite", "Defaulting to Eco-Tier"
