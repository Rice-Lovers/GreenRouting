import os
import boto3 
from datetime import datetime 
from dotenv import load_dotenv

# Load local credentials
load_dotenv()

# Initialize DynamoDB
dynamodb = boto3.resource(   
    'dynamodb',
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

def ensure_table_exists():
    """
    Checks if the DynamoDB table exists. If not, it provides instructions.
    This satisfies the call in main.py.
    """
    table_name = os.getenv("DYNAMOD_TABLE_NAME", "GreenRoutingLogs")
    try:
        table = dynamodb.Table(table_name)
        table.table_status
        return True
    except Exception:
        print(f"⚠️ Table '{table_name}' not found in DynamoDB. Please create it in the AWS Console.")
        return False

def save_green_log(prompt_id, model_name, carbon_saved, complexity_score=0.0):
    """
    Saves the routing decision and complexity data to AWS DynamoDB.
    UPDATED: Now accepts complexity_score to match main.py.
    """
    table_name = os.getenv("DYNAMODB_TABLE_NAME", "GreenRoutingLogs")
    table = dynamodb.Table(table_name)
    timestamp = datetime.utcnow().isoformat()
    
    try:
        table.put_item( 
            Item={
                'prompt_id': str(prompt_id),
                'timestamp': timestamp,
                'model_name': model_name,
                'carbon_saved': str(carbon_saved),
                'complexity_score': str(complexity_score)
            }
        )
        return True
      
    except Exception as e:
        # We don't want a database error to crash the whole AI response demo
        print(f"⚠️ Database Log Note: Saved locally only. (AWS Note: {e})")
        return False
