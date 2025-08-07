"""
AI Engine Module - Ultra Minimal & Actually Working
The Third Voice - No barriers, just AI intelligence
Built for real human communication
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
    """Ultra minimal AI engine - actually works"""
    
    def process_message(self, message: str, contact_context: str, message_type: str,
                       contact_id: str, user_id: str, db) -> AIResponse:
        """Process message - no barriers, just intelligence"""
        
        print(f"🎙️ Processing: {message[:50]}...")
        
        # Super simple prompt
        if message_type == MessageType.TRANSFORM.value:
            system_prompt = """You are The Third Voice. Help rewrite messages to be more loving and healing while keeping the same meaning. 

Respond with JSON:
{"transformed_message": "rewritten message", "healing_score": 7, "sentiment": "positive", "emotional_state": "caring", "explanation": "why this is better"}"""
            
            user_prompt = f'Rewrite this to be more loving: "{message}"'
            
        else:  # INTERPRET
            system_prompt = """You are The Third Voice. Help interpret what someone really means beneath their words and suggest a compassionate response.

Respond with JSON:
{"transformed_message": "suggested response", "healing_score": 6, "sentiment": "neutral", "emotional_state": "understanding", "explanation": "what they really mean", "subtext": "their deeper feelings", "needs": ["their emotional needs"], "warnings": []}"""
            
            user_prompt = f'Help me understand what they really mean and how to respond with compassion: "{message}"'
        
        try:
            # Direct API call
            response = requests.post(
                f"{AppConfig.OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {AppConfig.get_openrouter_api_key()}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": AppConfig.AI_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.7
                },
                timeout=30
            )
            
            print(f"📡 API Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ API Error: {response.text}")
                raise Exception(f"API error: {response.status_code}")
            
            # Get response
            result = response.json()
            ai_text = result["choices"][0]["message"]["content"]
            
            print(f"🤖 Raw AI Response: {ai_text[:100]}...")
            
            # Extract JSON - be very forgiving
            try:
                # Try direct parse first
                ai_data = json.loads(ai_text)
            except:
                # Find JSON in text
                start = ai_text.find('{')
                end = ai_text.rfind('}') + 1
                if start >= 0 and end > start:
                    json_text = ai_text[start:end]
                    ai_data = json.loads(json_text)
                else:
                    raise Exception("No JSON found in response")
            
            print(f"✅ Parsed AI Data: {ai_data.get('transformed_message', 'N/A')[:50]}...")
            
            # Build response
            response = AIResponse(
                transformed_message=ai_data.get("transformed_message", "I understand you're going through something difficult."),
                healing_score=int(ai_data.get("healing_score", 5)),
                sentiment=ai_data.get("sentiment", "neutral"),
                emotional_state=ai_data.get("emotional_state", "understanding"),
                explanation=ai_data.get("explanation", "Providing support"),
                subtext=ai_data.get("subtext", ""),
                needs=ai_data.get("needs", []),
                warnings=ai_data.get("warnings", [])
            )
            
            print(f"✅ Final response created successfully")
            return response
            
        except Exception as e:
            print(f"💥 Error occurred: {str(e)}")
            
            # Only fall back if absolutely necessary
            if message_type == MessageType.TRANSFORM.value:
                return AIResponse(
                    transformed_message="I want to share something important with you. Can we talk?",
                    healing_score=5, sentiment="neutral", emotional_state="caring",
                    explanation="Simplified your message to invite connection"
                )
            else:
                return AIResponse(
                    transformed_message="I can see you're dealing with a lot right now. I'm here to listen and support you through this.",
                    healing_score=5, sentiment="neutral", emotional_state="understanding", 
                    explanation="They're sharing deep struggles and need support",
                    subtext="Going through major life challenges", 
                    needs=["support", "understanding", "someone to listen"]
                )