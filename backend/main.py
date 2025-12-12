from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from ai_core import ai_service
from voice_service import voice_service
from voice_groq import groq_voice
from database import chat_db
from typing import List, Optional, Dict
from loguru import logger
import json
from datetime import datetime
import asyncio

# Initialize FastAPI app
app = FastAPI(
    title="Iroha AI Study Buddy",
    description="AI study mentor featuring Isshiki Iroha from Oregairu",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve simple web UI
app.mount("/web", StaticFiles(directory="public", html=True), name="web")

# Configure logger
logger.add("logs/api_{time}.log", rotation="1 day", retention="7 days")

# ===== PYDANTIC MODELS =====

class Message(BaseModel):
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    message: str = Field(..., description="User's message", min_length=1)
    persona: str = Field(default="iroha", description="Persona key (default: iroha)")
    history: Optional[List[Message]] = Field(default=[], description="Conversation history")
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=100, le=2000)

class ChatResponse(BaseModel):
    success: bool
    response: str
    persona: Dict[str, str]
    metadata: Optional[Dict] = None
    error: Optional[str] = None

class PersonaInfo(BaseModel):
    key: str
    name: str
    avatar: str
    description: Optional[str] = None

class VoiceRequest(BaseModel):
    text: str = Field(..., description="Text to convert to speech")
    voice: str = Field(default="iroha_jp", description="Voice preference")
    play_audio: bool = Field(default=False, description="Whether to play audio")

class VoiceResponse(BaseModel):
    success: bool
    audio_file: Optional[str] = None
    error: Optional[str] = None

# Session models for chat history
class SessionCreate(BaseModel):
    title: str = Field(default="New Chat")
    persona: str = Field(default="iroha")

class SessionResponse(BaseModel):
    id: int
    title: str
    persona: str
    created_at: str
    updated_at: str
    is_archived: bool
    message_count: int

class ChatWithSessionRequest(BaseModel):
    message: str = Field(..., description="User's message", min_length=1)
    session_id: Optional[int] = Field(default=None, description="Session ID for history")
    persona: str = Field(default="iroha")
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=100, le=2000)

# ===== ENDPOINTS =====

