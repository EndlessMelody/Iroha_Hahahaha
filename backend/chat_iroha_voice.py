"""
Interactive Voice Chat with Iroha
Chat with Iroha - She will respond in text AND voice!
Iroha sẽ vừa trả lời text vừa đọc cho bạn nghe luôn
"""
import os
import sys
import asyncio
from pathlib import Path
from ai_core import ai_service
from voice_groq import groq_voice
from loguru import logger
import tempfile
import subprocess

# Configure logger
logger.add("logs/chat_voice_{time}.log", rotation="1 day", retention="7 days")

class IrohaVoiceChat:
    """Interactive voice chat with Iroha"""
    
    def __init__(self):
        self.history = []
        self.temp_dir = Path(tempfile.gettempdir()) / "iroha_voice"
        self.temp_dir.mkdir(exist_ok=True)
        self.save_audio_files = False
        self.text_only = False
        self.voice_choice = "Fritz-PlayAI"
        self.speed = 1.05
        
        print("=" * 70)
        print("   IROHA VOICE CHAT - Interactive Mode")
        print("=" * 70)
        print()
        print("Iroha will respond with text and optional voice.")
        print()
        print("Commands:")
        print("  - Type message to chat")
        print("  - '/voice fritz|angelo|stella' select voice")
        print("  - '/speed 0.8' set speed (0.5-2.0)")
        print("  - '/textonly on|off' toggle voice output")
        print("  - '/save on|off' save audio to temp")
        print("  - '/history' view history, '/clear' clear history")
        print("  - '/export' save history to .txt")
        print("  - '/help' show help, 'quit' to exit")
        print()
        print("=" * 70)
        print()
    
    async def play_audio(self, audio_bytes: bytes):
        """Play audio bytes directly using OS media player"""
        try:
            # Save to temp file
            temp_file = self.temp_dir / f"temp_voice_{os.getpid()}.wav"
            with open(temp_file, "wb") as f:
                f.write(audio_bytes)
            
            # Save for later if user wants to keep audio
            if self.save_audio_files:
                keep_path = self.temp_dir / f"iroha_voice_{os.getpid()}.wav"
                keep_path.write_bytes(audio_bytes)
                print(f"Saved audio: {keep_path}")
            
            # Play using Windows default player (silent, no window)
            if sys.platform == "win32":
                subprocess.run(
                    ["powershell", "-c", 
                     f"(New-Object Media.SoundPlayer '{temp_file}').PlaySync()"],
                    capture_output=True
                )
            else:
                subprocess.run(["aplay", str(temp_file)], capture_output=True)
            
            temp_file.unlink(missing_ok=True)
            
        except Exception as e:
            logger.error(f"Audio playback error: {str(e)}")
            print(f"Warning: Could not play audio: {str(e)}")
    
    async def get_iroha_response(self, message: str):
        """Get text response from Iroha and (optionally) play voice"""
        try:
            print("\nIroha is thinking...")
            
            result = ai_service.get_response(
                message=message,
                persona_key="iroha",
                history=self.history
            )
            
            if result.get("error"):
                print(f"\n❌ Error: {result.get('error_message')}")
                return
            
            response_text = result["response"]
            
            # Update history
            self.history.append({"role": "user", "content": message})
            self.history.append({"role": "assistant", "content": response_text})
            
            # Display text response
            print(f"\n{result['persona']['name']} ({result['persona']['key']}):")
            print(response_text)
            print(f"\nResponse time: {result['metadata']['duration_seconds']:.2f}s")
            
            # Voice generation (skip if text-only)
            if self.text_only:
                print("\nText-only mode is ON. Skipping voice.")
                return
            
            print(f"\nGenerating voice... (Voice: {self.voice_choice}, Speed: {self.speed})")
            
            audio_bytes = await groq_voice.generate_audio(
                text=response_text,
                voice=self.voice_choice,
                speed=self.speed
            )
            
            print("Playing audio...")
            await self.play_audio(audio_bytes)
            
            print("\nDone.")
            
        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            print(f"\nError: {str(e)}")
            
            if "model_terms_required" in str(e):
                print("\nGroq PlayAI TTS requires terms acceptance.")
                print("Visit: https://console.groq.com/playground?model=playai-tts")
                print("You can turn on text-only mode: /textonly on")
    
    def print_help(self):
        print("\nCommands:")
        print("  /voice fritz|angelo|stella   - select voice")
        print("  /speed 0.5-2.0               - set speed")
        print("  /textonly on|off             - toggle voice output")
        print("  /save on|off                 - save audio WAV")
        print("  /history                     - view history")
        print("  /export                      - save history to .txt")
        print("  /clear                       - clear history")
        print("  /help                        - show help")
        print("  quit / exit                  - exit")

    def export_history(self):
        if not self.history:
            print("\nℹ️  Chưa có lịch sử để lưu")
            return
        export_path = self.temp_dir / f"iroha_history_{os.getpid()}.txt"
        lines = []
        for msg in self.history:
            role = "You" if msg["role"] == "user" else "Iroha"
            lines.append(f"[{role}] {msg['content']}")
        export_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"\n💾 Lịch sử đã lưu: {export_path}")

    async def run(self):
        """Main chat loop"""
        try:
            while True:
                print("\n" + "-" * 70)
                user_input = input("\nYou (Senpai): ").strip()
                
                if not user_input:
                    continue
                
                cmd = user_input.lower()
                
                # Exit
                if cmd in ["quit", "exit", "q"]:
                    print("\nIroha: Bye bye, Senpai. See you next time.")
                    break
                
                # Clear history
                if cmd == "clear":
                    self.history = []
                    print("\nChat history cleared!")
                    continue
                
                # Show history
                if cmd == "history":
                    print("\nConversation History:")
                    for i, msg in enumerate(self.history, 1):
                        role = "You" if msg["role"] == "user" else "Iroha"
                        print(f"  {i}. {role}: {msg['content'][:80]}...")
                    continue
                
                # Export history
                if cmd == "export" or cmd == "/export":
                    self.export_history()
                    continue
                
                # Help
                if cmd == "help" or cmd == "/help":
                    self.print_help()
                    continue
                
                # Voice selection
                if cmd.startswith("/voice"):
                    parts = cmd.split()
                    if len(parts) == 2:
                        choice = parts[1].strip().lower()
                        mapper = {
                            "fritz": "Fritz-PlayAI",
                            "angelo": "Angelo-PlayAI",
                            "stella": "Stella-PlayAI"
                        }
                        if choice in mapper:
                            self.voice_choice = mapper[choice]
                            print(f"\n✅ Voice set to {self.voice_choice}")
                        else:
                            print("\n⚠️  Voice not recognized. Options: fritz, angelo, stella")
                    else:
                        print("\n⚠️  Usage: /voice fritz|angelo|stella")
                    continue
                
                # Speed control
                if cmd.startswith("/speed"):
                    parts = cmd.split()
                    if len(parts) == 2:
                        try:
                            new_speed = float(parts[1])
                            if 0.5 <= new_speed <= 2.0:
                                self.speed = new_speed
                                print(f"\n✅ Speed set to {self.speed}")
                            else:
                                print("\n⚠️  Speed must be between 0.5 and 2.0")
                        except ValueError:
                            print("\n⚠️  Usage: /speed 1.05")
                    else:
                        print("\n⚠️  Usage: /speed 1.05")
                    continue
                
                # Text-only toggle
                if cmd.startswith("/textonly"):
                    parts = cmd.split()
                    if len(parts) == 2 and parts[1] in ["on", "off"]:
                        self.text_only = parts[1] == "on"
                        state = "ON" if self.text_only else "OFF"
                        print(f"\n✅ Text-only mode: {state}")
                    else:
                        print("\n⚠️  Usage: /textonly on|off")
                    continue
                
                # Save audio toggle
                if cmd.startswith("/save"):
                    parts = cmd.split()
                    if len(parts) == 2 and parts[1] in ["on", "off"]:
                        self.save_audio_files = parts[1] == "on"
                        state = "ON" if self.save_audio_files else "OFF"
                        print(f"\n✅ Save audio: {state}")
                    else:
                        print("\n⚠️  Usage: /save on|off")
                    continue
                
                # Get Iroha's response with voice
                await self.get_iroha_response(user_input)
                
        except KeyboardInterrupt:
            print("\n\nChat interrupted. Goodbye, Senpai.")
        except Exception as e:
            logger.error(f"Fatal error: {str(e)}")
            print(f"\nFatal error: {str(e)}")

async def main():
    """Entry point"""
    # Check API key
    if not os.getenv("GROQ_API_KEY"):
        print("❌ Error: GROQ_API_KEY not found in .env file!")
        print("Please add your Groq API key to the .env file.")
        sys.exit(1)
    
    # Check AI service
    try:
        ai_service.client
    except Exception as e:
        print(f"❌ Error: AI service not initialized: {str(e)}")
        sys.exit(1)
    
    # Start chat
    chat = IrohaVoiceChat()
    await chat.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        print(f"❌ Startup error: {str(e)}")
        sys.exit(1)
