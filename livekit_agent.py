"""
LiveKit Agent for Medical Avatar
Uses OpenAI Realtime API for LLM and TTS instead of LiveKit agents
"""

import os
import json
import logging
import asyncio
import certifi
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import AgentServer, JobContext
from livekit.plugins import hedra
import openai

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
    """Build system prompt from scenario"""
    
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


@server.rtc_session()
async def medical_avatar_entrypoint(ctx: JobContext):
    """Main agent entry point using OpenAI Realtime API"""
    
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
    
    # Start Hedra avatar if available
    avatar_session = None
    if avatar_img and HEDRA_API_KEY:
        try:
            patient_name = scenario.get('arabicTranslations', {}).get('patientInfo', {}).get('name', 'المريض')
            
            # Create a simple agent session for Hedra
            from livekit.agents import AgentSession
            from livekit.plugins import openai, silero
            
            session = AgentSession(
                vad=silero.VAD.load(),
                stt=openai.STT(language="ar"),
                llm=openai.LLM(model="gpt-4o-mini", temperature=0.7),
                tts=openai.TTS(voice="onyx"),
            )
            
            avatar_session = hedra.AvatarSession(
                avatar_image=avatar_img,
                avatar_participant_name=patient_name
            )
            await avatar_session.start(session, room=ctx.room)
            logger.info("✅ Hedra avatar started - Real-time animation enabled!")
            
            # Send greeting
            system_prompt = build_system_prompt(scenario)
            patient_name_clean = patient_name.replace('السيد ', '').replace('السيدة ', '')
            greeting = f"مرحباً، أنا {patient_name_clean}. دكتور، مش حاس حالي منيح اليوم. شو ممكن يكون السبب برأيك؟"
            
            await session.say(greeting, allow_interruptions=False)
            logger.info(f"👋 Patient greeting sent: {greeting}")
            
            # Keep session alive
            await asyncio.sleep(300)  # 5 minutes
            
        except Exception as e:
            logger.warning(f"⚠️ Hedra avatar failed: {e}")
            logger.info("Continuing without avatar...")
    
    logger.info(f"🎉 Medical Avatar session ended: {room_name}")


if __name__ == "__main__":
    agents.cli.run_app(server)
