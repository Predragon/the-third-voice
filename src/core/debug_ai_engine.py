"""
AI Engine Module - Enhanced Debug Version
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
    """AI processing engine using OpenRouter"""
    
    def __init__(self):
        pass
    
    def _create_message_hash(self, message: str, contact_context: str, message_type: str) -> str:
        """Create a hash for caching purposes"""
        combined = f"{message}_{contact_context}_{message_type}"
        hash_value = hashlib.md5(combined.encode()).hexdigest()
        
        # DEBUG: Log what we're hashing
        st.write(f"🔍 DEBUG: Creating hash for:")
        st.write(f"   Message: '{message}'")
        st.write(f"   Context: '{contact_context}'") 
        st.write(f"   Type: '{message_type}'")
        st.write(f"   Combined: '{combined}'")
        st.write(f"   Hash: '{hash_value}'")
        
        return hash_value
    
    def _normalize_sentiment(self, sentiment: str) -> str:
        """Normalize sentiment to match database constraints"""
        sentiment = sentiment.lower().strip()
        
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
        
        st.write(f"🎯 DEBUG: Getting system prompt for type='{message_type}', context='{relationship_context}'")
        
        if message_type == "transform":
            prompt = f"""You are a relationship communication expert helping someone rewrite their message to be kinder.

TASK: The user wants to send a message but knows it could be said more lovingly. Your job is to REWRITE their exact message to be more compassionate while keeping the same core meaning and intent.

CONTEXT: This is for a {relationship_context} relationship.

CRITICAL INSTRUCTIONS:
- You are in TRANSFORM mode - REWRITE their message to be better
- DO NOT respond to their message - TRANSFORM it
- Keep their core intent but make it more loving
- Turn accusations into "I" statements
- Show vulnerability instead of blame

EXAMPLE:
Input: "You never pickup the phone when I call"
Output: {{"transformed_message": "I feel disconnected when I can't reach you. Could we find a good time to talk?", "healing_score": 8, "sentiment": "positive", "emotional_state": "caring", "explanation": "Changed accusation to vulnerable feeling, offered collaborative solution"}}

RESPOND ONLY WITH JSON:
{{
  "transformed_message": "The rewritten, kinder version of their exact message",
  "healing_score": 8,
  "sentiment": "positive",
  "emotional_state": "caring", 
  "explanation": "What was changed and why it's more healing"
}}"""
            
            st.write("✅ Using TRANSFORM system prompt")
            return prompt

        else:  # INTERPRET mode
            prompt = f"""You are a relationship communication expert helping someone understand a difficult message they received.

TASK: The user received a challenging message in their {relationship_context} relationship. Help them understand what the sender really means and suggest a loving response.

