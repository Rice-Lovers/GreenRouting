import boto3
import json
import os
import time
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()

class NovaClient:
    def __init__(self):
        # Initialize the Bedrock client using your credentials from .env
        self.bedrock = boto3.client(
            service_name='bedrock-runtime', 
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )
        self.lite_model = os.getenv("NOVA_LITE_ID")
        self.pro_model = os.getenv("NOVA_PRO_ID")

    def invoke_nova(self, model_id, prompt, image_base64=None, system_prompt="You are a helpful, eco-conscious AI assistant."):
        """
        Executes a call to Amazon Nova with Image support, Exponential Backoff, 
        and Thinking-Block handling.
        """
        # 1. Prepare Multimodal Content
        content = [{"text": prompt}]
        
        if image_base64:
            # Insert image block at the start of the content list
            content.insert(0, {
                "image": {
                    "format": "png", 
                    "source": {"bytes": image_base64} # Nova accepts base64 bytes
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

        # 2. Exponential Backoff (Retry Logic)
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
                
                # 3. Handle 'Thinking' vs 'Text' Blocks
                # Nova 2 Lite output can include multiple content blocks
                output_content = response_body['output']['message']['content']
                
                # Filter out 'thinking' blocks and only join 'text' blocks for the user
                text_response = " ".join([item['text'] for item in output_content if 'text' in item])
                return text_response

            except ClientError as e:
                # Retry on Throttling (common during hackathons)
                if e.response['Error']['Code'] == 'ThrottlingException' and attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"Throttled. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                return f"AWS Error: {str(e)}"
            except Exception as e:
                return f"Unexpected Error: {str(e)}"

    def self_healing_check(self, response_to_check, original_prompt):
        """
        Uses Nova Lite to evaluate the quality of a response.
        If it returns 'FAILED', the main logic should trigger a Nova Pro fallback.
        """
        eval_prompt = (
            f"Review this AI response for the prompt: '{original_prompt}'.\n"
            f"Response: {response_to_check}\n"
            "Does this accurately and fully answer the prompt? Reply ONLY with 'SUCCESS' or 'FAILED'."
        )
        # Use Nova Lite for cost-effective evaluation
        check = self.invoke_nova(self.lite_model, eval_prompt)
        return "SUCCESS" in check.upper()
