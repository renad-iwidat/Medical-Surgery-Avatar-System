"""
LiveKit Room Manager
Manages room creation and token generation for students
"""

import os
import logging
from datetime import datetime, timedelta
from livekit.api import AccessToken, VideoGrants, LiveKitAPI

logger = logging.getLogger(__name__)

class LiveKitRoomManager:
    """Manages LiveKit rooms and tokens"""
    
    def __init__(self):
        self.url = os.getenv("LIVEKIT_URL")
        self.api_key = os.getenv("LIVEKIT_API_KEY")
        self.api_secret = os.getenv("LIVEKIT_API_SECRET")
        
        if not all([self.url, self.api_key, self.api_secret]):
            raise ValueError("Missing LiveKit credentials in .env")
        
        # Create API client
        self.api_client = LiveKitAPI(
            url=self.url,
            api_key=self.api_key,
            api_secret=self.api_secret
        )
        
        logger.info("✅ LiveKit Room Manager initialized")
    
    async def create_room_with_agent(self, room_name: str, max_participants: int = 1) -> dict:
        """Create a new room and request agent to join"""
        
        logger.info(f"📍 Creating room with agent: {room_name}")
        
        try:
            # Create room using API
            room = await self.api_client.room.create_room(
                api.CreateRoomRequest(
                    name=room_name,
                    empty_timeout=300,  # 5 minutes
                    max_participants=max_participants + 1  # +1 for agent
                )
            )
            
            logger.info(f"✅ Room created: {room_name}")
            
            return {
                "name": room.name,
                "sid": room.sid,
                "created_at": int(datetime.now().timestamp())
            }
        except Exception as e:
            logger.warning(f"⚠️ Room creation via API failed: {e}")
            # Fallback: room will be created automatically
            logger.info(f"📍 Room will be created automatically: {room_name}")
            return {
                "name": room_name,
                "sid": room_name,
                "created_at": int(datetime.now().timestamp())
            }
    
    def create_room(self, room_name: str, max_participants: int = 1) -> dict:
        """Create a new room (simplified - room is created automatically when first participant joins)"""
        
        logger.info(f"📍 Room will be created automatically: {room_name}")
        
        return {
            "name": room_name,
            "sid": room_name,
            "created_at": int(datetime.now().timestamp())
        }
    
    def generate_token(self, room_name: str, participant_name: str, is_agent: bool = False) -> str:
        """Generate access token for a participant"""
        
        logger.info(f"🔑 Generating token for {participant_name} in room {room_name}")
        
        try:
            token = AccessToken(
                api_key=self.api_key,
                api_secret=self.api_secret
            )
            
            token.with_identity(participant_name)
            token.with_name(participant_name)
            token.with_ttl(timedelta(hours=1))
            
            # Grant video permissions
            token.with_grants(VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=not is_agent,
                can_publish_data=True,
                can_subscribe=True
            ))
            
            token_str = token.to_jwt()
            logger.info(f"✅ Token generated for {participant_name}")
            return token_str
        except Exception as e:
            logger.error(f"❌ Failed to generate token: {e}")
            raise
    
    def delete_room(self, room_name: str) -> bool:
        """Delete a room (rooms are automatically cleaned up by LiveKit)"""
        
        logger.info(f"🗑️ Room will be auto-cleaned: {room_name}")
        return True


# Global instance
_room_manager = None

def get_room_manager() -> LiveKitRoomManager:
    """Get or create room manager instance"""
    global _room_manager
    if _room_manager is None:
        _room_manager = LiveKitRoomManager()
    return _room_manager
