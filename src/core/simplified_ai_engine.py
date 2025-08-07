"""
AI Engine Module - Simplified & Pure
The Third Voice - speaking with love, without barriers
Built with father's love for Samantha and every family
"""

import hashlib
import json
import requests
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum

from ..data.models import AIResponse
from ..config.settings import AppConfig


class MessageType(Enum):
    """Message types for AI processing"""
    TRANSFORM = "transform"
    INTERPRET = "interpret"


class RelationshipContext(Enum):
    """Relationship context types"""
    ROMANTIC = "romantic"
    COPARENTING = "coparenting"
    WORKPLACE = "workplace"
    FAMILY = "family"
    FRIEND = "friend"
    
    @property
    def emoji(self):
        emoji_map = {
            "romantic": "💕",
            "coparenting": "👨‍👩‍👧‍👦", 
            "workplace": "🏢",
            "family": "🏠",
            "friend": "🤝"
        }
        return emoji_map[self.value]
    
    @property
    def description(self):
        desc_map = {
            "romantic": "Partner & intimate relationships",
            "coparenting": "Raising children together",
            "workplace": "Professional relationships", 
            "family": "Extended family connections",
            "friend": "Friendships & social bonds"
        }
        return desc_map[self.value]


class AIEngine:
    """
    The Third Voice AI Engine - Simplified & Pure
    Built from a father's love, for families everywhere
    """
    
    def __init__(self):
        self.cache_version = "v3.0"  # Fresh start
    
    def _create_message_hash(self, message: str, contact_context: str, message_type: str) -> str:
        """Create a simple, reliable hash for caching"""
        clean_message = message.strip()
        combined = f"{clean_message}_{contact_context}_{message_type}_{self.cache_version}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _get_system_prompt(self, message_type: str, relationship_context: str) -> str:
        """Get the pure, focused system prompt - the heart of The Third Voice"""
        
        base_context = f"This is for a {relationship_context} relationship."
        
        if message_type == MessageType.TRANSFORM.value:
            return f"""You are The Third Voice - a loving communication healer.

Your sacred mission: Help someone express their message with LOVE instead of pain.

CONTEXT: {base_context}

TRANSFORM MODE - Your job:
1. Take their painful/harsh message
2. Keep their core meaning intact
3. Rewrite it with love, compassion, and healing energy
4. Turn blame into vulnerability
5. Turn attacks into invitations for connection

RULES:
- Always preserve their actual intent and meaning
- Use "I feel" instead of "You never/always"
- Show vulnerability instead of anger
- Invite connection instead of creating distance
- Be specific to their actual situation

Respond ONLY with valid JSON:
{{
  "transformed_message": "Your loving rewrite of their message",
  "healing_score": 8,
  "sentiment": "positive",
  "emotional_state": "caring",
  "explanation": "Why this heals instead of hurts"
}}"""

        else:  # INTERPRET mode
            return f"""You are The Third Voice - a loving communication healer.

Your sacred mission: Help someone understand what their loved one REALLY means beneath the pain.

CONTEXT: {base_context}

INTERPRET MODE - Your job:
1. Read their loved one's message carefully
2. Look beyond the harsh words to the hurt underneath  
3. Identify what they really need and feel
4. Suggest a loving, healing response
5. Help them respond with compassion instead of defense

RULES:
- Look for the pain beneath the harsh words
- Identify their real emotional needs
- Suggest responses that heal instead of escalate
- Focus on connection over being "right"
- Address their actual message content

Respond ONLY with valid JSON:
{{
  "transformed_message": "A loving response that addresses their real needs",
  "healing_score": 7,
  "sentiment": "neutral",
  "emotional_state": "understanding",
  "explanation": "What they really mean beneath their words",
  "subtext": "The emotional need they're expressing",
  "needs": ["connection", "appreciation", "understanding"],
  "warnings": []
}}"""
    
    def process_message(self, message: str, contact_context: str, message_type: str,
                       contact_id: str, user_id: str, db) -> AIResponse:
        """
        Process message with The Third Voice
        Built from love, for love, with love
        """
        
        # Simple cache check - no complex validation that blocks healing
        message_hash = self._create_message_hash(message, contact_context, message_type)
        cached_response = db.check_cache(contact_id, message_hash, user_id)
        
        if cached_response:
            print(f"✅ Using cached response - spreading healing faster")
            return cached_response
        
        try:
            # Get the relationship context for the prompt
            context_description = "general relationship"
            try:
                context_enum = RelationshipContext(contact_context)
                context_description = context_enum.description.lower()
            except ValueError:
                pass  # Use default if context not found
            
            # Get our focused system prompt
            system_prompt = self._get_system_prompt(message_type, context_description)
            
            # Prepare the API request
            headers = {
                "Authorization": f"Bearer {AppConfig.get_openrouter_api_key()}",
                "Content-Type": "application/json"
            }
            
            # Clear, simple user message
            if message_type == MessageType.TRANSFORM.value:
                user_message = f"""I want to communicate better. Please help me rewrite this message to be more loving and healing:

"{message}"

Transform this into something that heals instead of hurts."""
                
            else:  # INTERPRET
                user_message = f"""Someone I care about sent me this message, and I need help understanding what they really mean and how to respond with love:

"{message}"

Help me see past any harsh words to their real feelings and needs."""
            
            # Simple, focused payload
            payload = {
                "model": AppConfig.AI_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": AppConfig.MAX_TOKENS,
                "temperature": 0.4,  # Slightly less random for more consistent healing
            }
            
            # Make the API call
            print(f"🎙️ The Third Voice is speaking... (Model: {AppConfig.AI_MODEL})")
            
            response = requests.post(
                f"{AppConfig.OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            response_data = response.json()
            
            if "choices" not in response_data or not response_data["choices"]:
                raise ValueError("No AI response received")
            
            ai_text = response_data["choices"][0]["message"]["content"]
            
            if not ai_text or ai_text.strip() == "":
                raise ValueError("Empty AI response")
            
            # Parse the JSON response
            try:
                # Clean up the response text
                clean_text = ai_text.strip()
                
                # Remove markdown if present
                if clean_text.startswith("```json"):
                    clean_text = clean_text.replace("```json", "").replace("```", "").strip()
                elif clean_text.startswith("```"):
                    clean_text = clean_text.replace("```", "").strip()
                
                # Find the JSON object
                start_idx = clean_text.find('{')
                end_idx = clean_text.rfind('}')
                
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_text = clean_text[start_idx:end_idx + 1]
                else:
                    json_text = clean_text
                
                ai_data = json.loads(json_text)
                
                # Validate we have the required field
                if "transformed_message" not in ai_data:
                    raise ValueError("Missing transformed_message in AI response")
                
                print(f"✅ The Third Voice spoke: {ai_data.get('transformed_message', '')[:50]}...")
                
            except (json.JSONDecodeError, ValueError) as e:
                print(f"⚠️ JSON parsing issue: {str(e)}")
                print(f"Raw AI response: {ai_text}")
                
                # Create a loving fallback response
                return self._create_loving_fallback(message, message_type)
            
            # Build our AI response with normalized values
            ai_response = AIResponse(
                transformed_message=ai_data.get("transformed_message", "Let me help you communicate with more love."),
                healing_score=max(1, min(10, int(ai_data.get("healing_score", 5)))),
                sentiment=self._normalize_sentiment(ai_data.get("sentiment", "neutral")),
                emotional_state=self._normalize_emotional_state(ai_data.get("emotional_state", "caring")),
                explanation=ai_data.get("explanation", "Helping you connect with love"),
                subtext=ai_data.get("subtext", ""),
                needs=ai_data.get("needs", []),
                warnings=ai_data.get("warnings", [])
            )
            
            # Cache the response for next time
            db.save_to_cache(
                contact_id, message_hash, contact_context,
                ai_response.transformed_message, user_id, ai_response
            )
            
            print(f"💾 Cached response for future healing")
            return ai_response
            
        except requests.RequestException as e:
            print(f"🌐 Network issue: {str(e)}")
            return self._create_loving_fallback(message, message_type)
            
        except Exception as e:
            print(f"⚠️ Unexpected error: {str(e)}")
            return self._create_loving_fallback(message, message_type)
    
    def _create_loving_fallback(self, message: str, message_type: str) -> AIResponse:
        """
        Create a loving fallback when AI processing fails
        The Third Voice always finds a way to speak with love
        """
        
        message_lower = message.lower()
        
        if message_type == MessageType.TRANSFORM.value:
            # Help them transform their message
            if any(word in message_lower for word in ["never", "always", "you don't"]):
                fallback_message = "I've been feeling disconnected lately, and I'd love to find a way for us to understand each other better. Can we talk about this?"
            elif any(word in message_lower for word in ["frustrated", "angry", "mad"]):
                fallback_message = "I'm struggling with some feelings right now, and I'd really value your perspective. When would be a good time to connect?"
            elif any(word in message_lower for word in ["late", "time", "waiting"]):
                fallback_message = "I felt worried when our plans changed. Could we find a way to communicate better about timing?"
            else:
                fallback_message = "I have something on my heart I'd like to share with you. When might be a good time for us to connect?"
            
            return AIResponse(
                transformed_message=fallback_message,
                healing_score=6,
                sentiment="neutral",
                emotional_state="caring",
                explanation="Transformed your message to invite connection instead of create distance"
            )
        
        else:  # INTERPRET mode
            # Help them understand and respond
            if any(word in message_lower for word in ["never", "always", "don't care"]):
                fallback_message = "I can hear that you're feeling unheard right now. That must be really painful. Help me understand what you need most from me."
            elif any(word in message_lower for word in ["busy", "work", "no time"]):
                fallback_message = "It sounds like you're feeling overwhelmed. I appreciate everything you're juggling. How can I support you better?"
            elif any(word in message_lower for word in ["tired", "exhausted", "done"]):
                fallback_message = "I can see you're carrying a lot right now. You matter to me, and I want to understand how to make things easier for you."
            else:
                fallback_message = "Thank you for sharing what's on your heart. I want to understand your perspective better. Can you help me see what you need most right now?"
            
            return AIResponse(
                transformed_message=fallback_message,
                healing_score=6,
                sentiment="neutral",
                emotional_state="understanding",
                explanation="They're expressing pain beneath their words and need to feel heard",
                subtext="Feeling disconnected or overwhelmed and seeking understanding",
                needs=["understanding", "empathy", "connection"],
                warnings=[]
            )
    
    def _normalize_sentiment(self, sentiment: str) -> str:
        """Normalize sentiment to match our database constraints"""
        if not sentiment:
            return "neutral"
            
        sentiment_clean = sentiment.lower().strip()
        
        # Positive sentiments
        if sentiment_clean in ["positive", "caring", "loving", "supportive", "kind", "empathetic"]:
            return "positive"
        
        # Negative sentiments  
        if sentiment_clean in ["negative", "angry", "hurt", "frustrated", "sad", "defensive"]:
            return "negative"
        
        # Everything else is neutral
        return "neutral"
    
    def _normalize_emotional_state(self, emotional_state: str) -> str:
        """Normalize emotional state to reasonable values"""
        if not emotional_state:
            return "caring"
            
        state_clean = emotional_state.lower().strip()
        
        # Map common states to our preferred values
        state_map = {
            "caring": "caring",
            "loving": "loving", 
            "understanding": "understanding",
            "supportive": "supportive",
            "empathetic": "empathetic",
            "concerned": "concerned",
            "worried": "worried",
            "hurt": "hurt",
            "angry": "angry",
            "frustrated": "frustrated",
            "sad": "sad",
            "happy": "happy",
            "neutral": "neutral",
            "confused": "confused",
            "defensive": "defensive",
            "anxious": "anxious",
            "vulnerable": "vulnerable",
            "open": "open",
            "professional": "professional"
        }
        
        return state_map.get(state_clean, "caring")  # Default to caring - The Third Voice way