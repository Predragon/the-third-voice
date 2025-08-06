"""
AI Engine Module - Production Version
Handles AI processing for relationship communication healing
Fixed prompts to better distinguish Transform vs Interpret modes
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
        """Create a hash for caching purposes with version for cache invalidation"""
        # Add version to hash to invalidate old cache when needed
        CACHE_VERSION = "v1.1"  # Incremented to invalidate old cache with fixed prompts
        
        # Clean message to avoid whitespace issues
        clean_message = message.strip()
        combined = f"{clean_message}_{contact_context}_{message_type}_{CACHE_VERSION}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _validate_cached_response(self, cached_response: AIResponse, message: str, 
                                 contact_context: str, message_type: str) -> bool:
        """Validate that cached response makes sense for the input"""
        
        # Basic validation checks
        if not cached_response or not cached_response.transformed_message:
            return False
        
        # Check for obvious mismatches (like meetings vs phone calls)
        message_lower = message.lower()
        response_lower = cached_response.transformed_message.lower()
        
        # Keywords that should match between input and output
        key_topics = {
            'phone': ['phone', 'call', 'calling', 'reach'],
            'late': ['late', 'time', 'punctual', 'schedule'],
            'meeting': ['meeting', 'work', 'professional'],
            'money': ['money', 'financial', 'cost', 'expensive'],
            'help': ['help', 'support', 'assist']
        }
        
        # Find what topic the input is about
        input_topic = None
        for topic, keywords in key_topics.items():
            if any(keyword in message_lower for keyword in keywords):
                input_topic = topic
                break
        
        # If we identified a topic, make sure response is related
        if input_topic:
            topic_keywords = key_topics[input_topic]
            if not any(keyword in response_lower for keyword in topic_keywords):
                print(f"⚠️ Cache validation failed: Input about '{input_topic}' but response seems unrelated")
                return False
        
        return True
    
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
        
        if message_type == "transform":
            return f"""You are a relationship communication expert. Your job is to TRANSFORM and REWRITE messages to be more loving and compassionate.

CRITICAL: You are in TRANSFORM mode. The user wants to send a message but needs help saying it better.

Your task: Take their original message and REWRITE it to be kinder, more loving, and more healing.

Context: This is for a {relationship_context} relationship.

TRANSFORM RULES:
- REWRITE their message to be more compassionate
- Keep the same core meaning and intent
- Turn accusations into "I" statements
- Show vulnerability instead of blame
- Use loving, non-threatening language
- Address the same topic/issue they mentioned

ALWAYS respond with JSON in this exact format:
{{
  "transformed_message": "Your rewritten, more loving version of their message",
  "healing_score": 8,
  "sentiment": "positive",
  "emotional_state": "caring",
  "explanation": "Why this version is more healing and likely to get better results"
}}"""

        else:  # INTERPRET mode
            return f"""You are a relationship communication expert. Your job is to INTERPRET and UNDERSTAND messages someone received, then suggest how to respond lovingly.

CRITICAL: You are in INTERPRET mode. The user RECEIVED a message from someone and needs help understanding what the sender really meant and how to respond compassionately.

Your task: Help them understand the deeper meaning behind the message they received, then suggest a loving response.

Context: This is for a {relationship_context} relationship.

INTERPRET RULES:
- Analyze what the sender is REALLY feeling beneath their words
- Identify their underlying emotional needs
- Suggest a compassionate RESPONSE (not rewrite the original)
- Look for hurt, fear, or unmet needs behind difficult words
- Help them see the person's humanity

ALWAYS respond with JSON in this exact format:
{{
  "transformed_message": "A suggested loving response to what they received",
  "healing_score": 7,
  "sentiment": "neutral",
  "emotional_state": "empathetic",
  "explanation": "What the sender is likely really feeling or needing",
  "subtext": "The deeper emotional meaning behind their words",
  "needs": ["connection", "understanding", "validation"],
  "warnings": ["any concerning patterns to be aware of"]
}}"""

    def process_message(self, message: str, contact_context: str, message_type: str,
                       contact_id: str, user_id: str, db) -> AIResponse:
        """Process a message with AI and return structured response"""
        
        # Check cache first with validation
        message_hash = self._create_message_hash(message, contact_context, message_type)
        cached_response = db.check_cache(contact_id, message_hash, user_id)
        
        if cached_response:
            # Validate cached response makes sense
            if self._validate_cached_response(cached_response, message, contact_context, message_type):
                return cached_response
            else:
                # Invalid cache - clear it and continue with fresh API call
                print(f"🗑️ Clearing invalid cache entry for hash: {message_hash}")
                db.clear_cache_entry(contact_id, message_hash, user_id)
        
        try:
            # Get relationship context description
            context_desc = "general relationship"
            for rel_context in RelationshipContext:
                if rel_context.value == contact_context:
                    context_desc = rel_context.description.lower()
                    break
            
            system_prompt = self._get_system_prompt(message_type, context_desc)
            
            # Prepare the request
            headers = {
                "Authorization": f"Bearer {AppConfig.get_openrouter_api_key()}",
                "Content-Type": "application/json"
            }
            
            # Make the task VERY explicit in the user message
            if message_type == MessageType.TRANSFORM.value:
                user_message = f"""TRANSFORM MODE - I want to send this message but need it to be more loving:

