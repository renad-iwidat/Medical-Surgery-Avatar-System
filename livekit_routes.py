"""
LiveKit Routes
API endpoints for LiveKit integration
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from livekit_room_manager import get_room_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/livekit", tags=["livekit"])

class TokenRequest(BaseModel):
    room_name: str
    participant_name: str
    is_agent: bool = False

class RoomRequest(BaseModel):
    room_name: str
    max_participants: int = 1

@router.post("/token")
async def get_token(request: TokenRequest):
    """Generate LiveKit access token"""
    
    try:
        room_manager = get_room_manager()
        token = room_manager.generate_token(
            room_name=request.room_name,
            participant_name=request.participant_name,
            is_agent=request.is_agent
        )
        
        return {
            "token": token,
            "url": room_manager.url,
            "room": request.room_name
        }
    except Exception as e:
        logger.error(f"❌ Token generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/room")
async def create_room(request: RoomRequest):
    """Create a new LiveKit room and dispatch agent"""
    
    try:
        room_manager = get_room_manager()
        room = room_manager.create_room(
            room_name=request.room_name,
            max_participants=request.max_participants
        )
        
        # Agent is automatically dispatched via livekit_agent.py
        logger.info(f"✅ Room created: {request.room_name}")
        logger.info(f"   Agent will join automatically when participant connects")
        
        return room
    except Exception as e:
        logger.error(f"❌ Room creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rooms")
async def list_rooms():
    """List all active rooms"""
    
    try:
        room_manager = get_room_manager()
        rooms = room_manager.list_rooms()
        
        return {
            "rooms": [
                {
                    "name": room.name,
                    "sid": room.sid,
                    "num_participants": room.num_participants,
                    "created_at": room.creation_time
                }
                for room in rooms
            ]
        }
    except Exception as e:
        logger.error(f"❌ Failed to list rooms: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/room/{room_name}")
async def delete_room(room_name: str):
    """Delete a room"""
    
    try:
        room_manager = get_room_manager()
        success = room_manager.delete_room(room_name)
        
        if success:
            return {"message": f"Room {room_name} deleted"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete room")
    except Exception as e:
        logger.error(f"❌ Room deletion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
