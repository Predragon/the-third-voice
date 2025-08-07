"""
Simplified AI Engine Module
Processes messages for relationship communication using concise prompts
"""

import hashlib
import json
import requests
from typing import Optional
from enum import Enum
from ..config.settings import AppConfig
from ..data.models import AIResponse

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
    def description(self):
        desc_map = {
            "romantic": "partner & intimate relationships",
            "coparenting": "raising children together",
            "workplace": "professional relationships",
            "family": "extended family connections",
            "friend": "friendships & social bonds"
        }
        return desc_map[self.value]

class AIEngine:
    """Simplified AI processing engine using OpenRouter"""

    def __init__(self):
        pass

    def _normalize_sentiment(self, sentiment: str) -> str:
        """Normalize sentiment to match database constraints"""
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
            'frustrated': 'negative',
            'sad': 'negative',
            'defensive': 'negative',
            'confused': 'neutral'
        }
        return sentiment_map.get(sentiment.lower().strip(), 'unknown')

    def _normalize_emotional_state(self, emotional_state: str) -> str:
        """Normalize emotional state to common values"""
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
            'appreciative': 'appreciative',
            'professional': 'professional',
            'constructive': 'constructive',
            'vulnerable': 'vulnerable',
            'open': 'open',
            'appropriate': 'appropriate'
        }
        return state_map.get(emotional_state.lower().strip(), 'unknown')

    def process_message(self, message: str, contact_context: str, message_type: str,
                       contact_id: str, user_id: str, db) -> AIResponse:
        """Process a message with AI and return structured response"""
        
        # Validate inputs
        if message_type not in [m.value for m in MessageType]:
            return AIResponse(
                transformed_message="Invalid message type",
                healing_score=1,
                sentiment="negative",
                emotional_state="error",
                explanation="Invalid message type provided",
                subtext="",
                needs=[],
                warnings=["Invalid message type"]
            )

        # Check cache
        message_hash = hashlib.md5(f"{message}_{contact_context}_{message_type}_v1.0".encode()).hexdigest()
        cached_response = db.check_cache(contact_id, message_hash, user_id)
        if cached_response:
            return cached_response

        # Get relationship context description
        context_desc = "general relationship"
        for rel_context in RelationshipContext:
            if rel_context.value == contact_context:
                context_desc = rel_context.description.lower()
                break

        # Prepare prompt
        if message_type == MessageType.TRANSFORM.value:
            prompt = f"""I want to send this message in a {context_desc} relationship, but I need it to be more loving and constructive:

"{message}"

Rewrite the message to be kinder and more compassionate while preserving its core meaning. Respond with a JSON object containing:
- transformed_message: The rewritten message
- healing_score: A score from 1-10 indicating how constructive the response is
- sentiment: Must be 'positive', 'neutral', 'negative', or 'unknown'
- emotional_state: Must be one of 'caring', 'empathetic', 'supportive', 'neutral', 'professional', 'constructive', 'vulnerable', 'open'
- explanation: Why this response is more healing"""
        else:  # INTERPRET mode
            prompt = f"""Someone in a {context_desc} relationship sent me this message:

"{message}"

Analyze the message's content, tone, and intent. Suggest an appropriate response that addresses the sender's specific message. Respond with a JSON object containing:
- transformed_message: A suggested response that directly addresses the message
- healing_score: A score from 1-10 indicating how constructive the response is
- sentiment: Must be 'positive', 'neutral', 'negative', or 'unknown'
- emotional_state: Must be one of 'caring', 'empathetic', 'supportive', 'neutral', 'professional', 'constructive', 'vulnerable', 'open'
- explanation: What the sender is communicating and why this response fits
- subtext: The underlying meaning or needs in the sender's message
- needs: A list of the sender's likely needs (e.g., validation, acknowledgment)
- warnings: Any concerning patterns or empty list if none"""

        try:
            # Make API call
            headers = {
                "Authorization": f"Bearer {AppConfig.get_openrouter_api_key()}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": AppConfig.AI_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a relationship communication expert."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": AppConfig.MAX_TOKENS,
                "temperature": 0.3,
                "response_format": {"type": "json_object"} if "gpt" in AppConfig.AI_MODEL.lower() else None
            }
            payload = {k: v for k, v in payload.items() if v is not None}

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

            # Clean and parse JSON
            clean_text = ai_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text.replace("```json
            ai_data = json.loads(clean_text)

            # Create response object with normalized fields
            ai_response = AIResponse(
                transformed_message=ai_data.get("transformed_message", "Error processing message"),
                healing_score=min(max(int(ai_data.get("healing_score", 5)), 1), 10),
                sentiment=self._normalize_sentiment(ai_data.get("sentiment", "neutral")),
                emotional_state=self._normalize_emotional_state(ai_data.get("emotional_state", "neutral")),
                explanation=ai_data.get("explanation", ""),
                subtext=ai_data.get("subtext", ""),
                needs=ai_data.get("needs", []),
                warnings=ai_data.get("warnings", [])
            )

            # Save to cache
            db.save_to_cache(
                contact_id=contact_id,
                message_hash=message_hash,
                context=contact_context,
                response=ai_response.transformed_message,
                user_id=user_id,
                ai_response=ai_response,
                model=AppConfig.AI_MODEL
            )

            # Save to messages table
            if ai_response.transformed_message != "Error processing message":
                db.save_message(
                    contact_id=contact_id,
                    contact_name=db.get_contact_name(contact_id),
                    type=message_type,
                    original=message,
                    result=ai_response.transformed_message,
                    sentiment=ai_response.sentiment,
                    emotional_state=ai_response.emotional_state,
                    healing_score=ai_response.healing_score,
                    model=AppConfig.AI_MODEL,
                    user_id=user_id
                )

            # Save to interpretations table (INTERPRET mode only)
            if message_type == MessageType.INTERPRET.value and ai_response.transformed_message != "Error processing message":
                db.save_interpretation(
                    contact_id=contact_id,
                    contact_name=db.get_contact_name(contact_id),
                    original_message=message,
                    interpretation=ai_response.transformed_message,
                    interpretation_score=ai_response.healing_score,
                    model=AppConfig.AI_MODEL,
                    user_id=user_id
                )

            return ai_response

        except Exception as e:
            # Simple fallback
            ai_response = AIResponse(
                transformed_message="I couldn't process the message, but I'm here to help. Could you clarify or try again?",
                healing_score=3,
                sentiment="neutral",
                emotional_state="neutral",
                explanation=f"Error processing message: {str(e)}",
                subtext="",
                needs=["clarification"],
                warnings=["Processing error"]
            )

            # Save error to messages table
            db.save_message(
                contact_id=contact_id,
                contact_name=db.get_contact_name(contact_id),
                type=message_type,
                original=message,
                result=ai_response.transformed_message,
                sentiment=ai_response.sentiment,
                emotional_state=ai_response.emotional_state,
                healing_score=ai_response.healing_score,
                model=AppConfig.AI_MODEL,
                user_id=user_id
            )

            return ai_response
