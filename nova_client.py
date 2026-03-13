import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

class NovaClient:
    def __init__(self):
        self.bedrock = boto3.client(
            service_name='bedrock-runtime', 
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )

    def invoke_nova(self, model_id, prompt, system_prompt="You are a helpful, eco-conscious AI assistant."):
        """
        Executes a call to the specified Amazon Nova model.
        """
        # Base configuration for Nova 2 models
        inf_params = {
            "max_new_tokens": 1000,
            "top_p": 0.9,
            "top_k": 50,
            "temperature": 0.7
        }

        # For Nova 2 Lite, we can enable 'Extended Thinking' for better reasoning
        if "lite" in model_id:
            # Setting thinking to 'low' for everyday tasks to save compute
            inf_params["thinking"] = {"type": "enabled", "budget_tokens": 1024}

        body = json.dumps({
            "messages": [{"role": "user", "content": [{"text": prompt}]}],
            "system": [{"text": system_prompt}],
            "inferenceConfig": inf_params
        })

        try:
            response = self.bedrock.invoke_model(
                body=body,
                modelId=model_id,
                accept="application/json",
                contentType="application/json"
            )
            
            response_body = json.loads(response.get("body").read())
            # Extract text from Nova's multimodal output structure
            return response_body['output']['message']['content'][0]['text']
            
        except Exception as e:
            return f"Error invoking {model_id}: {str(e)}"

    def self_healing_check(self, lite_response, original_prompt):
        """
        A 10/10 feature: Use Nova 2 Lite to evaluate if its own answer was sufficient.
        If it detects failure, it signals the router to upgrade to Nova Pro.
        """
        eval_prompt = f"Does this answer accurately fulfill the prompt: '{original_prompt}'? Answer only YES or NO. Answer: {lite_response}"
        check = self.invoke_nova("us.amazon.nova-lite-v1:0", eval_prompt)
        return "YES" in check.upper()