@app.get("/", tags=["Health"])
def read_root():
    """Health check endpoint"""
    return {
        "status": "online",
        "message": "Iroha AI Study Buddy is ready",
        "persona": "Isshiki Iroha",
        "version": "2.0.0",
        "framework": "FastAPI + PyTorch + Groq",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health", tags=["Health"])
def health_check():
    """Detailed health check"""
    import torch
    return {
        "status": "healthy",
        "pytorch": {
            "available": True,
            "version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "device": str(ai_service.device)
        },
        "groq": {
            "model": ai_service.model,
            "status": "connected"
        }
    }

@app.get("/persona", response_model=PersonaInfo, tags=["Persona"])
def get_persona():
    """Get Iroha persona info"""
    try:
        personas = ai_service.get_available_personas()
        logger.info("Retrieved Iroha persona info")
        return personas[0]
    except Exception as e:
        logger.error(f"Error getting persona: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint"""
    try:
        logger.info(f"Chat request - Persona: {request.persona}, Length: {len(request.message)}")
        
        # Convert Pydantic models to dicts
        history_dicts = [
            {"role": h.role, "content": h.content} 
            for h in request.history
        ] if request.history else []
        
        # Get AI response
        result = ai_service.get_response(
            message=request.message,
            persona_key=request.persona,
            history=history_dicts,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # Check for errors
        if result.get("error"):
            logger.error(f"AI Service error: {result.get('error_message')}")
            return ChatResponse(
                success=False,
                response=result["response"],
                persona={"name": "System", "avatar": "", "key": "error"},
                error=result.get("error_message")
            )
        
        logger.info("Chat response generated")
        return ChatResponse(
            success=True,
            response=result["response"],
            persona=result["persona"],
            metadata=result.get("metadata")
        )
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/sentiment", tags=["Chat"])
async def analyze_sentiment(message: str):
    """Analyze sentiment of user message"""
    try:
        sentiment = ai_service.analyze_sentiment(message)
        return {
            "message": message,
            "sentiment": sentiment,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== CHAT HISTORY ENDPOINTS =====

@app.get("/sessions", tags=["History"])
async def get_sessions(include_archived: bool = False):
    """Get all chat sessions"""
    try:
        sessions = chat_db.get_all_sessions(include_archived=include_archived)
        return {
            "success": True,
            "sessions": sessions  # Already dicts from database
        }
    except Exception as e:
        logger.error(f"Error getting sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sessions", tags=["History"])
async def create_session(request: SessionCreate):
    """Create a new chat session"""
    try:
        session = chat_db.create_session(title=request.title, persona=request.persona)
        return {
            "success": True,
            "session": session.to_dict()
        }
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions/{session_id}", tags=["History"])
async def get_session(session_id: int):
    """Get a specific session with messages"""
    try:
        session = chat_db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        messages = chat_db.get_session_messages(session_id)
        return {
            "success": True,
            "session": session.to_dict(),
            "messages": [m.to_dict() for m in messages]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/sessions/{session_id}", tags=["History"])
async def update_session(session_id: int, title: str):
    """Update session title"""
    try:
        session = chat_db.update_session_title(session_id, title)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return {
            "success": True,
            "session": session.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/sessions/{session_id}", tags=["History"])
async def delete_session(session_id: int, permanent: bool = False):
    """Delete or archive a session"""
    try:
        if permanent:
            success = chat_db.delete_session(session_id)
        else:
            success = chat_db.archive_session(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/session", response_model=ChatResponse, tags=["Chat", "History"])
async def chat_with_session(request: ChatWithSessionRequest):
    """Chat with auto-save to session history"""
    try:
        # Create session if not provided
        session_id = request.session_id
        if not session_id:
            session = chat_db.create_session(persona=request.persona)
            session_id = session.id
        
        # Get history from database
        history_dicts = chat_db.get_session_history(session_id)
        
        logger.info(f"Chat with session {session_id} - Persona: {request.persona}")
        
        # Save user message
        chat_db.add_message(session_id, "user", request.message)
        
        # Get AI response
        result = ai_service.get_response(
            message=request.message,
            persona_key=request.persona,
            history=history_dicts,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # Save assistant response
        response_time = result.get("metadata", {}).get("duration_seconds", "")
        chat_db.add_message(
            session_id, 
            "assistant", 
            result["response"],
            response_time=str(response_time) if response_time else None
        )
        
        if result.get("error"):
            return ChatResponse(
                success=False,
                response=result["response"],
                persona={"name": "System", "avatar": "", "key": "error"},
                error=result.get("error_message")
            )
        
        # Add session_id to metadata
        metadata = result.get("metadata", {})
        metadata["session_id"] = session_id
        
        return ChatResponse(
            success=True,
            response=result["response"],
            persona=result["persona"],
            metadata=metadata
        )
        
    except Exception as e:
        logger.error(f"Chat with session error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== VOICE ENDPOINTS =====

@app.post("/voice/tts", response_model=VoiceResponse, tags=["Voice"])
async def text_to_speech(request: VoiceRequest):
    """Convert text to speech - Iroha speaks"""
    try:
        logger.info(f"TTS request - Voice: {request.voice}, Text length: {len(request.text)}")
        
        audio_file = await voice_service.iroha_speak(
            text=request.text,
            voice_preference=request.voice,
            play_audio=request.play_audio
        )
        
        logger.info(f"TTS generated: {audio_file}")
        return VoiceResponse(
            success=True,
            audio_file=audio_file
        )
        
    except Exception as e:
        logger.error(f"TTS error: {str(e)}")
        return VoiceResponse(
            success=False,
            error=str(e)
        )

@app.get("/voice/audio/{filename}", tags=["Voice"])
async def get_audio_file(filename: str):
    """Download/stream audio file"""
    try:
        audio_path = voice_service.output_dir / filename
        if not audio_path.exists():
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        return FileResponse(
            path=str(audio_path),
            media_type="audio/mpeg",
            filename=filename
        )
    except Exception as e:
        logger.error(f"Error serving audio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice/stt", tags=["Voice"])
async def speech_to_text(audio: UploadFile = File(...), language: str = "ja-JP"):
    """Convert speech to text - User speaks"""
    try:
        logger.info(f"STT request - File: {audio.filename}, Language: {language}")
        
        # Save uploaded audio temporarily
        temp_file = voice_service.output_dir / f"temp_{audio.filename}"
        with open(temp_file, "wb") as f:
            content = await audio.read()
            f.write(content)
        
        # Recognize speech
        text = voice_service.speech_to_text(
            audio_file=str(temp_file),
            language=language
        )
        
        # Cleanup temp file
        temp_file.unlink()
        
        if text:
            logger.info(f"STT result: {text}")
            return {
                "success": True,
                "text": text,
                "language": language
            }
        else:
            return {
                "success": False,
                "text": None,
                "error": "Could not recognize speech"
            }
            
    except Exception as e:
        logger.error(f"STT error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/voice/voices", tags=["Voice"])
async def get_available_voices():
    """Get list of available voices"""
    return {
        "voices": voice_service.get_available_voices(),
        "default": voice_service.default_voice
    }

@app.post("/voice/groq/stream", tags=["Voice", "Groq"])
async def groq_voice_stream(
    text: str,
    voice: str = "Fritz-PlayAI",
    speed: float = 1.05,
    sample_rate: int = 48000
):
    """Stream Iroha voice in real-time using Groq PlayAI TTS"""
    try:
        logger.info(f"Groq streaming TTS - Voice: {voice}, Speed: {speed}")
        
        async def audio_generator():
            async for chunk in groq_voice.stream_audio(
                text=text,
                voice=voice,
                speed=speed
            ):
                yield chunk
        
        return StreamingResponse(
            audio_generator(),
            media_type="audio/wav",
            headers={
                "Content-Disposition": "inline",
                "X-Voice": voice
            }
        )
        
    except Exception as e:
        logger.error(f"Groq streaming error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice/groq/file", tags=["Voice", "Groq"])
async def groq_voice_file(
    text: str,
    voice: str = "Fritz-PlayAI",
    speed: float = 1.05,
    sample_rate: int = 48000
):
    """Generate Iroha voice file using Groq PlayAI TTS"""
    try:
        logger.info(f"Groq file TTS - Voice: {voice}, Speed: {speed}")
        
        audio_file = await groq_voice.save_audio_file(
            text=text,
            voice=voice,
            speed=speed
        )
        
        logger.info(f"Groq audio generated: {audio_file}")
        return {
            "success": True,
            "audio_file": audio_file,
            "voice": voice
        }
        
    except Exception as e:
        logger.error(f"Groq file generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/voice/groq/config", tags=["Voice", "Groq"])
async def get_groq_config():
    """Get Groq PlayAI voice config (voices, speed range, sample rates)"""
    return groq_voice.get_config()

@app.post("/chat/voice", tags=["Chat", "Voice"])
async def chat_with_voice(request: ChatRequest, voice: str = "iroha_jp"):
    """Chat endpoint with voice response"""
    try:
        logger.info(f"Voice chat request - Persona: {request.persona}")
        
        # Get text response
        history_dicts = [
            {"role": h.role, "content": h.content} 
            for h in request.history
        ] if request.history else []
        
        result = ai_service.get_response(
            message=request.message,
            persona_key=request.persona,
            history=history_dicts,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        if result.get("error"):
            return ChatResponse(
                success=False,
                response=result["response"],
                persona={"name": "System", "avatar": "", "key": "error"},
                error=result.get("error_message")
            )
        
        # Generate voice for response
        audio_file = await voice_service.iroha_speak(
            text=result["response"],
            voice_preference=voice,
            play_audio=False
        )
        
        # Add audio_file to metadata
        metadata = result.get("metadata", {})
        metadata["audio_file"] = audio_file
        
        logger.info("Voice chat response generated")
        return ChatResponse(
            success=True,
            response=result["response"],
            persona=result["persona"],
            metadata=metadata
        )
        
    except Exception as e:
        logger.error(f"Voice chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/voice/groq/stream", tags=["Chat", "Voice", "Groq"])
async def chat_with_groq_voice_stream(request: ChatRequest, speed: float = 1.05):
    """Chat with Iroha and get real-time streaming voice response (Groq PlayAI)"""
    try:
        logger.info(f"Groq voice chat stream - Persona: {request.persona}")
        
        # Get text response
        history_dicts = [
            {"role": h.role, "content": h.content} 
            for h in request.history
        ] if request.history else []
        
        result = ai_service.get_response(
            message=request.message,
            persona_key=request.persona,
            history=history_dicts,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        if result.get("error"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error_message", "AI service error")
            )
        
        response_text = result["response"]
        
        # Stream audio
        async def audio_generator():
            # First chunk: send metadata as JSON
            metadata = {
                "type": "metadata",
                "text": response_text,
                "persona": result["persona"]
            }
            yield (json.dumps(metadata) + "\n").encode()
            
            # Stream audio chunks
            async for chunk in groq_voice.stream_audio(
                text=response_text,
                speed=speed
            ):
                yield chunk
        
        return StreamingResponse(
            audio_generator(),
            media_type="application/octet-stream",
            headers={
                "X-Response-Text": response_text[:200]  # Truncated for header
            }
        )
        
    except Exception as e:
        logger.error(f"Groq voice chat stream error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== WEBSOCKET (For real-time chat) =====

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected - Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected - Total: {len(self.active_connections)}")
    
    async def send_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time chat"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            message = data.get("message")
            persona = data.get("persona", "iroha")
            history = data.get("history", [])
            
            logger.info(f"WebSocket message received - Persona: {persona}")
            
            # Get AI response
            result = ai_service.get_response(
                message=message,
                persona_key=persona,
                history=history
            )
            
            # Send response back
            await manager.send_message(result, websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected from WebSocket")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket)

# ===== STARTUP/SHUTDOWN EVENTS =====

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Iroha AI Study Buddy Backend")
    logger.info(f"Persona: Isshiki Iroha")
    logger.info(f"AI Model: {ai_service.model}")
    logger.info(f"Voice: Edge TTS (Free) + Groq PlayAI TTS (Streaming)")
    logger.info("Backend ready")
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Iroha AI Study Buddy Backend")
    logger.info("Goodbye")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

