import os
import boto3 
from datetime import datetime 
from dotenv import load_dotenv
from decimal import Decimal

# Load local credentials
load_dotenv()

# Initialize DynamoDB
dynamodb = boto3.resource(   
    'dynamodb',
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

def ensure_table_exists():
    """
    Checks if the DynamoDB table exists. 
    Matches the call in main.py to prevent startup crashes.
    """
    table_name = os.getenv("DYNAMODB_TABLE_NAME", "GreenRoutingLogs")
    try:
        table = dynamodb.Table(table_name)
        # Accessing an attribute to trigger an exception if table doesn't exist
        _ = table.table_status
        return True
    except Exception:
        print(f"⚠️ Table '{table_name}' not found. Ensure it exists in region {os.getenv('AWS_REGION')}.")
        return False

def save_green_log(prompt_id, model_name, carbon_saved, complexity_score=0.0):
    """
    Saves multi-agent routing decisions and environmental impact to AWS DynamoDB.
    Converts numbers to Decimal to avoid float errors in AWS.
    """
    table_name = os.getenv("DYNAMODB_TABLE_NAME", "GreenRoutingLogs")
    table = dynamodb.Table(table_name)
    timestamp = datetime.utcnow().isoformat()
    
    # Clean up model name for database consistency (e.g., "claude_pro" -> "CLAUDE PRO")
    formatted_model = str(model_name).upper().replace("_", " ")
    
    try:
        table.put_item( 
            Item={
                'prompt_id': str(prompt_id),
                'timestamp': timestamp,
                'model_name': formatted_model,
                # DynamoDB requires Decimal for numeric values to preserve precision
                'carbon_saved': Decimal(str(carbon_saved)),
                'complexity_score': Decimal(str(complexity_score))
            }
        )
        print(f"✅ Logged to DynamoDB: {formatted_model} saved {carbon_saved}mg CO2")
        return True
      
    except Exception as e:
        # Prevents database issues from interrupting the AI demo flow
        print(f"⚠️ Database Log Note: Could not save to AWS. (Error: {e})")
        return False
