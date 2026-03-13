import os
import boto3 #official AWS SDK for python
from datetime import datetime #generate timestamps for logs
from dotenv import load_dotenv

# Load local credentials
load_dotenv()

# Initialize DynamoDB using the variables from .env
# Note: boto3 automatically looks for AWS_ACCESS_KEY_ID and 
# AWS_SECRET_ACCESS_KEY if they are in the environment.
dynamodb = boto3.resource(   
    'dynamodb',
    region_name=os.getenv("AWS_REGION", "us-east-1")  #specifiess data center
) #creates a connection to DynamoDB

def save_green_log(prompt_id, model_name, carbon_saved):
    """
    Saves the routing decision and carbon offset data to AWS DynamoDB.
    """
    table = dynamodb.Table('GreenRoutingLogs')
    timestamp = datetime.utcnow().isoformat()
    
    try:
        table.put_item( 
            Item={
                'prompt_id': str(prompt_id),
                'timestamp': timestamp,
                'model_name': model_name,
                'carbon_saved': str(carbon_saved)
            }
        ) #sends data to AWS to save in table
        return True #confirms the save was successful
      
    except Exception as e:
        print(f"Database Error: Could not save log to DynamoDB. {e}")
        return False
