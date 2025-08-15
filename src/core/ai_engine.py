"""
AI Engine Module - Content-Filter Resistant
The Third Voice - Works around AI model limitations
Built to handle real human communication
"""

import json
import requests
from enum import Enum
from ..data.models import AIResponse
from ..config.settings import AppConfig


class MessageType(Enum):
    TRANSFORM = "transform"
    INTERPRET = "interpret"


class RelationshipContext(Enum):
    ROMANTIC = "romantic"
    COPARENTING = "coparenting" 
    WORKPLACE = "workplace"
    FAMILY = "family"
    FRIEND = "friend"
    
    @property
    def emoji(self):
        return {
            "romantic": "💕", "coparenting": "👨‍👩‍👧‍👦", "workplace": "🏢", 
            "family": "🏠", "friend": "🤝"
        }[self.value]
    
    @property 
    def description(self):
        return {
            "romantic": "Partner & intimate relationships", "coparenting": "Raising children together",
            "workplace": "Professional relationships", "family": "Extended family connections", 
            "friend": "Friendships & social bonds"
        }[self.value]


class AIEngine:
    """AI engine that works around content filtering"""
    
    def __init__(self):
        self.models = [
            {"id": "deepseek/deepseek-chat-v3-0324:free", "name": "DeepSeek Chat v3"},
            {"id": "deepseek/deepseek-r1-distill-llama-70b:free", "name": "DeepSeek R1 Distill"},
            {"id": "meta-llama/llama-3.2-3b-instruct:free", "name": "Llama 3.2 3B"},
            {"id": "qwen/qwen-2.5-7b-instruct:free", "name": "Qwen 2.5 7B"},
            {"id": "google/gemma-2-9b-it:free", "name": "Gemma 2 9B"}
        ]
    
    def _sanitize_message(self, message: str) -> str:
        sanitized = message.replace("bitch", "[expletive]")
        sanitized = sanitized.replace("vagina", "[inappropriate reference]")
        sanitized = sanitized.replace("deport", "remove from country")
        return sanitized
    
    def _try_model(self, model_info: dict, system_prompt: str, user_prompt: str) -> dict:
        api_key = AppConfig.get_openrouter_api_key()
        if not api_key:
            print("❌ ERROR: No OpenRouter API key found!")
            return None
        
        try:
            response = requests.post(
                f"{AppConfig.OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model_info["id"],
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.7
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and result["choices"]:
                    return result
            
            print(f"❌ Model {model_info['name']} failed: Status {response.status_code}")
            return None
            
        except Exception as e:
            print(f"❌ Error with {model_info['name']}: {str(e)}")
            return None
    
    def process_message(self, message: str, contact_context: str, message_type: str,
                       contact_id: str, user_id: str, db) -> AIResponse:
        system_prompt, user_prompts = "", []
        
        if message_type == MessageType.TRANSFORM.value:
            system_prompt = """You are a communication helper. Rewrite messages to be more constructive and healing while keeping the core meaning. Respond with JSON:
{"transformed_message": "rewritten message", "healing_score": 7, "sentiment": "positive", "emotional_state": "caring", "explanation": "why this helps"}"""
            user_prompts = [
                f'Please rewrite this message to be more constructive: "{message}"',
                f'Please rewrite this message to be more constructive: "{self._sanitize_message(message)}"'
            ]
        else:  # INTERPRET
            system_prompt = """You are a communication helper. Interpret what someone really means beneath their words, even when they're upset. Suggest compassionate responses. Respond with JSON:
{"transformed_message": "suggested response", "healing_score": 6, "sentiment": "neutral", "emotional_state": "understanding", "explanation": "what they really mean", "subtext": "their deeper feelings", "needs": ["emotional needs"], "warnings": []}"""
            user_prompts = [
                f'Help me understand what they really mean and how to respond compassionately: "{message}"',
                f'Help me understand what they really mean and how to respond compassionately: "{self._sanitize_message(message)}"'
            ]
        
        for model_info in self.models:
            for prompt in user_prompts:
                result = self._try_model(model_info, system_prompt, prompt)
                if result:
                    try:
                        ai_text = result["choices"][0]["message"]["content"]
                        start = ai_text.find('{')
                        end = ai_text.rfind('}') + 1
                        ai_data = json.loads(ai_text[start:end])
                        return AIResponse(
                            transformed_message=ai_data.get("transformed_message", "I understand this is difficult."),
                            healing_score=int(ai_data.get("healing_score", 5)),
                            sentiment=ai_data.get("sentiment", "neutral"),
                            emotional_state=ai_data.get("emotional_state", "understanding"),
                            explanation=ai_data.get("explanation", "Providing support"),
                            subtext=ai_data.get("subtext", ""),
                            needs=ai_data.get("needs", []),
                            warnings=ai_data.get("warnings", []),
                            model_used=model_info["name"],
                            model_id=model_info["id"]
                        )
                    except:
                        continue
        
        # Fallback if all models fail
        return AIResponse(
            transformed_message="I can see you're dealing with a lot right now. I'm here to support you.",
            healing_score=5, sentiment="neutral", emotional_state="understanding",
            explanation="Fallback response", model_used="Fallback System", model_id="fallback"
        )
