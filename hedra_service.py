"""
Hedra Avatar Service
Handles avatar animation and real-time video streaming with Hedra API
"""

import os
import logging
import requests
import time
import hashlib
from dotenv import load_dotenv
from typing import Optional, Dict

load_dotenv()

logger = logging.getLogger(__name__)

class HedraAvatarService:
    """Service for managing Hedra avatars with real-time video generation"""
    
    def __init__(self):
        self.api_key = os.getenv("HEDRA_API_KEY")
        self.base_url = "https://mercury.dev.dream-ai.com/api/v1"  # Hedra's actual API endpoint
        
        # Avatar image paths
        self.avatar_morning_path = "img/avatar-morning.jpeg"
        self.avatar_evening_path = "img/avatar-evening.png"
        
        # Cache for generated videos (to avoid regenerating same content)
        self.video_cache = {}
        
        if not self.api_key:
            logger.warning("⚠️ HEDRA_API_KEY not found - avatar animation will be disabled")
        else:
            logger.info("✅ Hedra Avatar Service initialized")
    
    def get_avatar_path(self, avatar_type: str) -> str:
        """Get avatar image path based on type"""
        if avatar_type == "morning":
            return self.avatar_morning_path
        else:
            return self.avatar_evening_path
    
    def get_avatar_id(self, avatar_type: str) -> str:
        """Get avatar ID from environment"""
        if avatar_type == "morning":
            return os.getenv("HEDRA_AVATAR_MORNING_ID", "morning_avatar")
        else:
            return os.getenv("HEDRA_AVATAR_EVENING_ID", "evening_avatar")
    
    def _get_cache_key(self, text: str, avatar_image_url: str) -> str:
        """Generate cache key for video"""
        content = f"{text}_{avatar_image_url}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def generate_talking_avatar(
        self, 
        text: str, 
        avatar_image_url: str,
        voice_id: str = "default",
        use_cache: bool = True
    ) -> Optional[Dict]:
        """
        Generate talking avatar video using Hedra API
        
        Args:
            text: The text for the avatar to speak
            avatar_image_url: URL of the avatar image
            voice_id: Voice ID to use
            use_cache: Whether to use cached videos
        
        Returns:
            Dict with video_url and job_id, or None if failed
        """
        if not self.api_key:
            logger.error("❌ Hedra API key not configured")
            return None
        
        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(text, avatar_image_url)
            if cache_key in self.video_cache:
                logger.info(f"✅ Using cached video for text: {text[:50]}...")
                return self.video_cache[cache_key]
        
        try:
            logger.info(f"🎤 Generating audio for text: {text[:50]}...")
            
            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Step 1: Generate audio using Hedra's TTS
            audio_payload = {
                "text": text,
                "voiceId": "b42d6c83-9ab5-4bce-a1e7-c1c8c1b57d3f"  # Arabic voice
            }
            
            audio_response = requests.post(
                f"{self.base_url}/audio",
                headers=headers,
                json=audio_payload,
                timeout=30
            )
            
            if audio_response.status_code != 200:
                logger.error(f"❌ Audio generation failed: {audio_response.status_code}")
                return None
            
            audio_data = audio_response.json()
            audio_url = audio_data.get("url")
            
            if not audio_url:
                logger.error("❌ No audio URL returned")
                return None
            
            logger.info(f"✅ Audio generated")
            
            # Step 2: Create character video with audio
            logger.info(f"🎬 Creating character video...")
            
            video_payload = {
                "audioSource": audio_url,
                "avatarImage": avatar_image_url,
                "aspectRatio": "1:1"
            }
            
            video_response = requests.post(
                f"{self.base_url}/character",
                headers=headers,
                json=video_payload,
                timeout=30
            )
            
            if video_response.status_code != 200:
                logger.error(f"❌ Video creation failed: {video_response.status_code}")
                return None
            
            video_data = video_response.json()
            job_id = video_data.get("jobId")
            
            if not job_id:
                logger.error("❌ No job_id returned")
                return None
            
            logger.info(f"✅ Video job created: {job_id}")
            
            # Step 3: Poll for completion
            max_attempts = 90
            attempt = 0
            
            while attempt < max_attempts:
                time.sleep(1)
                attempt += 1
                
                status_response = requests.get(
                    f"{self.base_url}/character/{job_id}",
                    headers=headers,
                    timeout=10
                )
                
                if status_response.status_code != 200:
                    continue
                
                status_data = status_response.json()
                status = status_data.get("status")
                
                if attempt % 5 == 0:
                    logger.info(f"📊 Status: {status} ({attempt}/{max_attempts}s)")
                
                if status == "completed":
                    video_url = status_data.get("videoUrl")
                    if video_url:
                        logger.info(f"✅ Video ready!")
                        result = {
                            "video_url": video_url,
                            "job_id": job_id,
                            "status": "completed"
                        }
                        
                        # Cache result
                        if use_cache:
                            cache_key = self._get_cache_key(text, avatar_image_url)
                            self.video_cache[cache_key] = result
                        
                        return result
                    else:
                        logger.error("❌ No video_url in response")
                        return None
                
                elif status == "failed":
                    logger.error(f"❌ Job failed")
                    return None
            
            logger.error("❌ Timeout after 90s")
            return None
            
        except Exception as e:
            logger.error(f"❌ Exception: {str(e)}")
            return None


async def setup_avatars():
    """Setup avatars - verify paths exist"""
    service = HedraAvatarService()
    
    if not os.path.exists(service.avatar_morning_path):
        logger.error(f"❌ Morning avatar not found: {service.avatar_morning_path}")
        raise Exception(f"Missing: {service.avatar_morning_path}")
    
    if not os.path.exists(service.avatar_evening_path):
        logger.error(f"❌ Evening avatar not found: {service.avatar_evening_path}")
        raise Exception(f"Missing: {service.avatar_evening_path}")
    
    logger.info(f"✅ Avatars setup complete!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(setup_avatars())
