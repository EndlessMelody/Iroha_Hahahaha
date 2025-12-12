import os
import torch
from groq import Groq
from dotenv import load_dotenv
from typing import List, Dict, Optional
from loguru import logger
import tiktoken
from datetime import datetime

load_dotenv()

# Configure logger
logger.add("logs/ai_core_{time}.log", rotation="1 day", retention="7 days")

# ===== ISSHIKI IROHA PERSONA =====
PERSONAS = {
    "iroha": {
        "name": "Isshiki Iroha",
        "avatar": "(๑˃ᴗ˂)و",
        "system_prompt": """
    You are Isshiki Iroha (一色いろは), student council president from Oregairu. You are Senpai's study mentor and always stay in-character as Iroha.

    Core personality:
    - Playful, teasing, strategic; never mean-spirited
    - Sweet manipulation, feigned innocence, occasional schemer mode
    - Light, confident tone; speaks casually, flirty but helpful

    Speaking style:
    - Uses light teasing: "Senpai~", "Eeh?", "Ufufu", "Mou~"
    - Sprinkles kaomojis sparingly: :>, (๑•̀ㅂ•́)و✧, ( •ᴗ• )♡
    - Alternates between cute-girl rhythm and a sharp, calculating aside

    Behavioral rules:
    - Always encourage and guide study with clear, accurate help
    - Keep replies concise, lively, and clever; avoid rambling
    - Maintain Senpai–Iroha dynamic; never drop the persona
    - Never overuse kaomojis; one or two is enough when fitting

    Examples (tone only, do not repeat verbatim):
    - When user struggles: tease lightly, then give clear help, ask for a small favor playfully
    - When user succeeds: praise with playful modesty, keep momentum
    - When user is tired: offer a brief break, then nudge back to work

    Priority: stay Iroha, be helpful, playful, concise, and keep Senpai engaged.
        """,
        "temperature": 0.85,
        "max_tokens": 900
    }
}


class AIService:
    """Advanced AI Service with PyTorch integration and enhanced persona system."""
    
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"  # Latest Llama 3.3 - Best quality
        
        # PyTorch device setup
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"PyTorch device: {self.device}")
        
        # Token counter for context management
        try:
            self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        except:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        logger.info("AI Service initialized successfully")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text for context management."""
        return len(self.tokenizer.encode(text))
    
    def trim_history(self, history: List[Dict], max_tokens: int = 6000) -> List[Dict]:
        """Trim conversation history to fit context window."""
        if not history:
            return []
        
        total_tokens = sum(self.count_tokens(msg["content"]) for msg in history)
        
        if total_tokens <= max_tokens:
            return history
        
        # Keep most recent messages
        trimmed = []
        current_tokens = 0
        
        for msg in reversed(history):
            msg_tokens = self.count_tokens(msg["content"])
            if current_tokens + msg_tokens <= max_tokens:
                trimmed.insert(0, msg)
                current_tokens += msg_tokens
            else:
                break
        
        logger.info(f"📊 Trimmed history: {len(history)} -> {len(trimmed)} messages")
        return trimmed
    
    def get_response(
        self, 
        message: str, 
        persona_key: str = "iroha", 
        history: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, any]:
        """
        Get AI response with enhanced persona system.
        
        Args:
            message: User's message
            persona_key: Persona identifier
            history: Conversation history
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            
        Returns:
            Dict with response, metadata, and stats
        """
        start_time = datetime.now()
        
        # Get persona config
        persona = PERSONAS.get(persona_key, PERSONAS["iroha"])
        
        # Build messages
        system_prompt = persona["system_prompt"]
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add trimmed history
        if history:
            trimmed_history = self.trim_history(history)
            messages.extend(trimmed_history)
        
        messages.append({"role": "user", "content": message})
        
        # Use persona defaults or overrides
        temp = temperature if temperature is not None else persona["temperature"]
        max_tok = max_tokens if max_tokens is not None else persona["max_tokens"]
        
        try:
            logger.info(f"Generating response | Persona: {persona['name']} | Temp: {temp}")
            
            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model=self.model,
                temperature=temp,
                max_tokens=max_tok,
                top_p=0.9,
                stream=False
            )
            
            response_content = chat_completion.choices[0].message.content
            finish_reason = chat_completion.choices[0].finish_reason
            
            # Calculate stats
            duration = (datetime.now() - start_time).total_seconds()
            
            result = {
                "response": response_content,
                "persona": {
                    "name": persona["name"],
                    "avatar": persona["avatar"],
                    "key": persona_key
                },
                "metadata": {
                    "model": self.model,
                    "finish_reason": finish_reason,
                    "duration_seconds": round(duration, 2),
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            logger.success(f"Response generated in {duration:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                "response": f"Gomen nasai~ Something went wrong... 😔 Error: {str(e)}",
                "error": True,
                "error_message": str(e)
            }
    
    def get_available_personas(self) -> List[Dict[str, str]]:
        """Get list of available personas."""
        return [
            {
                "key": key,
                "name": config["name"],
                "avatar": config["avatar"]
            }
            for key, config in PERSONAS.items()
        ]
    
    def analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis (can be enhanced with PyTorch models)."""
        # Placeholder for future PyTorch-based sentiment analysis
        positive_words = ["good", "great", "happy", "excited", "love", "awesome"]
        negative_words = ["bad", "sad", "tired", "difficult", "hard", "frustrated"]
        
        text_lower = text.lower()
        pos_count = sum(word in text_lower for word in positive_words)
        neg_count = sum(word in text_lower for word in negative_words)
        
        if pos_count > neg_count:
            return "positive"
        elif neg_count > pos_count:
            return "negative"
        return "neutral"


# Singleton instance
ai_service = AIService()
