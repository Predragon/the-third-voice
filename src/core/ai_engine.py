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
            return f"""You are a relationship communication expert. Your ONLY job is to transform messages to be kinder and more constructive while preserving the original meaning.

The user has a {relationship_context} relationship and wants to improve their message.

CRITICAL INSTRUCTIONS:
- You MUST respond ONLY with valid JSON
- Do NOT include any text before or after the JSON
- Do NOT use markdown formatting
- Transform the message to be more loving, empathetic, and constructive
- Rate healing potential 1-10 (higher = more healing)
- Analyze the emotional tone

RESPOND WITH ONLY THIS JSON FORMAT:
{{
  "transformed_message": "The improved, kinder version of their message",
  "healing_score": 8,
  "sentiment": "concerned",
  "emotional_state": "worried", 
  "explanation": "Brief explanation of what was improved and why"
}}"""

        else:  # INTERPRET mode
            return f"""You are a relationship communication expert. Your ONLY job is to help interpret difficult messages and suggest loving responses.

The user received a challenging message in a {relationship_context} relationship.

CRITICAL INSTRUCTIONS:
- You MUST respond ONLY with valid JSON
- Do NOT include any text before or after the JSON
- Do NOT use markdown formatting
- Help them understand the deeper meaning and suggest a compassionate response

RESPOND WITH ONLY THIS JSON FORMAT:
{{
  "transformed_message": "A suggested loving and understanding response",
  "healing_score": 7,
  "sentiment": "hurt",
  "emotional_state": "defensive",
  "explanation": "What the sender likely really means beneath their words",
  "subtext": "The underlying emotions or needs they're expressing",
  "needs": ["emotional need 1", "emotional need 2"],
  "warnings": ["any red flags to be aware of"]
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
                    {"role": "user", "content": f"Transform this message: '{message}'"}
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
                    # Debug: Show extracted JSON
                    st.write(f"Debug: Extracted JSON: '{json_text}'")
                    ai_data = json.loads(json_text)
                else:
                    # Try parsing the whole cleaned text
                    ai_data = json.loads(clean_text)
                
                # Validate required fields
                if "transformed_message" not in ai_data:
                    raise ValueError("Missing transformed_message in AI response")
                    
            except (json.JSONDecodeError, ValueError) as e:
                st.error(f"JSON parsing error: {str(e)}")
                st.write(f"Debug: Failed to parse: '{clean_text}'")
                
                # Create a structured fallback based on the raw response
                fallback_message = clean_text[:200] + "..." if len(clean_text) > 200 else clean_text
                ai_data = {
                    "transformed_message": f"I notice some concern in your message. Here's a gentler approach: '{fallback_message}'",
                    "healing_score": 4,
                    "sentiment": "neutral",
                    "emotional_state": "unclear",
                    "explanation": "AI provided unstructured response - please try rephrasing your message"
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
