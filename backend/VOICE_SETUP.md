# Iroha Voice Service Setup

## Voice Capabilities

Backend giờ đã có đầy đủ chức năng voice:

### 1. Text-to-Speech (TTS)

- **Edge TTS**: Free, high-quality Microsoft voices
- **Giọng nói có sẵn**:
  - `iroha_jp`: Giọng Nhật nữ trẻ, dễ thương (NanamiNeural) - **Default**
  - `iroha_jp_alt`: Giọng Nhật nữ thay thế (AoiNeural)
  - `iroha_en`: Giọng Anh nữ biểu cảm (AriaNeural)
  - `iroha_vi`: Giọng Việt nữ (HoaiMyNeural)

### 2. Speech-to-Text (STT)

- **Google Speech Recognition**: Nhận dạng giọng nói từ file audio hoặc microphone
- **Hỗ trợ ngôn ngữ**: Japanese (ja-JP), English (en-US), Vietnamese (vi-VN)

## Installation

### Step 1: Install Python packages

```powershell
pip install -r requirements.txt
```

**Note**: PyAudio có thể cần cài đặt thủ công trên Windows:

```powershell
pip install pipwin
pipwin install pyaudio
```

Hoặc download wheel file từ: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

### Step 2: Test voice service

```powershell
python demo_voice.py
```

## API Endpoints

### 1. Text-to-Speech (Iroha nói)

```bash
POST /voice/tts
{
  "text": "Senpaaaai! Hôm nay học gì nè?",
  "voice": "iroha_jp",
  "play_audio": false
}
```

Response:

```json
{
  "success": true,
  "audio_file": "voice_outputs/iroha_voice_20241211_143052.mp3"
}
```

### 2. Get Audio File

```bash
GET /voice/audio/{filename}
```

Returns MP3 audio file để play hoặc download

### 3. Speech-to-Text (User nói)

```bash
POST /voice/stt
Content-Type: multipart/form-data

audio: [audio file]
language: "ja-JP"
```

Response:

```json
{
  "success": true,
  "text": "今日は何を勉強しますか",
  "language": "ja-JP"
}
```

### 4. Get Available Voices

```bash
GET /voice/voices
```

Response:

```json
{
  "voices": {
    "iroha_jp": "ja-JP-NanamiNeural",
    "iroha_jp_alt": "ja-JP-AoiNeural",
    "iroha_en": "en-US-AriaNeural",
    "iroha_vi": "vi-VN-HoaiMyNeural"
  },
  "default": "iroha_jp"
}
```

### 5. Chat with Voice Response

```bash
POST /chat/voice?voice=iroha_jp
{
  "message": "Giải thích cho tớ về đạo hàm",
  "persona": "iroha",
  "history": []
}
```

Response includes both text and audio file:

```json
{
  "success": true,
  "response": "Eehh, đạo hàm à Senpai? :> ...",
  "persona": {
    "name": "Isshiki Iroha",
    "avatar": "(๑˃ᴗ˂)و",
    "key": "iroha"
  },
  "metadata": {
    "audio_file": "voice_outputs/iroha_voice_20241211_143052.mp3",
    "tokens_used": 245
  }
}
```

## Usage Examples

### Python Client

```python
import asyncio
from voice_service import voice_service
from ai_core import ai_service

async def chat_with_voice():
    # Get AI response
    result = ai_service.get_response(
        message="Tớ đang stress vì thi",
        persona_key="iroha"
    )

    # Generate voice
    audio_file = await voice_service.iroha_speak(
        text=result['response'],
        voice_preference="iroha_jp"
    )

    print(f"Text: {result['response']}")
    print(f"Audio: {audio_file}")

    # Optional: Play audio
    await voice_service.play_audio(audio_file)

asyncio.run(chat_with_voice())
```

### JavaScript/Frontend

```javascript
// Chat with voice
async function chatWithVoice(message) {
  const response = await fetch(
    "http://localhost:8000/chat/voice?voice=iroha_jp",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: message,
        persona: "iroha",
      }),
    }
  );

  const data = await response.json();

  // Display text
  console.log("Iroha:", data.response);

  // Play audio
  if (data.metadata?.audio_file) {
    const audio = new Audio(
      `http://localhost:8000/voice/audio/${data.metadata.audio_file
        .split("/")
        .pop()}`
    );
    audio.play();
  }
}
```

## Voice Configuration

Customize trong [config.py](config.py):

```python
# Voice Configuration
DEFAULT_TTS_VOICE = "iroha_jp"
DEFAULT_STT_LANGUAGE = "ja-JP"
VOICE_RATE = "+15%"      # Speech speed
VOICE_PITCH = "+8Hz"     # Voice pitch (higher = cuter)
```

## Notes

- Audio files lưu trong `voice_outputs/` directory
- Format: MP3, tương thích mọi browser/player
- Edge TTS hoàn toàn **free** và không cần API key
- Giọng Japanese sẽ phù hợp nhất với anime character personality
- Có thể adjust `rate` và `pitch` để customize giọng nói

## Next Steps

Có thể tạo:

1. **Voice Chat UI** - Frontend với microphone input và audio playback
2. **Voice Chat Terminal** - Terminal app với voice I/O
3. **Voice Conversation Mode** - Hands-free voice conversation
4. **Multi-language Support** - Auto-detect và switch giọng theo ngôn ngữ

---

**Iroha is ready to speak! (๑˃ᴗ˂)و**
