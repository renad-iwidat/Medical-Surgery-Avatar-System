"""
Setup LiveKit Agent Dispatch
"""
import os
from livekit import api
from dotenv import load_dotenv

load_dotenv()

def setup_dispatch():
    """Setup agent dispatch for medical avatar rooms"""
    
    url = os.getenv('LIVEKIT_URL')
    api_key = os.getenv('LIVEKIT_API_KEY')
    api_secret = os.getenv('LIVEKIT_API_SECRET')
    
    if not all([url, api_key, api_secret]):
        print("❌ Missing LiveKit credentials")
        return False
    
    try:
        lk_api = api.LiveKitAPI(url, api_key, api_secret)
        
        # Create dispatch rule for morning sessions
        morning_rule = lk_api.agent_dispatch.create_dispatch(
            agent_name="medical-avatar",
            room_name="medical-avatar-morning-*"
        )
        print(f"✅ Morning dispatch rule: {morning_rule.id}")
        
        # Create dispatch rule for evening sessions
        evening_rule = lk_api.agent_dispatch.create_dispatch(
            agent_name="medical-avatar",
            room_name="medical-avatar-evening-*"
        )
        print(f"✅ Evening dispatch rule: {evening_rule.id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False

if __name__ == "__main__":
    setup_dispatch()
