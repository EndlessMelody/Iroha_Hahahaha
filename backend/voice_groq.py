"""
Groq Voice Service - TTS with PlayAI
Uses Groq's PlayAI-TTS for high-quality text-to-speech
Sử dụng cùng GROQ_API_KEY như AI service
"""
import os
import asyncio
from pathlib import Path
from groq import AsyncGroq
from dotenv import load_dotenv
from loguru import logger
from typing import Optional, AsyncGenerator, Dict

load_dotenv()

# Configure logger
logger.add("logs/voice_groq_{time}.log", rotation="1 day", retention="7 days")

class GroqVoiceService:
    """
    Groq Voice Service for Iroha AI
    - TTS with PlayAI model
    - Multiple voice options
    - Same API key as text generation
    """
    
    def __init__(self):
        """Initialize Groq voice service"""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.warning("GROQ_API_KEY not found in .env")
        
        self.client = AsyncGroq(api_key=api_key)
        
        # Available FEMALE voices from PlayAI TTS (Groq valid voices only)
        self.available_voices = {
            "Arista-PlayAI": "🌸 Sweet & cute - BEST FOR IROHA",
            "Celeste-PlayAI": "✨ Elegant & warm",
            "Aaliyah-PlayAI": "💕 Friendly & cheerful",
            "Ruby-PlayAI": "🎀 Soft & gentle",
            "Jennifer-PlayAI": "💫 Clear & expressive",
            "Nia-PlayAI": "🌺 Warm & soothing",
            "Quinn-PlayAI": "🦋 Lively & bright",
            "Adelaide-PlayAI": "🌷 Sweet & melodic",
        }
        
        # Default voice for Iroha - Female cute voice
        self.default_voice = "Arista-PlayAI"
        self.model = "playai-tts"
        
        self.output_dir = Path("voice_outputs")
        self.output_dir.mkdir(exist_ok=True)
        # Allowed sample rates for PlayAI
        self.allowed_sample_rates = {8000, 16000, 22050, 24000, 32000, 44100, 48000}
        self.default_sample_rate = 48000
        self.min_speed = 0.5
        self.max_speed = 2.0
        
        logger.info("Groq Voice Service initialized")
    
    async def generate_audio(
        self,
        text: str,
        voice: str = "Fritz-PlayAI",
        speed: float = 1.05,
        sample_rate: int = 48000
    ) -> bytes:
        """
        Generate audio from text
        
        Args:
            text: Text to convert to speech
            voice: Voice name (Fritz-PlayAI, Angelo-PlayAI, Stella-PlayAI)
            speed: Speech speed (0.5 to 5.0)
            sample_rate: Audio sample rate (8000-48000)
            
        Returns:
            Audio bytes (WAV format)
        """
        try:
            if voice not in self.available_voices:
                logger.warning(f"Unknown voice '{voice}', using default '{self.default_voice}'")
                voice = self.default_voice
            # Clamp speed to allowed range
            speed = max(self.min_speed, min(self.max_speed, speed))
            # Validate sample rate
            if sample_rate not in self.allowed_sample_rates:
                logger.warning(f"Invalid sample_rate {sample_rate}, using {self.default_sample_rate}")
                sample_rate = self.default_sample_rate
            
            logger.info(f"Generating TTS - Voice: {voice}, Speed: {speed}")
            
            # Generate audio with Groq PlayAI
            response = await self.client.audio.speech.create(
                model=self.model,
                voice=voice,
                input=text,
                speed=speed,
                sample_rate=sample_rate,
                response_format="wav"
            )
            
            logger.info("TTS generation completed")
            # Read the response content
            return await response.read()
            
        except Exception as e:
            logger.error(f"TTS generation error: {str(e)}")
            raise

    def get_config(self) -> Dict:
        """Return voice config for UI/API consumers"""
        return {
            "voices": self.available_voices,
            "default_voice": self.default_voice,
            "recommended": "Fritz-PlayAI",
            "speed_min": self.min_speed,
            "speed_max": self.max_speed,
            "default_speed": 1.05,
            "sample_rates": sorted(self.allowed_sample_rates),
            "default_sample_rate": self.default_sample_rate,
        }
    
    async def stream_audio(
        self,
        text: str,
        voice: str = "Fritz-PlayAI",
        speed: float = 1.05
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream audio (generates full audio then yields)
        
        Args:
            text: Text to convert
            voice: Voice name
            speed: Speech speed
            
        Yields:
            Audio chunks
        """
        audio_bytes = await self.generate_audio(text, voice, speed)
        # Yield in chunks for streaming
        chunk_size = 4096
        for i in range(0, len(audio_bytes), chunk_size):
            yield audio_bytes[i:i + chunk_size]
    
    async def save_audio_file(
        self,
        text: str,
        output_file: Optional[str] = None,
        voice: str = "Fritz-PlayAI",
        speed: float = 1.05
    ) -> str:
        """
        Generate and save audio file
        
        Args:
            text: Text to convert
            output_file: Optional output filename
            voice: Voice name
            speed: Speech speed
            
        Returns:
            Path to saved file
        """
        try:
            if output_file is None:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = self.output_dir / f"iroha_groq_{timestamp}.wav"
            else:
                file_path = self.output_dir / output_file
            
            logger.info(f"Saving audio file: {file_path}")
            
            # Generate audio
            audio_bytes = await self.generate_audio(text, voice, speed)
            
            # Save to file
            with open(file_path, "wb") as f:
                f.write(audio_bytes)
            
            logger.info(f"Audio file saved: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Save audio error: {str(e)}")
            raise
    
    def get_available_voices(self) -> dict:
        """Get list of available voices"""
        return self.available_voices
    
    async def iroha_speak(
        self,
        text: str,
        save_file: bool = False
    ):
        """
        Make Iroha speak
        
        Args:
            text: Text for Iroha to speak
            save_file: Whether to save to file (True) or return bytes (False)
            
        Returns:
            Audio file path if save_file=True, else audio bytes
        """
        if save_file:
            return await self.save_audio_file(text, voice=self.default_voice, speed=1.05)
        else:
            return await self.generate_audio(text, voice=self.default_voice, speed=1.05)

# Global instance
groq_voice = GroqVoiceService()

# Quick helper functions
async def iroha_speak_bytes(text: str):
    """Quick helper to get Iroha speech as bytes"""
    return await groq_voice.iroha_speak(text, save_file=False)

async def iroha_speak_file(text: str):
    """Quick helper to save Iroha speech to file"""
    return await groq_voice.iroha_speak(text, save_file=True)

async def iroha_stream(text: str) -> AsyncGenerator[bytes, None]:
    """Quick helper to stream Iroha speech"""
    async for chunk in groq_voice.stream_audio(text):
        yield chunk

# Test function
async def test_groq_voice():
    """Test Groq voice service"""
    print("Testing Groq Voice Service...")
    print()
    
    print(f"Available voices: {list(groq_voice.get_available_voices().keys())}")
    print(f"Default voice: {groq_voice.default_voice}")
    print()
    
    test_texts = [
        "Senpaaaai! Hôm nay chúng ta học gì nè?",
        "Eehh? Senpai cần giúp à? Finee, tớ sẽ giúp đây!",
        "Senpai đã làm tốt lắm! Tớ tự hào về Senpai!",
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"[Test {i}]")
        print(f"Text: {text}")
        
        try:
            # Test file generation
            audio_file = await iroha_speak_file(text)
            print(f"✓ File generated: {audio_file}")
            
            # Test streaming
            chunk_count = 0
            async for chunk in iroha_stream(text):
                chunk_count += 1
            print(f"✓ Streaming: {chunk_count} chunks")
            
        except Exception as e:
            print(f"✗ Error: {str(e)}")
        
        print()
    
    print("Groq Voice Service test complete!")

if __name__ == "__main__":
    asyncio.run(test_groq_voice())
