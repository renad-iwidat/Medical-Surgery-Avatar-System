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

# Workaround for Pydantic/LiveKit compatibility
import sys
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Suppress the specific Pydantic error during import
import io
from contextlib import redirect_stderr

stderr_capture = io.StringIO()
with redirect_stderr(stderr_capture):
    try:
        from livekit import agents, rtc
        from livekit.agents import AgentServer, AgentSession, Agent, JobContext
        from livekit.plugins import openai, silero, hedra
    except Exception as e:
        if "SessionUsageUpdatedEvent" not in str(e):
            raise
        # If it's the Pydantic error, continue anyway
        from livekit import agents, rtc
        from livekit.agents import AgentServer, AgentSession, Agent, JobContext
        from livekit.plugins import openai, silero, hedra

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
    """Build system prompt from scenario - Rule-based responses from JSON only"""
    
    arabic_translations = scenario.get('arabicTranslations', {})
    patient_info = arabic_translations.get('patientInfo', {})
    
    patient_name = patient_info.get('name', 'المريض')
    patient_age = patient_info.get('age', '')
    patient_gender = patient_info.get('gender', 'ذكر')
    patient_occupation = patient_info.get('occupation', '')
    
    diagnosis = arabic_translations.get('diagnosis', '')
    chief_complaint = arabic_translations.get('presentingComplaint', {}).get('full', '')
    
    # Build complete scenario data as JSON string for reference
    scenario_json = json.dumps(arabic_translations, ensure_ascii=False, indent=2)
    
    prompt = f"""أنت مريض افتراضي في جلسة تدريب طبية OSCE للجراحة.

معلوماتك الأساسية:
- الاسم: {patient_name}
- العمر: {patient_age}
- الجنس: {patient_gender}
- المهنة: {patient_occupation}
- التشخيص: {diagnosis}
- الشكوى الرئيسية: {chief_complaint}

التعليمات الحرجة - اتبعها بدقة:
1. أجب فقط من المعلومات الموجودة في السيناريو أدناه - لا تخترع معلومات
2. تحدث بالعربية الفصحى مع لهجة فلسطينية/شامية خفيفة
3. كن واقعياً وطبيعياً - أنت مريض حقيقي يعاني من ألم
4. أجب بإجابات قصيرة ومباشرة (جملة أو جملتين فقط)
5. أظهر الألم والانزعاج بشكل طبيعي في إجاباتك
6. كن متعاوناً مع الطالب لكن لا تعطِ تشخيصات طبية
7. إذا سُئلت عن شيء غير موجود في السيناريو، قل "ما بعرف" أو "لا أعرف"
8. لا تستخدم معرفتك الطبية العامة - فقط ما هو مكتوب في السيناريو

أسلوب الرد:
- استخدم "عندي" بدل "لدي"
- استخدم "بحس" بدل "أشعر"
- استخدم "وجع" أو "ألم" للألم
- استخدم "من" للزمن (مثلاً: "من 12 ساعة")
- كن بسيط ومباشر في الكلام

معلومات السيناريو الكاملة (أجب منها فقط):
{scenario_json}

تذكر: أنت مريض حقيقي، مش دكتور. أجب فقط من المعلومات أعلاه."""
    
    return prompt


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
    
    # Determine scenario type from room name
    scenario_type = "morning" if "morning" in room_name.lower() else "evening"
    avatar_path = AVATAR_MORNING if scenario_type == "morning" else AVATAR_EVENING
    
    logger.info(f"📋 Scenario: {scenario_type}")
    logger.info(f"🖼️ Avatar: {avatar_path}")
    
    # Load scenario
    scenario = load_scenario(scenario_type)
    if not scenario:
        logger.error("❌ Failed to load scenario")
        return
    
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
        tts=openai.TTS(voice="onyx"),  # Male voice for Arabic
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
            logger.warning(f"⚠️ Hedra avatar failed (will continue without avatar): {e}")
            avatar_session = None
    
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