CRITICAL INSTRUCTIONS:
- You are in INTERPRET mode - help them respond to what they received
- DO NOT rewrite their message - suggest how to RESPOND
- Help decode the underlying emotions and needs
- Suggest a compassionate response back

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
            
            st.write("✅ Using INTERPRET system prompt")
            return prompt

    def process_message(self, message: str, contact_context: str, message_type: str,
                       contact_id: str, user_id: str, db) -> AIResponse:
        """Process a message with AI and return structured response"""
        
        # ENHANCED DEBUG INFO
        st.write("🚀 DEBUG: Starting process_message")
        st.write(f"   📝 Message: '{message}'")
        st.write(f"   🎭 Context: '{contact_context}'")
        st.write(f"   🎯 Type: '{message_type}'")
        st.write(f"   👤 Contact ID: '{contact_id}'")
        st.write(f"   🆔 User ID: '{user_id}'")
        
        # Check cache first
        message_hash = self._create_message_hash(message, contact_context, message_type)
        
        st.write("🔍 Checking cache...")
        cached_response = db.check_cache(contact_id, message_hash, user_id)
        
        if cached_response:
            st.write("💾 FOUND CACHED RESPONSE!")
            st.write(f"   Cached message: '{cached_response.transformed_message}'")
            st.write("❌ This might be wrong - consider clearing cache")
            return cached_response
        else:
            st.write("✅ No cache found - will make new API call")
        
        try:
            # Get relationship context description
            context_desc = "general relationship"
            for rel_context in RelationshipContext:
                if rel_context.value == contact_context:
                    context_desc = rel_context.description.lower()
                    break
            
            st.write(f"📋 Context description: '{context_desc}'")
            
            system_prompt = self._get_system_prompt(message_type, context_desc)
            
            # Prepare the request
            headers = {
                "Authorization": f"Bearer {AppConfig.get_openrouter_api_key()}",
                "Content-Type": "application/json"
            }
            
            # Make the task even more explicit in the user message
            if message_type == "transform":
                user_message = f"""TRANSFORM MODE: I want to send this message but need to say it more lovingly. Please REWRITE it to be kinder while keeping the same meaning:

Original message: "{message}"

Please rewrite this to be more compassionate."""
            else:
                user_message = f"""INTERPRET MODE: I received this difficult message and need help understanding it and responding:

Message I received: "{message}"

Please help me understand what they really mean and suggest a loving response."""
            
            st.write("📤 User message being sent:")
            st.code(user_message)
            
            payload = {
                "model": AppConfig.AI_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": AppConfig.MAX_TOKENS,
                "temperature": 0.3,
                "response_format": {"type": "json_object"} if "gpt" in AppConfig.AI_MODEL.lower() else None
            }
            
            # Remove None values from payload
            payload = {k: v for k, v in payload.items() if v is not None}
            
            st.write("🌐 Making API call...")
            
            # Make API call
            response = requests.post(
                f"{AppConfig.OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            
            if "choices" not in response_data or not response_data["choices"]:
                raise ValueError("No choices in API response")
            
            ai_text = response_data["choices"][0]["message"]["content"]
            
            st.write("📨 Raw AI response:")
            st.code(ai_text)
            
            if not ai_text or ai_text.strip() == "":
                raise ValueError("Empty AI response")
            
            # Parse JSON
            try:
                clean_text = ai_text.strip()
                
                if clean_text.startswith("```json"):
                    clean_text = clean_text.replace("```json", "").replace("```", "").strip()
                elif clean_text.startswith("```"):
                    clean_text = clean_text.replace("```", "").strip()
                
                start_idx = clean_text.find('{')
                end_idx = clean_text.rfind('}')
                
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_text = clean_text[start_idx:end_idx + 1]
                    ai_data = json.loads(json_text)
                else:
                    ai_data = json.loads(clean_text)
                
                if "transformed_message" not in ai_data:
                    raise ValueError("Missing transformed_message in AI response")
                
                st.write("✅ Successfully parsed JSON response")
                st.write(f"   Transformed: '{ai_data.get('transformed_message', 'N/A')}'")
                    
            except (json.JSONDecodeError, ValueError) as e:
                st.write(f"❌ JSON parsing failed: {e}")
                
                # Create message-specific fallback
                if message_type == "transform":
                    if "phone" in message.lower():
                        fallback_message = "I feel disconnected when I can't reach you. Could we find a good time to talk?"
                    elif "late" in message.lower():
                        fallback_message = "I feel frustrated when we start late. Could we work together to find a better approach?"
                    else:
                        fallback_message = f"I'd like to talk about something that's been on my mind about us."
                else:
                    fallback_message = "Thank you for sharing that with me. I'd like to understand better."
                    
                ai_data = {
                    "transformed_message": fallback_message,
                    "healing_score": 4,
                    "sentiment": "neutral",
                    "emotional_state": "neutral",
                    "explanation": "AI had trouble parsing - using fallback approach"
                }
                
                st.write(f"🔄 Using fallback: '{fallback_message}'")
            
            # Normalize and create response
            normalized_sentiment = self._normalize_sentiment(ai_data.get("sentiment", "neutral"))
            normalized_emotional_state = self._normalize_emotional_state(ai_data.get("emotional_state", "neutral"))
            
            ai_response = AIResponse(
                transformed_message=ai_data.get("transformed_message", "Error processing message"),
                healing_score=min(max(int(ai_data.get("healing_score", 5)), 1), 10),
                sentiment=normalized_sentiment,
                emotional_state=normalized_emotional_state,
                explanation=ai_data.get("explanation", ""),
                subtext=ai_data.get("subtext", ""),
                needs=ai_data.get("needs", []),
                warnings=ai_data.get("warnings", [])
            )
            
            st.write("💾 Saving to cache...")
            
            # Cache the response
            db.save_to_cache(
                contact_id, message_hash, contact_context,
                ai_response.transformed_message, user_id, ai_response
            )
            
            st.write("✅ Processing complete!")
            return ai_response
            
        except requests.RequestException as e:
            st.write(f"❌ API Request error: {e}")
            return self._create_fallback_response("API connection error")
            
        except Exception as e:
            st.write(f"❌ General error: {e}")
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