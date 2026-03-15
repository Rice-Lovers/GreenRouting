import boto3
import json
import os
import time
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()

class NovaClient:
    def __init__(self):
        # The 'bedrock-runtime' client is used for the Converse API
        self.bedrock = boto3.client(
            service_name='bedrock-runtime', 
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )
        # Fallback for self-healing (using the Nova Lite ID from your map)
        self.default_eval_model = "us.amazon.nova-lite-v1:0"

    def invoke_nova(self, model_id, prompt, image_base64=None, system_prompt="You are a helpful, eco-conscious AI assistant."):
        """
        Universal invoker using the Bedrock Converse API.
        Compatible with Nova, Claude, Llama, and Mistral.
        """
        # 1. Prepare standardized message content
        content = [{"text": prompt}]
        
        if image_base64:
            # Converse API handles image bytes directly
            content.insert(0, {
                "image": {
                    "format": "png", 
                    "source": {"bytes": image_base64}
                }
            })

        messages = [{"role": "user", "content": content}]
        system_blocks = [{"text": system_prompt}]

        # 2. Exponential Backoff (Retry Logic)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Standardized call for all model providers
                response = self.bedrock.converse(
                    modelId=model_id,
                    messages=messages,
                    system=system_blocks,
                    inferenceConfig={
                        "maxTokens": 1000,
                        "temperature": 0.7
                    }
                )
                
                # 3. Standardized Response Parsing
                # Converse API returns a clean dictionary regardless of provider
                output_message = response['output']['message']
                
                # Join text blocks (handles cases where models return reasoning + text)
                response_text = "".join([
                    block['text'] for block in output_message['content'] if 'text' in block
                ])
                
                return response_text

            except ClientError as e:
                error_code = e.response['Error']['Code']
                # Common in hackathons: retry if we hit request limits
                if error_code == 'ThrottlingException' and attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"Throttled. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                return f"AWS Bedrock Error ({model_id}): {str(e)}"
            except Exception as e:
                return f"Unexpected Client Error: {str(e)}"

    def self_healing_check(self, response_to_check, original_prompt):
        """
        Evaluates the quality of a response.
        If it returns 'FAILED', the main logic triggers a high-tier fallback.
        """
        eval_prompt = (
            f"Review this AI response for the prompt: '{original_prompt}'.\n"
            f"Response: {response_to_check}\n"
            "Does this accurately and fully answer the prompt? Reply ONLY with 'SUCCESS' or 'FAILED'."
        )
        # Use an efficient model for quick evaluation
        check = self.invoke_nova(self.default_eval_model, eval_prompt)
        return "SUCCESS" in check.upper()
