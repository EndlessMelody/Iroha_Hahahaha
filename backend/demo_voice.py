"""
Demo Voice Service - Test Iroha's voice capabilities
Shows TTS (Text-to-Speech) functionality
"""
import asyncio
from voice_service import voice_service
from ai_core import ai_service

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

async def demo_iroha_voice():
    """Demo Iroha speaking in different languages"""
    
    print(Colors.HEADER + "="*70)
    print("     IROHA VOICE DEMO - Text-to-Speech")
    print("="*70 + Colors.ENDC)
    print()
    
    # Test scenarios
    scenarios = [
        {
            "name": "Japanese Greeting",
            "voice": "iroha_jp",
            "text": "センパイ！今日は何を勉強しますか？頑張りましょう！"
        },
        {
            "name": "English Greeting", 
            "voice": "iroha_en",
            "text": "Senpaaaai! What are we studying today? Let's do our best!"
        },
        {
            "name": "Vietnamese Greeting",
            "voice": "iroha_vi",
            "text": "Chào Senpai! Hôm nay chúng ta học gì nè?"
        },
        {
            "name": "Study Encouragement (JP)",
            "voice": "iroha_jp",
            "text": "頑張って！センパイならできるよ！私が応援してるから！"
        }
    ]
    
    print(Colors.OKGREEN + "Available voices:" + Colors.ENDC)
    voices = voice_service.get_available_voices()
    for key, voice in voices.items():
        print(f"  - {key}: {voice}")
    print()
    
    for i, scenario in enumerate(scenarios, 1):
        print(Colors.OKCYAN + f"\n[Test {i}] {scenario['name']}" + Colors.ENDC)
        print(Colors.OKBLUE + f"Voice: {scenario['voice']}" + Colors.ENDC)
        print(Colors.WARNING + f"Text: {scenario['text']}" + Colors.ENDC)
        
        try:
            # Generate voice
            print("Generating audio...")
            audio_file = await voice_service.iroha_speak(
                text=scenario['text'],
                voice_preference=scenario['voice'],
                play_audio=False
            )
            
            print(Colors.OKGREEN + f"✓ Audio generated: {audio_file}" + Colors.ENDC)
            
            # Optional: Uncomment to play audio
            # print("Playing audio...")
            # await voice_service.play_audio(audio_file)
            
        except Exception as e:
            print(Colors.FAIL + f"✗ Error: {str(e)}" + Colors.ENDC)
        
        print()
    
    print(Colors.HEADER + "="*70)
    print("     VOICE DEMO COMPLETE")
    print("="*70 + Colors.ENDC)
    print()
    print(Colors.WARNING + "Note: Audio files saved in voice_outputs/" + Colors.ENDC)
    print(Colors.OKBLUE + "To play audio, uncomment the play_audio line in the code" + Colors.ENDC)
    print()

async def demo_chat_with_voice():
    """Demo chat with AI and voice generation"""
    
    print(Colors.HEADER + "\n" + "="*70)
    print("     IROHA CHAT + VOICE DEMO")
    print("="*70 + Colors.ENDC)
    print()
    
    questions = [
        "Giải thích cho tớ về đạo hàm nhé!",
        "Tớ đang stress vì thi, giúp tớ với",
        "Senpai làm được rồi! Khen tớ đi!"
    ]
    
    for i, question in enumerate(questions, 1):
        print(Colors.OKCYAN + f"\n[Chat {i}]" + Colors.ENDC)
        print(Colors.OKBLUE + f"User: {question}" + Colors.ENDC)
        print()
        
        try:
            # Get AI response
            result = ai_service.get_response(
                message=question,
                persona_key="iroha"
            )
            
            response_text = result['response']
            print(Colors.OKGREEN + "Iroha (Text):" + Colors.ENDC)
            print(Colors.WARNING + response_text + Colors.ENDC)
            print()
            
            # Generate voice
            print("Generating voice...")
            audio_file = await voice_service.iroha_speak(
                text=response_text,
                voice_preference="iroha_jp"
            )
            
            print(Colors.OKGREEN + f"✓ Voice: {audio_file}" + Colors.ENDC)
            
        except Exception as e:
            print(Colors.FAIL + f"✗ Error: {str(e)}" + Colors.ENDC)
        
        print()
    
    print(Colors.HEADER + "="*70)
    print("     CHAT + VOICE DEMO COMPLETE")
    print("="*70 + Colors.ENDC)
    print()

async def main():
    """Run all demos"""
    
    print(Colors.BOLD + Colors.HEADER)
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║                    IROHA VOICE SERVICE DEMO                       ║")
    print("║                Text-to-Speech + AI Integration                    ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print(Colors.ENDC)
    print()
    
    # Run voice demo
    await demo_iroha_voice()
    
    # Run chat + voice demo
    await demo_chat_with_voice()
    
    print(Colors.OKGREEN + "All demos complete! (๑˃ᴗ˂)و" + Colors.ENDC)
    print()

if __name__ == "__main__":
    asyncio.run(main())
