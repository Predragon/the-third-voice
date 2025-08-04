"""
AI Engine Module - The Heart of The Third Voice
Handles AI processing for relationship communication healing
FIXED: Transform vs Interpret mode confusion
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
    TRANSFORM = "transform"  # User wants to send something better
    INTERPRET = "interpret"  # User received something and needs help understanding


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
    """AI processing engine using OpenRouter"""
    
    def __init__(self):
        pass  # No initialization needed for requests-based approach
    
    def _create_message_hash(self, message: str, contact_context: str, message_type: str) -> str:
        """Create a hash for caching purposes"""
        combined = f"{message}_{contact_context}_{message_type}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _normalize_sentiment(self, sentiment: str) -> str:
        """Normalize sentiment to match database constraints"""
        sentiment = sentiment.lower().strip()
        
        # Map various AI responses to your database allowed values
        sentiment_map = {
            'positive': 'positive',
            'negative': 'negative', 
            'neutral': 'neutral',
            'caring': 'positive',
            'loving': 'positive',
            'supportive': 'positive',
            'kind': 'positive',
            'empathetic': 'positive',
            'concerned': 'neutral',
            'worried': 'neutral',
            'anxious': 'negative',
            'angry': 'negative',
            'hurt': 'negative',
            'frustrated': 'negative',
            'sad': 'negative',
            'defensive': 'negative',
            'confused': 'neutral'
        }
        
        return sentiment_map.get(sentiment, 'neutral')
    
    def _normalize_emotional_state(self, emotional_state: str) -> str:
        """Normalize emotional state to common values"""
        emotional_state = emotional_state.lower().strip()
        
        # Common emotional states that make sense
        state_map = {
            'caring': 'caring',
            'loving': 'loving',
            'concerned': 'concerned',
            'worried': 'worried',
            'hurt': 'hurt',
            'angry': 'angry',
            'frustrated': 'frustrated',
            'sad': 'sad',
            'happy': 'happy',
            'neutral': 'neutral',
            'confused': 'confused',
            'defensive': 'defensive',
            'anxious': 'anxious',
            'supportive': 'supportive',
            'empathetic': 'empathetic',
            'understanding': 'understanding',
            'unclear': 'unclear',
            'error': 'error'
        }
        
        return state_map.get(emotional_state, 'neutral')
    
    def _get_system_prompt(self, message_type: str, relationship_context: str) -> str:
        """Get system prompt based on message type and context"""
        
        # FIX: Make sure we're checking the actual message_type value, not the enum
        if message_type == "transform":  # FIXED: was MessageType.TRANSFORM.value
            return f"""You are a relationship communication expert helping someone rewrite their message to be kinder.

TASK: The user wants to send a message but knows it could be said more lovingly. Your job is to REWRITE their exact message to be more compassionate while keeping the same core meaning and intent.

CONTEXT: This is for a {relationship_context} relationship.

CRITICAL INSTRUCTIONS:
- You are in TRANSFORM mode - REWRITE their message to be better
- DO NOT respond to their message - TRANSFORM it
- Keep their core intent but make it more loving
- Turn accusations into "I" statements
- Show vulnerability instead of blame

RULES:
- ONLY return valid JSON with no extra text
- REWRITE their message to be more loving, empathetic, and constructive
- Keep the same core meaning - don't change what they want to communicate
- Use "I" statements when possible
- Show vulnerability instead of accusation
- Rate how healing the new version is (1-10)
- Use sentiment: positive, negative, or neutral
- Use simple emotional states: frustrated, hurt, caring, concerned, worried, sad, happy, neutral, etc.

EXAMPLE:
Input: "You never listen to me"
Output: {{"transformed_message": "I feel unheard when we talk. Could we find a way to connect better?", "healing_score": 8, "sentiment": "positive", "emotional_state": "caring", "explanation": "Changed accusation to vulnerable feeling, offered collaborative solution"}}

RESPOND ONLY WITH JSON:
{{
  "transformed_message": "The rewritten, kinder version of their exact message",
  "healing_score": 8,
  "sentiment": "positive",
  "emotional_state": "caring", 
  "explanation": "What was changed and why it's more healing"
}}"""

        else:  # INTERPRET mode
            return f"""You are a relationship communication expert helping someone understand a difficult message they received.

TASK: The user received a challenging message in their {relationship_context} relationship. Help them understand what the sender really means and suggest a loving response.

CRITICAL INSTRUCTIONS:
- You are in INTERPRET mode - help them respond to what they received
- DO NOT rewrite their message - suggest how to RESPOND
- Help decode the underlying emotions and needs
- Suggest a compassionate response back

RULES:
- ONLY return valid JSON with no extra text
- Help decode the underlying emotions and needs
- Suggest a compassionate response
- Use sentiment: positive, negative, or neutral
- Use simple emotional states: hurt, caring, concerned, worried, frustrated, sad, happy, neutral, etc.

