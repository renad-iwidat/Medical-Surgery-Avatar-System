"""
LiveKit Agent for Medical Avatar
Handles real-time communication with students using Hedra for avatar animation
"""

import os
import json
import logging
import asyncio
import certifi
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv

# Suppress Pydantic warnings before importing LiveKit
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

from livekit import agents, rtc
from livekit.agents import AgentServer, AgentSession, Agent, JobContext
from livekit.plugins import openai, silero, hedra
from prompts import get_system_prompt

# SSL certificates
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

load_dotenv()

# Configure logging
logger = logging.getLogger("medical-avatar")
logger.setLevel(logging.INFO)

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HEDRA_API_KEY = os.getenv("HEDRA_API_KEY")

if OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
if HEDRA_API_KEY:
    os.environ["HEDRA_API_KEY"] = HEDRA_API_KEY

# Avatar images
AVATAR_MORNING = "img/avatar-morning.jpeg"
AVATAR_EVENING = "img/avatar-evening.png"

# Create agent server
server = AgentServer()


def load_scenario(scenario_type: str) -> dict:
    """Load scenario from JSON file"""
    scenario_file = f"scenarios/case-{scenario_type}.json"
    
    try:
        with open(scenario_file, 'r', encoding='utf-8') as f:
            scenario = json.load(f)
        logger.info(f"✅ Loaded scenario: {scenario_file}")
        return scenario
    except Exception as e:
        logger.error(f"❌ Failed to load scenario: {e}")
        return {}


def build_system_prompt(scenario: dict) -> str:
    """Build system prompt from prompts.py - Uses the new detailed rules"""
    
    # Get the base prompt from prompts.py
    base_prompt = get_system_prompt(scenario, language='ar')
    
    # Add the complete scenario data as JSON for reference
    arabic_translations = scenario.get('arabicTranslations', {})
    scenario_json = json.dumps(arabic_translations, ensure_ascii=False, indent=2)
    
    # Combine base prompt with scenario data
    complete_prompt = f"""{base_prompt}

=== بيانات السيناريو الكاملة - أجب منها فقط ===

{scenario_json}

تذكر: أجب فقط من البيانات أعلاه. إذا سُئلت عن شيء غير موجود، قل "ما بعرف"."""
    
    return complete_prompt


class MedicalPatientAgent(Agent):
    """Medical patient agent for OSCE training"""
    
    def __init__(self, scenario: dict):
        instructions = build_system_prompt(scenario)
        super().__init__(instructions=instructions)


