from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from pathlib import Path
from dotenv import load_dotenv
from session_manager import SessionManager
from scenario_manager import ScenarioManager
from livekit_routes import router as livekit_router
import json

# Load environment variables
load_dotenv()

app = FastAPI(title="Medical Avatar - Surgery")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize managers
session_manager = SessionManager()
scenario_manager = ScenarioManager()
medical_agent = None  # Lazy initialization

def get_agent():
    """Get or create medical agent"""
    global medical_agent
    if medical_agent is None:
        from agent import MedicalAgent
        medical_agent = MedicalAgent()
    return medical_agent

# Pydantic models
class StartSessionRequest(BaseModel):
    studentName: str
    department: str
    session: str

class SendMessageRequest(BaseModel):
    sessionId: str
    message: str

class EndSessionRequest(BaseModel):
    sessionId: str

class TTSRequest(BaseModel):
    text: str
    gender: str = "female"

class VideoGenerationRequest(BaseModel):
    text: str
    imageUrl: str
    voiceId: str = "default"

# Include LiveKit routes
app.include_router(livekit_router)

# API Routes (MUST be before static files mount)

@app.get("/api/scenarios")
async def get_scenarios():
    """Get all available scenarios"""
    scenarios = scenario_manager.get_all_scenarios()
    return scenarios

@app.get("/api/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str):
    """Get a specific scenario"""
    scenario = scenario_manager.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario

@app.post("/api/session/start")
async def start_session(request: StartSessionRequest):
    """Start a new session"""
    result = session_manager.create_session(
        student_name=request.studentName,
        department=request.department,
        session_type=request.session
    )
    return result

@app.post("/api/session/message")
async def send_message(request: SendMessageRequest):
    """Send a message and get response"""
    session = session_manager.get_session(request.sessionId)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session['is_active']:
        raise HTTPException(status_code=400, detail="Session is not active")
    
    # Add student message
    session_manager.add_message(request.sessionId, "student", request.message)
    
    # Get conversation history
    history = session_manager.get_session_messages(request.sessionId)
    
    # Generate response
    agent = get_agent()
    response = agent.generate_response(
        scenario=session['scenario'],
        question=request.message,
        conversation_history=history[:-1]  # Exclude the current message
    )
    
    # Add agent response
    session_manager.add_message(request.sessionId, "avatar", response)
    
    return {
        "success": True,
        "response": response
    }

@app.post("/api/session/end")
async def end_session(request: EndSessionRequest):
    """End a session"""
    success = session_manager.end_session(request.sessionId)
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "success": True,
        "message": "Session ended successfully"
    }

@app.get("/api/tts-status")
async def tts_status():
    """Check if TTS is available"""
    return {
        "enabled": bool(os.getenv("OPENAI_API_KEY")),
        "service": "OpenAI TTS"
    }

@app.post("/api/tts")
async def text_to_speech(request: TTSRequest):
    """Generate speech from text using OpenAI TTS"""
    text = request.text
    gender = request.gender
    
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    
    try:
        from openai import OpenAI
        import io
        
        # Remove SSL_CERT_FILE environment variable if it exists
        if 'SSL_CERT_FILE' in os.environ:
            del os.environ['SSL_CERT_FILE']
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Use appropriate voice based on gender (shimmer for female, fable for male)
        voice = "shimmer" if gender == "female" else "fable"
        
        # Enhanced instructions for more natural patient-like speech in Arabic
        instructions = (
            "تحدثي بالعربية بنبرة طبيعية ودافئة كمريضة حقيقية. أظهري القلق والتعب بشكل خفيف. "
            "تكلمي بهدوء وتعاون مع الطبيب. عبّري عن الألم والانزعاج بطريقة واقعية وإنسانية. "
            "استخدمي نبرة صوت متعبة قليلاً لكن واضحة."
        ) if gender == "female" else (
            "تحدث بالعربية بنبرة طبيعية وواضحة كمريض حقيقي. أظهر القلق والألم بشكل طبيعي. "
            "تكلم بهدوء وتعاون مع الطبيب. عبّر عن الانزعاج والتعب بطريقة واقعية وإنسانية. "
            "استخدم نبرة صوت متعبة قليلاً لكن واضحة ومفهومة."
        )
        
        response = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice=voice,
            input=text,
            speed=1.4,
            response_format="mp3"
        )
        
        # Return audio stream
        return StreamingResponse(
            io.BytesIO(response.content),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=speech.mp3"}
        )
    except Exception as e:
        print(f"TTS Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"TTS error: {str(e)}")

@app.post("/api/generate-video")
async def generate_video(request: VideoGenerationRequest):
    """Generate video with lip sync using Hedra API"""
    try:
        from hedra_service import HedraAvatarService
        
        hedra_service = HedraAvatarService()
        
        # Generate talking avatar
        result = await hedra_service.generate_talking_avatar(
            text=request.text,
            avatar_image_url=request.imageUrl,
            voice_id=request.voiceId
        )
        
        if result and result.get("video_url"):
            return {
                "status": "success",
                "video_url": result["video_url"],
                "job_id": result["job_id"]
            }
        else:
            # Fallback to image if Hedra fails
            return {
                "status": "fallback",
                "message": "Video generation failed, using image fallback",
                "image_url": request.imageUrl
            }
    except Exception as e:
        print(f"Video generation error: {str(e)}")
        return {
            "status": "fallback",
            "message": f"Error: {str(e)}",
            "image_url": request.imageUrl
        }

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "Medical Avatar Surgery"}

# Mount static files LAST
public_dir = Path("public")
if public_dir.exists():
    app.mount("/", StaticFiles(directory="public", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
