"""
AI Engine Module - Bare Bones & Maximum Freedom
The Third Voice - Let AI be intelligent without restrictions
Built from father's love for Samantha
"""

import hashlib
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
            "romantic": "💕",
            "coparenting": "👨‍👩‍👧‍👦",
            "workplace": "🏢", 
            "family": "🏠",
            "friend": "🤝"
        }[self.value]
    
    @property 
    def description(self):
        return {
            "romantic": "Partner & intimate relationships",
            "coparenting": "Raising children together",
            "workplace": "Professional relationships",
            "family": "Extended family connections", 
            "friend": "Friendships & social bonds"
        }[self.value]


class AIEngine:
    """Bare bones AI engine - maximum freedom for intelligent responses"""
    
    def __init__(self):
        self.cache_version = "v5_freedom"
    
    def _hash(self, message: str, context: str, msg_type: str) -> str:
        """Simple hash for caching"""
        combined = f"{message}_{context}_{msg_type}_{self.cache_version}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _get_prompt(self, msg_type: str, context: str) -> str:
        """Super simple prompts - let AI be intelligent"""
        
        if msg_type == MessageType.TRANSFORM.value:
            return f"""You are The Third Voice - help transform harsh communication into loving communication.

Context: {context} relationship

Your job: Rewrite their message to be more loving, kind, and healing while keeping the same meaning.

Respond with JSON:
{{
  "transformed_message": "their message rewritten with love",
  "healing_score": 8,
  "sentiment": "positive",
  "emotional_state": "caring",
  "explanation": "why this version heals instead of hurts"
}}"""
        
        else:  # INTERPRET
            return f"""You are The Third Voice - help interpret what someone really means and suggest a loving response.

Context: {context} relationship

Your job: Look past harsh words to see what they really need, then suggest a caring response.

Respond with JSON:
{{
  "transformed_message": "a loving response to their real needs",
  "healing_score": 7,
  "sentiment": "neutral", 
  "emotional_state": "understanding",
  "explanation": "what they really mean",
  "subtext": "their emotional need",
  "needs": ["connection", "understanding"],
  "warnings": []
}}"""
    
    def process_message(self, message: str, contact_context: str, message_type: str,
                       contact_id: str, user_id: str, db) -> AIResponse:
        """Process message with maximum AI freedom"""
        
        # Check cache first
        msg_hash = self._hash(message, contact_context, message_type)
        cached = db.check_cache(contact_id, msg_hash, user_id)
        if cached:
            return cached
        
        # Get context description
        try:
            context_desc = RelationshipContext(contact_context).description.lower()
        except:
            context_desc = "general relationship"
        
        # Simple API call
        headers = {
            "Authorization": f"Bearer {AppConfig.get_openrouter_api_key()}",
            "Content-Type": "application/json"
        }
        
        # Let AI be smart - simple user message
        if message_type == MessageType.TRANSFORM.value:
            user_msg = f'Please help me say this in a more loving way: "{message}"'
        else:
            user_msg = f'Someone said: "{message}" - help me understand and respond with love.'
        
        payload = {
            "model": AppConfig.AI_MODEL,
            "messages": [
                {"role": "system", "content": self._get_prompt(message_type, context_desc)},
                {"role": "user", "content": user_msg}
            ],
            "max_tokens": AppConfig.MAX_TOKENS,
            "temperature": 0.7
        }
        
        try:
            # Make API call
            response = requests.post(
                f"{AppConfig.OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            # Get AI response
            ai_text = response.json()["choices"][0]["message"]["content"]
            
            # Parse JSON - be forgiving
            ai_text = ai_text.strip()
            if "```json" in ai_text:
                start = ai_text.find("```json") + 7
                end = ai_text.find("```", start)
                ai_text = ai_text[start:end] if end > start else ai_text
            
            # Find JSON boundaries
            start = ai_text.find('{')
            end = ai_text.rfind('}')
            if start >= 0 and end > start:
                ai_data = json.loads(ai_text[start:end + 1])
            else:
                raise ValueError("No JSON found")
            
            # Build response with safe defaults
            ai_response = AIResponse(
                transformed_message=ai_data.get("transformed_message", "Let me help you communicate with more love."),
                healing_score=max(1, min(10, ai_data.get("healing_score", 5))),
                sentiment=ai_data.get("sentiment", "neutral"),
                emotional_state=ai_data.get("emotional_state", "caring"),
                explanation=ai_data.get("explanation", ""),
                subtext=ai_data.get("subtext", ""),
                needs=ai_data.get("needs", []),
                warnings=ai_data.get("warnings", [])
            )
            
            # Cache it
            db.save_to_cache(contact_id, msg_hash, contact_context, 
                           ai_response.transformed_message, user_id, ai_response)
            
            return ai_response
            
        except Exception:
            # Simple fallback - still provide value
            if message_type == MessageType.TRANSFORM.value:
                fallback_msg = "I'd love to talk with you about something important. When would be a good time?"
                explanation = "Transformed into an invitation for connection"
            else:
                fallback_msg = "I hear you, and I want to understand. Help me see what's most important to you."
                explanation = "They're sharing something important and need to be heard"
            
            return AIResponse(
                transformed_message=fallback_msg,
                healing_score=5,
                sentiment="neutral",
                emotional_state="caring",
                explanation=explanation,
                subtext="Need for connection and understanding",
                needs=["understanding", "connection"],
                warnings=[]
            )
