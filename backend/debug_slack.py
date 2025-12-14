import os
import requests
from dotenv import load_dotenv

def debug_slack():
    print(f"Current Working Directory: {os.getcwd()}")
    
    # Try loading .env
    print("Loading .env file...")
    load_dotenv()
    
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    
    if not webhook_url:
        print("ERROR: SLACK_WEBHOOK_URL not found in environment.")
        print("Please ensure you have created a '.env' file in the 'backend' directory")
        print("and added your SLACK_WEBHOOK_URL to it.")
        return
        
    masked_url = webhook_url[:8] + "..." + webhook_url[-4:] if len(webhook_url) > 12 else "***"
    print(f"Found SLACK_WEBHOOK_URL: {masked_url}")
    
    print("\nAttempting to send test message...")
    
    payload = {
        "text": "*Debug Test*\nThis is a test message from the Slack Debugger."
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("SUCCESS: Message sent successfully!")
        else:
            print("FAILURE: Slack rejected the request.")
            
    except Exception as e:
        print(f"EXCEPTION: {e}")

if __name__ == "__main__":
    debug_slack()
