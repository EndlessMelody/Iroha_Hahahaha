"""
Voice Service for Iroha AI - Text-to-Speech and Speech-to-Text
Provides voice interaction capabilities using Edge TTS and Speech Recognition
"""
import asyncio
import os
from pathlib import Path
import edge_tts
import speech_recognition as sr
from loguru import logger
from typing import Optional, Dict, List
from pydub import AudioSegment
from pydub.playback import play
import io

# Configure logger
logger.add("logs/voice_{time}.log", rotation="1 day", retention="7 days")

class VoiceService:
    """
    Voice service for Iroha AI study buddy
    - TTS: Convert Iroha's text responses to voice
    - STT: Convert user's voice to text
    """
    
    def __init__(self):
        """Initialize voice service with Edge TTS and Speech Recognition"""
        # Edge TTS voices (Japanese female voices for anime character feel)
        self.available_voices = {
            "iroha_jp": "ja-JP-NanamiNeural",      # Japanese female, young and cute
            "iroha_jp_alt": "ja-JP-AoiNeural",     # Japanese female, alternative
            "iroha_en": "en-US-AriaNeural",        # English female, expressive
            "iroha_vi": "vi-VN-HoaiMyNeural",      # Vietnamese female
        }
        
        self.default_voice = "iroha_jp"
        self.speech_recognizer = sr.Recognizer()
        self.output_dir = Path("voice_outputs")
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info("Voice service initialized")
    
    async def text_to_speech(
        self,
        text: str,
        voice_key: str = "iroha_jp",
        rate: str = "+10%",
        pitch: str = "+5Hz",
        output_file: Optional[str] = None
    ) -> str:
        """
        Convert text to speech using Edge TTS
        
        Args:
            text: Text to convert to speech
            voice_key: Voice identifier from available_voices
            rate: Speech rate (+/-50%)
            pitch: Voice pitch adjustment
            output_file: Optional output filename
            
        Returns:
            Path to generated audio file
        """
        try:
            voice = self.available_voices.get(voice_key, self.available_voices[self.default_voice])
            
            if output_file is None:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = self.output_dir / f"iroha_voice_{timestamp}.mp3"
            else:
                output_file = self.output_dir / output_file
            
            # Create TTS communicate
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=rate,
                pitch=pitch
            )
            
            # Save audio file
            await communicate.save(str(output_file))
            
            logger.info(f"TTS generated: {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"TTS error: {str(e)}")
            raise
    
    def speech_to_text(
        self,
        audio_file: Optional[str] = None,
        language: str = "ja-JP",
        timeout: int = 5
    ) -> Optional[str]:
        """
        Convert speech to text using Speech Recognition
        
        Args:
            audio_file: Path to audio file, or None to use microphone
            language: Language code (ja-JP, en-US, vi-VN)
            timeout: Timeout for microphone listening
            
        Returns:
            Recognized text or None
        """
        try:
            if audio_file:
                # Recognize from audio file
                with sr.AudioFile(audio_file) as source:
                    audio_data = self.speech_recognizer.record(source)
                    text = self.speech_recognizer.recognize_google(
                        audio_data,
                        language=language
                    )
                    logger.info(f"STT from file: {text}")
                    return text
            else:
                # Recognize from microphone
                with sr.Microphone() as source:
                    logger.info("Listening from microphone...")
                    self.speech_recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio_data = self.speech_recognizer.listen(source, timeout=timeout)
                    
                    text = self.speech_recognizer.recognize_google(
                        audio_data,
                        language=language
                    )
                    logger.info(f"STT from mic: {text}")
                    return text
                    
        except sr.WaitTimeoutError:
            logger.warning("STT timeout - no speech detected")
            return None
        except sr.UnknownValueError:
            logger.warning("STT could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error(f"STT API error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"STT error: {str(e)}")
            return None
    
    async def play_audio(self, audio_file: str):
        """
        Play audio file
        
        Args:
            audio_file: Path to audio file to play
        """
        try:
            audio = AudioSegment.from_file(audio_file)
            play(audio)
            logger.info(f"Played audio: {audio_file}")
        except Exception as e:
            logger.error(f"Error playing audio: {str(e)}")
            raise
    
    def get_available_voices(self) -> Dict[str, str]:
        """Get list of available voices"""
        return self.available_voices
    
    async def iroha_speak(
        self,
        text: str,
        voice_preference: str = "iroha_jp",
        play_audio: bool = False
    ) -> str:
        """
        Convenience method for Iroha to speak
        
        Args:
            text: Text for Iroha to speak
            voice_preference: Voice to use
            play_audio: Whether to play audio immediately
            
        Returns:
            Path to audio file
        """
        audio_file = await self.text_to_speech(
            text=text,
            voice_key=voice_preference,
            rate="+15%",  # Slightly faster for energetic feel
            pitch="+8Hz"   # Higher pitch for cute voice
        )
        
        if play_audio:
            await self.play_audio(audio_file)
        
        return audio_file

# Global voice service instance
voice_service = VoiceService()

# Async helper for quick usage
async def make_iroha_speak(text: str, voice: str = "iroha_jp") -> str:
    """Quick helper to make Iroha speak"""
    return await voice_service.iroha_speak(text, voice)

# Test function
async def test_voice():
    """Test voice service"""
    print("Testing Voice Service...")
    
    # Test TTS
    test_text = "Senpaaaai! Hôm nay chúng ta học gì nè? (๑˃ᴗ˂)و"
    print(f"Text: {test_text}")
    
    audio_file = await voice_service.iroha_speak(test_text, "iroha_jp")
    print(f"Audio generated: {audio_file}")
    
    # Uncomment to play audio
    # await voice_service.play_audio(audio_file)
    
    print("Voice service test complete")

if __name__ == "__main__":
    asyncio.run(test_voice())
