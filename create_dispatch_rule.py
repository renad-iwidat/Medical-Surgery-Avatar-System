"""
Create LiveKit Agent Dispatch Rule
"""
import os
from livekit import api
from dotenv import load_dotenv

load_dotenv()

def create_dispatch_rule():
    """Create agent dispatch rule for medical avatar"""
    
    # Get LiveKit credentials
    url = os.getenv('LIVEKIT_URL')
    api_key = os.getenv('LIVEKIT_API_KEY')
    api_secret = os.getenv('LIVEKIT_API_SECRET')
    
    if not all([url, api_key, api_secret]):
        print("❌ Missing LiveKit credentials in .env file")
        return
    
    # Create API client
    lk_api = api.LiveKitAPI(url, api_key, api_secret)
    
    # Create dispatch rule
    try:
        rule = lk_api.agent_dispatch.create_dispatch(
            agent_name="medical-avatar-agent",
            room_name="medical-avatar-*",  # Match all rooms starting with medical-avatar-
            metadata={"type": "medical-training"}
        )
        
        print(f"✅ Dispatch rule created: {rule.id}")
        print(f"   Agent: {rule.agent_name}")
        print(f"   Room pattern: {rule.room_name}")
        
    except Exception as e:
        print(f"❌ Failed to create dispatch rule: {e}")

if __name__ == "__main__":
    create_dispatch_rule()