@server.rtc_session()
async def medical_avatar_entrypoint(ctx: JobContext):
    """Main agent entry point"""
    
    room_name = ctx.room.name
    logger.info(f"🚀 Starting Medical Avatar for room: {room_name}")
    
    # Determine scenario type from room name - more precise matching
    room_name_lower = room_name.lower()
    if "morning" in room_name_lower:
        scenario_type = "morning"
    elif "evening" in room_name_lower:
        scenario_type = "evening"
    else:
        # Default to evening if not specified
        scenario_type = "evening"
        logger.warning(f"⚠️ Could not determine scenario type from room name, defaulting to evening")
    
    avatar_path = AVATAR_MORNING if scenario_type == "morning" else AVATAR_EVENING
    
    logger.info(f"📋 Scenario: {scenario_type}")
    logger.info(f"🖼️ Avatar: {avatar_path}")
    logger.info(f"📍 Room name analysis: '{room_name}' -> scenario_type: '{scenario_type}'")
    logger.info(f"✅ CONFIRMED: Using {scenario_type.upper()} scenario")
    
    # Load scenario
    scenario = load_scenario(scenario_type)
    if not scenario:
        logger.error("❌ Failed to load scenario")
        return
    
    # Verify scenario loaded correctly
    patient_name = scenario.get('arabicTranslations', {}).get('patientInfo', {}).get('name', 'Unknown')
    logger.info(f"✅ Scenario loaded: Patient = {patient_name}, Type = {scenario_type}")
    
    # Load avatar image
    avatar_img = None
    try:
        img = Image.open(avatar_path)
        if img.mode != 'RGB':
            if img.mode == 'RGBA':
                bg = Image.new('RGB', img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[3])
                img = bg
            else:
                img = img.convert('RGB')
        avatar_img = img
        logger.info("✅ Avatar image loaded")
    except Exception as e:
        logger.error(f"❌ Failed to load avatar: {e}")
        return
    
    # Create agent session with Arabic male voice
    session = AgentSession(
        vad=silero.VAD.load(),
        stt=openai.STT(language="ar"),
        llm=openai.LLM(model="gpt-4o-mini", temperature=0.7),
        tts=openai.TTS(voice="fable", speed=1.0),  # Male voice, slower for Arabic clarity
    )
    
    # Start Hedra avatar if available
    avatar_session = None
    if avatar_img and HEDRA_API_KEY:
        try:
            patient_name = scenario.get('arabicTranslations', {}).get('patientInfo', {}).get('name', 'المريض')
            
            avatar_session = hedra.AvatarSession(
                avatar_image=avatar_img,
                avatar_participant_name=patient_name
            )
            await avatar_session.start(session, room=ctx.room)
            logger.info("✅ Hedra avatar started - Real-time animation enabled!")
        except Exception as e:
            logger.warning(f"⚠️ Hedra avatar failed: {e}")
    
    # Create agent instance
    agent_instance = MedicalPatientAgent(scenario)
    
    # Start agent session
    await session.start(
        room=ctx.room,
        agent=agent_instance
    )
    
    logger.info(f"🎉 Medical Avatar ready in room: {room_name}")
    logger.info("✅ Real-time avatar animation with Hedra")
    logger.info("✅ Arabic speech recognition")
    logger.info("✅ OpenAI GPT-4o-mini for responses")
    
    # Send initial greeting from patient after a short delay
    async def send_greeting():
        try:
            await asyncio.sleep(4)  # Wait for connection
            
            patient_name = scenario.get('arabicTranslations', {}).get('patientInfo', {}).get('name', 'المريض')
            # Remove "السيد" or "السيدة" prefix if present
            patient_name = patient_name.replace('السيد ', '').replace('السيدة ', '')
            
            # NEW GREETING - exactly as requested
            greeting = f"مرحباً، أنا {patient_name}. دكتور، مش حاس حالي منيح اليوم. شو ممكن يكون السبب برأيك؟"
            
            # Send greeting through agent
            await session.say(greeting, allow_interruptions=False)
            logger.info(f"👋 Patient greeting SAID via session.say: {greeting}")
            
            # Also send as data message so it appears in transcript
            try:
                greeting_data = {
                    "type": "transcription",
                    "role": "patient",
                    "text": greeting
                }
                await ctx.room.local_participant.publish_data(
                    json.dumps(greeting_data, ensure_ascii=False).encode('utf-8'),
                    reliable=True
                )
                logger.info(f"👋 Greeting sent as data message for transcript")
            except Exception as e:
                logger.warning(f"⚠️ Failed to send greeting as data message: {e}")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to send greeting: {e}")
    
    # Start greeting task in background
    asyncio.create_task(send_greeting())
    
    # Wait for disconnect - but don't close immediately
    disconnect_event = asyncio.Event()
    
    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        # Only disconnect if it's a real student (not the avatar)
        if not participant.identity.startswith("hedra-avatar") and not participant.identity.startswith("agent"):
            logger.info(f"👋 User disconnected from room: {room_name}")
            # Wait a bit before closing in case they reconnect
            asyncio.create_task(delayed_disconnect())
    
    async def delayed_disconnect():
        await asyncio.sleep(5)  # Wait 5 seconds
        disconnect_event.set()
    
    try:
        await disconnect_event.wait()
        
        # Cleanup
        if avatar_session:
            try:
                if hasattr(avatar_session, 'close'):
                    await avatar_session.close()
                logger.info(f"✅ Avatar stopped: {room_name}")
            except Exception as e:
                logger.warning(f"⚠️ Error stopping avatar: {e}")
        
        if session:
            try:
                await session.aclose()
                logger.info(f"✅ Session closed: {room_name}")
            except Exception as e:
                logger.warning(f"⚠️ Error closing session: {e}")
        
        logger.info(f"👋 Session ended: {room_name}")
        
    except Exception as e:
        logger.error(f"❌ Error in room {room_name}: {e}")
        raise


if __name__ == "__main__":
    agents.cli.run_app(server)
