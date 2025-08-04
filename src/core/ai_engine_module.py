"""
AI Engine Module - The Heart of The Third Voice
Handles AI processing for relationship communication healing
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
    
    def _get_system_prompt(self, message_type: str, relationship_context: str) -> str:
        """Get system prompt based on message type and context"""
        
        if message_type == MessageType.TRANSFORM.value:
            return f"""You are a relationship communication helper. The user has a {relationship_context} relationship and wants to say something in a kinder way.

Transform their message to be more loving and constructive while keeping the same meaning.

Respond in this exact JSON format:
{{
  "transformed_message": "rewritten message here",
  "healing_score": 7,
  "sentiment": "neutral",
  "emotional_state": "concerned", 
  "explanation": "what was changed"
}}"""

        else:  # INTERPRET mode
            return f"""You are a relationship communication helper. The user received a difficult message in a {relationship_context} relationship and needs help understanding it.

Help them understand what the person really means and suggest a loving response.

Respond in this exact JSON format:
{{
  "transformed_message": "suggested response here",
  "healing_score": 6,
  "sentiment": "neutral",
  "emotional_state": "hurt",
  "explanation": "what they really mean",
  "subtext": "underlying feelings",
  "needs": ["need1", "need2"],
  "warnings": ["warning if any"]
}}"""

    def process_message(self, message: str, contact_context: str, message_type: str,
                       contact_id: str, user_id: str, db) -> AIResponse:
        """Process a message with AI and return structured response"""
        
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
            
            # Prepare the request
            headers = {
                "Authorization": f"Bearer {AppConfig.get_openrouter_api_key()}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": AppConfig.AI_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                "max_tokens": AppConfig.MAX_TOKENS,
                "temperature": AppConfig.TEMPERATURE
            }
            
            # Make API call with better error handling
            response = requests.post(
                f"{AppConfig.OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            # Debug: Log the response status
            st.write(f"Debug: API Response Status: {response.status_code}")
            
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            
            # Debug: Check if choices exist
            if "choices" not in response_data or not response_data["choices"]:
                st.error(f"Debug: No choices in API response: {response_data}")
                raise ValueError("No choices in API response")
            
            ai_text = response_data["choices"][0]["message"]["content"]
            
            # Debug: Show raw AI response
            st.write(f"Debug: Raw AI Response: '{ai_text}'")
            
            # Handle empty response
            if not ai_text or ai_text.strip() == "":
                st.error("AI returned empty response")
                raise ValueError("Empty AI response")
            
            # Try to parse as JSON with improved error handling
            try:
                # Clean the response - remove any markdown formatting
                clean_text = ai_text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text.replace("```json", "").replace("```", "").strip()
                elif clean_text.startswith("```"):
                    clean_text = clean_text.replace("```", "").strip()
                
                # Debug: Show cleaned text
                st.write(f"Debug: Cleaned text: '{clean_text}'")
                
                ai_data = json.loads(clean_text)
                
                # Validate required fields
                if "transformed_message" not in ai_data:
                    raise ValueError("Missing transformed_message in AI response")
                    
            except (json.JSONDecodeError, ValueError) as e:
                st.error(f"JSON parsing error: {str(e)}")
                st.write(f"Debug: Failed to parse: '{clean_text}'")
                
                # Try to extract a reasonable response from non-JSON text
                if ai_text and len(ai_text.strip()) > 0:
                    ai_data = {
                        "transformed_message": ai_text.strip(),
                        "healing_score": 5,
                        "sentiment": "neutral",
                        "emotional_state": "unclear",
                        "explanation": "AI provided text response instead of JSON"
                    }
                else:
                    # Complete fallback
                    ai_data = {
                        "transformed_message": "I'm having trouble processing this message right now. Please try again with different wording.",
                        "healing_score": 3,
                        "sentiment": "neutral",
                        "emotional_state": "unclear",
                        "explanation": "AI response parsing failed"
                    }
            
            # Create structured response
            ai_response = AIResponse(
                transformed_message=ai_data.get("transformed_message", "Error processing message"),
                healing_score=ai_data.get("healing_score", 5),
                sentiment=ai_data.get("sentiment", "neutral"),
                emotional_state=ai_data.get("emotional_state", "unclear"),
                explanation=ai_data.get("explanation", ""),
                subtext=ai_data.get("subtext", ""),
                needs=ai_data.get("needs", []),
                warnings=ai_data.get("warnings", [])
            )
            
            # Cache the response
            db.save_to_cache(
                contact_id, message_hash, contact_context,
                ai_response.transformed_message, user_id, ai_response
            )
            
            return ai_response
            
        except requests.RequestException as e:
            st.error(f"API request error: {str(e)}")
            return self._create_fallback_response("API connection error")
            
        except Exception as e:
            st.error(f"AI processing error: {str(e)}")
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