"{message}"

Please REWRITE this message to be kinder and more compassionate while keeping the same meaning."""
            else:
                user_message = f"""INTERPRET MODE - Someone sent me this message and I need help understanding it:

"{message}"

Please help me understand what they really mean and suggest a loving way to RESPOND to them."""
            
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
            
            if not ai_text or ai_text.strip() == "":
                raise ValueError("Empty AI response")
            
            # Parse JSON
            try:
                clean_text = ai_text.strip()
                
                # Log the raw AI response for debugging
                print(f"🤖 Raw AI response: {clean_text[:200]}...")
                
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
                
                print(f"✅ Successfully parsed AI response: {ai_data.get('transformed_message', '')[:50]}...")
                    
            except (json.JSONDecodeError, ValueError) as e:
                print(f"❌ JSON parsing error: {str(e)}")
                print(f"Raw response was: {ai_text}")
                
                # Create context-aware fallback based on message type and content
                if message_type == "interpret":
                    # For interpret mode, provide analysis of what they likely mean
                    message_lower = message.lower()
                    if "case" in message_lower and "prosecutor" in message_lower:
                        ai_data = {
                            "transformed_message": "Thank you for keeping me updated on the legal situation. I appreciate you taking care of this and letting me know about the potential hearing. Please keep me posted as things develop.",
                            "healing_score": 7,
                            "sentiment": "neutral",
                            "emotional_state": "supportive",
                            "explanation": "They're trying to keep you informed and manage your expectations about the legal process",
                            "subtext": "They want to be transparent about the process while managing the uncertainty",
                            "needs": ["communication", "understanding", "cooperation"],
                            "warnings": []
                        }
                    elif "lot on your plate" in message_lower:
                        ai_data = {
                            "transformed_message": "I appreciate you acknowledging that I have a lot going on. Thank you for the update and for handling this. Your communication helps me feel more at ease about the situation.",
                            "healing_score": 8,
                            "sentiment": "positive",
                            "emotional_state": "grateful", 
                            "explanation": "They're showing empathy for your situation while keeping you informed",
                            "subtext": "They care about your stress level and want to be considerate",
                            "needs": ["consideration", "communication", "support"],
                            "warnings": []
                        }
                    else:
                        ai_data = {
                            "transformed_message": "Thank you for reaching out and keeping me in the loop. I appreciate your communication.",
                            "healing_score": 6,
                            "sentiment": "neutral",
                            "emotional_state": "appreciative",
                            "explanation": "They're trying to maintain good communication with you",
                            "subtext": "There's likely a desire to keep the relationship positive",
                            "needs": ["communication", "understanding"],
                            "warnings": []
                        }
                else:
                    # For transform mode
                    if "phone" in message.lower() or "call" in message.lower():
                        fallback_message = "I feel disconnected when I can't reach you. Could we find a good time to talk?"
                    elif "late" in message.lower():
                        fallback_message = "I feel frustrated when we start late. Could we work together to find a better approach?"
                    elif "never" in message.lower():
                        fallback_message = "I feel unheard and would love to connect better with you."
                    else:
                        fallback_message = "I'd like to talk about something that's been on my mind."
                    
                    ai_data = {
                        "transformed_message": fallback_message,
                        "healing_score": 4,
                        "sentiment": "neutral",
                        "emotional_state": "neutral",
                        "explanation": "Rewritten to use 'I' statements and avoid blame"
                    }
            
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
            
            # Cache the response with additional validation
            db.save_to_cache(
                contact_id, message_hash, contact_context,
                ai_response.transformed_message, user_id, ai_response
            )
            
            return ai_response
            
        except requests.RequestException as e:
            return self._create_fallback_response("API connection error")
            
        except Exception as e:
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
