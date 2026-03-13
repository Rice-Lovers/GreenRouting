import boto3
import json
import os
import time
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()

class NovaClient:
    def __init__(self):
        self.bedrock = boto3.client(
            service_name='bedrock-runtime', 
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )

    def invoke_nova(self, model_id, prompt, image_base64=None, system_prompt="You are a helpful, eco-conscious AI assistant."):
        """
        Executes a call to Amazon Nova with Exponential Backoff and Thinking-Block handling.
        """
        content = [{"text": prompt}]
        if image_base64:
            content.insert(0, {
                "image": {
                    "format": "png", 
                    "source": {"bytes": image_base64}
                }
            })

        body = json.dumps({
            "messages": [{"role": "user", "content": content}],
            "system": [{"text": system_prompt}],
            "inferenceConfig": {
                "max_new_tokens": 1000,
                "temperature": 0.7
            }
        })

        # --- RECOMENDATION 2: Exponential Backoff (Retry Logic) ---
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.bedrock.invoke_model(
                    body=body,
                    modelId=model_id,
                    accept="application/json",
                    contentType="application/json"
                )
                
                response_body = json.loads(response.get("body").read())
                
                # --- RECOMMENDATION 1: Handle 'Thinking' vs 'Text' ---
                # Nova 2 Lite 'Extended Thinking' results can be structured differently
                output_content = response_body['output']['message']['content']
                
                # Extract only the 'text' parts, ignoring the 'thinking' blocks for the final UI
                text_response = " ".join([item['text'] for item in output_content if 'text' in item])
                return text_response

            except ClientError as e:
                if e.response['Error']['Code'] == 'ThrottlingException' and attempt < max_retries - 1:
                    time.sleep(2 ** attempt) # Wait 1s, then 2s, then 4s
                    continue
                return f"AWS Error: {str(e)}"
            except Exception as e:
                return f"Unexpected Error: {str(e)}"

    def self_healing_check(self, response_to_check, original_prompt):
        """
        --- RECOMMENDATION 3: Clean Self-Healing Check ---
        Uses a stricter prompt to ensure a clear binary decision.
        """
        eval_prompt = (
            f"Review this AI response for the prompt: '{original_prompt}'.\n"
            f"Response: {response_to_check}\n"
            "Does this accurately and fully answer the prompt? reply with 'SUCCESS' or 'FAILED'."
        )
        # Use Nova Lite for the quick evaluation
        check = self.invoke_nova(os.getenv("NOVA_LITE_ID"), eval_prompt)
        return "SUCCESS" in check.upper()
