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
    """
    table_name = os.getenv("DYNAMODB_TABLE_NAME", "GreenRoutingLogs")
    try:
        table = dynamodb.Table(table_name)
        _ = table.table_status
        return True
    except Exception:
        print(f"⚠️ Table '{table_name}' not found. Ensure it exists in region {os.getenv('AWS_REGION')}.")
        return False

def save_green_log(prompt_id, model_name, carbon_saved, complexity_score, prompt_text, response_text, session_id="GLOBAL"):
    """
    Saves multi-agent routing decisions with a session_id for isolation.
    """
    table_name = os.getenv("DYNAMODB_TABLE_NAME", "GreenRoutingLogs")
    table = dynamodb.Table(table_name)
    timestamp = datetime.utcnow().isoformat()
    
    formatted_model = str(model_name).upper().replace("_", " ")
    
    try:
        table.put_item( 
            Item={
                'prompt_id': str(prompt_id),
                'session_id': session_id,  # Isolates metrics per refresh
                'timestamp': timestamp,
                'model_name': formatted_model,
                'carbon_saved': Decimal(str(carbon_saved)),
                'complexity_score': Decimal(str(complexity_score)),
                'prompt_text': prompt_text,
                'response_text': response_text
            }
        )
        print(f"✅ Logged to DynamoDB: {formatted_model} (Session: {session_id})")
        return True
    except Exception as e:
        print(f"⚠️ Database Log Error: {e}")
        return False

def get_total_savings(session_id=None):
    """
    Calculates savings. If session_id is provided, it ONLY sums logs for this session.
    This fixes the issue of previous sessions bleeding into the current one.
    """
    table_name = os.getenv("DYNAMODB_TABLE_NAME", "GreenRoutingLogs")
    table = dynamodb.Table(table_name)
    try:
        if session_id:
            # Filter scan to only include the current session
            from boto3.dynamodb.conditions import Attr
            response = table.scan(
                FilterExpression=Attr('session_id').eq(session_id),
                ProjectionExpression="carbon_saved"
            )
        else:
            response = table.scan(ProjectionExpression="carbon_saved")
            
        items = response.get('Items', [])
        total = sum(float(item['carbon_saved']) for item in items if 'carbon_saved' in item)
        return round(total, 2)
    except Exception as e:
        print(f"⚠️ Error calculating savings: {e}")
        return 0.0

def get_recent_logs(limit=50):
    """
    Retrieves recent logs for Semantic Caching pool.
    """
    table_name = os.getenv("DYNAMODB_TABLE_NAME", "GreenRoutingLogs")
    table = dynamodb.Table(table_name)
    try:
        response = table.scan(Limit=limit)
        return response.get('Items', [])
    except Exception as e:
        print(f"⚠️ Error fetching cache pool: {e}")
        return []

def clear_database_logs():
    """
    HARD RESET: Deletes all items in the DynamoDB table.
    """
    table_name = os.getenv("DYNAMODB_TABLE_NAME", "GreenRoutingLogs")
    table = dynamodb.Table(table_name)
    try:
        scan = table.scan(ProjectionExpression='prompt_id')
        with table.batch_writer() as batch:
            for each in scan.get('Items', []):
                batch.delete_item(Key={'prompt_id': each['prompt_id']})
        return True
    except Exception as e:
        print(f"⚠️ Error clearing database: {e}")
        return False