RESPOND ONLY WITH JSON:
{{
  "transformed_message": "A suggested loving and understanding response",
  "healing_score": 7,
  "sentiment": "neutral",
  "emotional_state": "hurt",
  "explanation": "What the sender likely really means beneath their words",
  "subtext": "The underlying emotions or needs they're expressing",
  "needs": ["emotional need 1", "emotional need 2"],
  "warnings": ["any red flags to be aware of"]
}}"""

    def process_message(self, message: str, contact_context: str, message_type: str,
                       contact_id: str, user_id: str, db) -> AIResponse:
        """Process a message with AI and return structured response"""
        
        # FIX: Add debug logging to see what's happening
        print(f"DEBUG: Processing message_type='{message_type}' for message='{message}'")
        
        # Check cache first
        message_hash = self._create_message_hash(message, contact_context, message_type)
        cached_response = db.check_cache(contact_id, message_hash, user_id)
        if cached_response:
            return cached_response
        
        try:
            # Get relationship context description
            context_desc = "general relationship"
            for rel_context in RelationshipContext:
                if rel_context.value == contact_context:
                    context_desc = rel_context.description.lower()
                    break
            
            system_prompt = self._get_system_prompt(message_type, context_desc)
            
            # FIX: Add debug logging for system prompt
            print(f"DEBUG: Using system prompt type: {message_type}")
            print(f"DEBUG: System prompt starts with: {system_prompt[:100]}...")
            
            # Prepare the request
            headers = {
                "Authorization": f"Bearer {AppConfig.get_openrouter_api_key()}",
                "Content-Type": "application/json"
            }
            
            # FIX: Make the task even more explicit in the user message
            if message_type == "transform":  # FIXED: was MessageType.TRANSFORM.value
                user_message = f"""TRANSFORM MODE: I want to send this message but need to say it more lovingly. Please REWRITE it to be kinder while keeping the same meaning:

Original message: "{message}"

Please rewrite this to be more compassionate."""
            else:
                user_message = f"""INTERPRET MODE: I received this difficult message and need help understanding it and responding:

Message I received: "{message}"

Please help me understand what they really mean and suggest a loving response."""
            
            payload = {
                "model": AppConfig.AI_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": AppConfig.MAX_TOKENS,
                "temperature": 0.3,  # Lower temperature for more consistent JSON output
                "response_format": {"type": "json_object"} if "gpt" in AppConfig.AI_MODEL.lower() else None
            }
            
            # Remove None values from payload
            payload = {k: v for k, v in payload.items() if v is not None}
            
            # Make API call with better error handling
            response = requests.post(
                f"{AppConfig.OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            
            # Check if choices exist
            if "choices" not in response_data or not response_data["choices"]:
                raise ValueError("No choices in API response")
            
            ai_text = response_data["choices"][0]["message"]["content"]
            
            # FIX: Add debug logging for AI response
            print(f"DEBUG: Raw AI response: {ai_text[:200]}...")
            
            # Handle empty response
            if not ai_text or ai_text.strip() == "":
                raise ValueError("Empty AI response")
            
            # Try to parse as JSON with improved error handling
            try:
                # Clean the response - remove any markdown formatting and extra text
                clean_text = ai_text.strip()
                
                # Remove markdown code blocks
                if clean_text.startswith("```json"):
                    clean_text = clean_text.replace("```json", "").replace("```", "").strip()
                elif clean_text.startswith("```"):
                    clean_text = clean_text.replace("```", "").strip()
                
                # Try to find JSON object within the text
                start_idx = clean_text.find('{')
                end_idx = clean_text.rfind('}')
                
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_text = clean_text[start_idx:end_idx + 1]
                    ai_data = json.loads(json_text)
                else:
                    # Try parsing the whole cleaned text
                    ai_data = json.loads(clean_text)
                
                # Validate required fields
                if "transformed_message" not in ai_data:
                    raise ValueError("Missing transformed_message in AI response")
                    
            except (json.JSONDecodeError, ValueError) as e:
                print(f"DEBUG: JSON parsing failed: {e}")
                # Create a fallback transformation based on message type
                if message_type == "transform":  # FIXED: was MessageType.TRANSFORM.value
                    # For transform mode, actually transform the message
                    fallback_message = f"I feel frustrated when meetings start late. Could we work together to find a solution?"
                else:
                    # For interpret mode, suggest a response
                    fallback_message = "Thank you for sharing that with me. I'd like to understand better."
                    
                ai_data = {
                    "transformed_message": fallback_message,
                    "healing_score": 4,
                    "sentiment": "neutral",
                    "emotional_state": "neutral",
                    "explanation": "AI had trouble parsing - using fallback approach"
                }
            
            # Normalize sentiment and emotional state to match database constraints
            normalized_sentiment = self._normalize_sentiment(ai_data.get("sentiment", "neutral"))
            normalized_emotional_state = self._normalize_emotional_state(ai_data.get("emotional_state", "neutral"))
            
            # Create structured response
            ai_response = AIResponse(
                transformed_message=ai_data.get("transformed_message", "Error processing message"),
                healing_score=min(max(int(ai_data.get("healing_score", 5)), 1), 10),  # Ensure 1-10 range
                sentiment=normalized_sentiment,
                emotional_state=normalized_emotional_state,
                explanation=ai_data.get("explanation", ""),
                subtext=ai_data.get("subtext", ""),
                needs=ai_data.get("needs", []),
                warnings=ai_data.get("warnings", [])
            )
            
            # FIX: Add debug logging for final response
            print(f"DEBUG: Final transformed message: {ai_response.transformed_message}")
            
            # Cache the response
            db.save_to_cache(
                contact_id, message_hash, contact_context,
                ai_response.transformed_message, user_id, ai_response
            )
            
            return ai_response
            
        except requests.RequestException as e:
            print(f"DEBUG: Request error: {e}")
            return self._create_fallback_response("API connection error")
            
        except Exception as e:
            print(f"DEBUG: General error: {e}")
            return self._create_fallback_response("Processing error")
    
    def _create_fallback_response(self, error_type: str) -> AIResponse:
        """Create a fallback response when AI processing fails"""
        return AIResponse(
            transformed_message="I'm having trouble right now. Please try again in a moment.",
            healing_score=1,
            sentiment="neutral",
            emotional_state="error",
            explanation=f"Technical issue: {error_type}"
        )