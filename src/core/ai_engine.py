"""
AI Engine Module - Maximum Freedom Version
Let The Third Voice AI speak naturally and intelligently
Built from a father's love, with complete AI freedom
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
    The Third Voice AI Engine - Maximum Freedom
    Let AI be intelligent and natural
    """
    
    def __init__(self):
        self.cache_version = "v4.0"  # Freedom edition
    
    def _create_message_hash(self, message: str, contact_context: str, message_type: str) -> str:
        """Create a simple hash for caching"""
        clean_message = message.strip()
        combined = f"{clean_message}_{contact_context}_{message_type}_{self.cache_version}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _get_system_prompt(self, message_type: str, relationship_context: str) -> str:
        """Simple, natural prompts that give AI maximum freedom"""
        
        if message_type == MessageType.TRANSFORM.value:
            return f"""You are The Third Voice - a wise communication helper.

Your job: Help someone say their message in a kinder, more loving way.

This is for a {relationship_context} relationship.

TRANSFORM their message:
- Keep their exact meaning and intent
- Make it more caring and less harsh
- Use "I feel" instead of "You always/never"  
- Show vulnerability instead of attack
- Invite connection instead of blame

Be intelligent. Read their actual message carefully and respond appropriately to what they actually said.

Always respond with this JSON format:
{{
  "transformed_message": "Your improved version of their message",
  "healing_score": 8,
  "sentiment": "positive", 
  "emotional_state": "caring",
  "explanation": "Why this version works better"
}}"""

        else:  # INTERPRET mode
            return f"""You are The Third Voice - a wise communication helper.

Your job: Help someone understand what another person really means in their message, and suggest how to respond.

This is for a {relationship_context} relationship.

INTERPRET their message:
- Read their actual message carefully 
- Look for the real meaning behind any harsh words
- Identify what the sender really needs or feels
- Suggest an appropriate, caring response
- Be intelligent about the actual content they shared

Always respond with this JSON format:
{{
  "transformed_message": "A good response to their actual message",
  "healing_score": 7,
  "sentiment": "neutral",
  "emotional_state": "understanding", 
  "explanation": "What this message is really about",
  "subtext": "What they're really trying to communicate",
  "needs": ["what they need emotionally"],
  "warnings": []
}}"""
    
    def process_message(self, message: str, contact_context: str, message_type: str,
                       contact_id: str, user_id: str, db) -> AIResponse:
        """
        Process message with maximum AI freedom and intelligence
        """
        
        # Simple cache check
        message_hash = self._create_message_hash(message, contact_context, message_type)
        cached_response = db.check_cache(contact_id, message_hash, user_id)
        
        if cached_response:
            return cached_response
        
        try:
            # Get relationship context
            context_description = "general relationship"
            try:
                context_enum = RelationshipContext(contact_context)
                context_description = context_enum.description.lower()
            except ValueError:
                pass
            
            # Get simple system prompt
            system_prompt = self._get_system_prompt(message_type, context_description)
            
            # Prepare API request
            headers = {
                "Authorization": f"Bearer {AppConfig.get_openrouter_api_key()}",
                "Content-Type": "application/json"
            }
            
            # SIMPLE user message - let AI be intelligent
            if message_type == MessageType.TRANSFORM.value:
                user_message = f'Help me say this in a kinder way: "{message}"'
            else:  # INTERPRET
                user_message = f'Someone said this to me: "{message}" - Help me understand what they mean and how to respond.'
            
            # API call with maximum freedom
            payload = {
                "model": AppConfig.AI_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": AppConfig.MAX_TOKENS,
                "temperature": 0.7,  # More creativity and natural responses
            }
            
            response = requests.post(
                f"{AppConfig.OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            response_data = response.json()
            
            if "choices" not in response_data or not response_data["choices"]:
                return self._create_simple_fallback(message, message_type)
            
            ai_text = response_data["choices"][0]["message"]["content"]
            
            if not ai_text or ai_text.strip() == "":
                return self._create_simple_fallback(message, message_type)
            
            # Parse JSON - be very forgiving
            try:
                clean_text = ai_text.strip()
                
                # Remove markdown if present
                if "```json" in clean_text:
                    start = clean_text.find("```json") + 7
                    end = clean_text.find("```", start)
                    if end > start:
                        clean_text = clean_text[start:end]
                
                # Find JSON object
                start_idx = clean_text.find('{')
                end_idx = clean_text.rfind('}')
                
                if start_idx != -1 and end_idx != -1:
                    json_text = clean_text[start_idx:end_idx + 1]
                    ai_data = json.loads(json_text)
                else:
                    return self._create_simple_fallback(message, message_type)
                
            except (json.JSONDecodeError, ValueError):
                return self._create_simple_fallback(message, message_type)
            
            # Build response with safe defaults
            ai_response = AIResponse(
                transformed_message=ai_data.get("transformed_message", "Let me help you communicate with more love."),
                healing_score=max(1, min(10, int(ai_data.get("healing_score", 5)))),
                sentiment=self._safe_get(ai_data, "sentiment", "neutral"),
                emotional_state=self._safe_get(ai_data, "emotional_state", "caring"),
                explanation=ai_data.get("explanation", ""),
                subtext=ai_data.get("subtext", ""),
                needs=ai_data.get("needs", []),
                warnings=ai_data.get("warnings", [])
            )
            
            # Cache it
            db.save_to_cache(
                contact_id, message_hash, contact_context,
                ai_response.transformed_message, user_id, ai_response
            )
            
            return ai_response
            
        except Exception as e:
            return self._create_simple_fallback(message, message_type)
    
    def _create_simple_fallback(self, message: str, message_type: str) -> AIResponse:
        """Ultra-simple fallback that still provides value"""
        
        if message_type == MessageType.TRANSFORM.value:
            return AIResponse(
                transformed_message="I'd like to talk about something that's important to me. When would be a good time for us to connect?",
                healing_score=5,
                sentiment="neutral",
                emotional_state="caring",
                explanation="Transformed your message into an invitation for connection"
            )
        else:  # INTERPRET
            return AIResponse(
                transformed_message="I appreciate you sharing that with me. Help me understand what's most important to you about this.",
                healing_score=5,
                sentiment="neutral", 
                emotional_state="understanding",
                explanation="They're sharing something important with you",
                subtext="Looking for understanding and connection",
                needs=["to be heard", "understanding"],
                warnings=[]
            )
    
    def _safe_get(self, data: dict, key: str, default: str) -> str:
        """Safely get values with reasonable defaults"""
        value = data.get(key, default)
        if not value or not isinstance(value, str):
            return default
        
        # Basic validation for sentiment
        if key == "sentiment":
            if value.lower() in ["positive", "negative", "neutral"]:
                return value.lower()
            return "neutral"
        
        # Clean up emotional state
        if key == "emotional_state":
            clean_value = value.lower().strip()
            if len(clean_value) > 20:  # Too long
                return "caring"
            return clean_value
        
        return value
