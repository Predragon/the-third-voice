```python
import hashlib
import json
import logging
import re
from datetime import datetime
from enum import Enum
from typing import Optional

import requests
from src.config.settings import AppConfig
from src.data.models import AIResponse

# Configure logging for debugging on Streamlit Cloud and Redmi 14C
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageType(Enum):
    TRANSFORM = "transform"
    INTERPRET = "interpret"

class RelationshipContext(Enum):
    ROMANTIC = ("romantic", "romantic partner", "💕")
    COPARENTING = ("coparenting", "raising children together", "👨‍👩‍👧")
    WORKPLACE = ("workplace", "professional relationship", "💼")
    FAMILY = ("family", "family member", "👪")
    FRIEND = ("friend", "friendship", "🤝")

    def __init__(self, value, description, emoji):
        self._value_ = value
        self.description = description
        self.emoji = emoji

class AIEngine:
    """AI Engine for processing messages with emotional intelligence"""
    CACHE_VERSION = "v1.0"

    def __init__(self):
        self.base_url = AppConfig.OPENROUTER_BASE_URL
        self.api_key = AppConfig.get_openrouter_api_key()
        self.available_models = self._get_available_models()
        self.current_model_index = 0

    def _get_available_models(self):
        """Retrieve available models from secrets or fallback to default"""
        models = [AppConfig.AI_MODEL]
        try:
            import toml
            secrets_path = ".streamlit/secrets.toml"
            secrets = toml.load(secrets_path) if hasattr(toml, 'load') else {}
            models.extend([secrets.get("MODELS", {}).get(f"model{i}", "") for i in range(2, 7)])
            models = [m for m in models if m]  # Remove empty strings
        except Exception as e:
            logger.warning(f"Failed to load models from secrets: {str(e)}")
        return models or [AppConfig.AI_MODEL]

    def _create_message_hash(self, message: str, contact_context: str, message_type: str) -> str:
        """Create a unique hash for the message, context, and type"""
        message = re.sub(r'[^\w\s.,!?]', '', message.strip())  # Sanitize input
        combined = f"{message}_{contact_context}_{message_type}_{self.CACHE_VERSION}"
        return hashlib.md5(combined.encode()).hexdigest()

    def _get_system_prompt(self, message_type: str, context_desc: str) -> str:
        """Generate system prompt based on message type and context"""
        base_prompt = (
            f"You are a relationship communication expert helping someone communicate with their {context_desc}. "
        )
        if message_type == MessageType.TRANSFORM.value:
            return (
                base_prompt +
                "TASK: Rewrite the user's message to be more loving, compassionate, and likely to be well-received, "
                "while preserving the original intent. "
                "CRITICAL INSTRUCTIONS:\n"
                "- You are in TRANSFORM mode - rewrite the user's message\n"
                "- Use 'I' statements to express feelings\n"
                "- Avoid blame or accusations\n"
                "- Suggest collaboration or vulnerability\n"
                "RESPOND ONLY WITH JSON:\n"
                "{\n"
                '  "transformed_message": "The rewritten message",\n'
                '  "healing_score": 7,\n'
                '  "sentiment": "neutral",\n'
                '  "emotional_state": "calm",\n'
                '  "explanation": "Why this message is more likely to be well-received"\n'
                "}"
            )
        else:  # INTERPRET
            return (
                base_prompt +
                "TASK: The user received a challenging message in their "
                f"{context_desc} relationship. Help them understand what the sender really means "
                "and suggest a loving response.\n"
                "CRITICAL INSTRUCTIONS:\n"
                "- You are in INTERPRET mode - help them respond to what they received\n"
                "- DO NOT rewrite their message - suggest how to RESPOND\n"
                "- Help decode the underlying emotions and needs\n"
                "- Suggest a compassionate response back\n"
                "RESPOND ONLY WITH JSON:\n"
                "{\n"
                '  "transformed_message": "A suggested loving and understanding response",\n'
                '  "healing_score": 7,\n'
                '  "sentiment": "neutral",\n'
                '  "emotional_state": "hurt",\n'
                '  "explanation": "What the sender likely really means beneath their words",\n'
                '  "subtext": "The underlying emotions or needs they\'re expressing",\n'
                '  "needs": ["emotional need 1", "emotional need 2"],\n'
                '  "warnings": ["any red flags to be aware of"]\n'
                "}"
            )

    def _normalize_sentiment(self, sentiment: str) -> str:
        """Normalize sentiment to allowed values"""
        sentiment = sentiment.lower() if sentiment else "unknown"
        allowed = ["positive", "negative", "neutral", "unknown"]
        return sentiment if sentiment in allowed else "unknown"

    def _normalize_emotional_state(self, emotional_state: str) -> str:
        """Normalize emotional state"""
        emotional_state = emotional_state.lower() if emotional_state else "unclear"
        allowed = ["happy", "sad", "angry", "frustrated", "empathetic", "calm", "hurt", "unclear"]
        return emotional_state if emotional_state in allowed else "unclear"

    def _validate_cached_response(self, cached_response: AIResponse, message: str,
                                 contact_context: str, message_type: str) -> bool:
        """Validate if cached response is still relevant"""
        if not cached_response or not cached_response.transformed_message:
            return False
        message_lower = message.lower()
        response_lower = cached_response.transformed_message.lower()
        if message_type == MessageType.TRANSFORM.value:
            key_words = message_lower.split()
            return any(word in response_lower for word in key_words if len(word) > 3)
        else:  # INTERPRET
            emotional_triggers = ["never", "always", "late", "sorry", "time", "father", "mother"]
            if any(trigger in message_lower for trigger in emotional_triggers):
                return any(trigger in response_lower for trigger in ["sorry", "understand", "discuss"])
            if cached_response.sentiment == "negative" and "sorry" not in response_lower:
                logger.warning("Cache validation failed: Negative sentiment lacks apology")
                return False
        return True

    def _make_robust_ai_request(self, payload: dict, retries: int = 3) -> Optional[dict]:
        """Make API request with model fallback and retry logic"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        for attempt in range(retries):
            model = self.available_models[self.current_model_index % len(self.available_models)]
            payload["model"] = model
            logger.info(f"Attempting API request with model: {model}, attempt {attempt + 1}")
            try:
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=10
                )
                response.raise_for_status()
                logger.info(f"API response: {response.text[:200]}...")  # Truncate for brevity
                self.current_model_index = 0  # Reset to primary model
                return response.json()
            except requests.RequestException as e:
                logger.error(f"API error with {model}: {str(e)}")
                if isinstance(e, requests.HTTPError) and e.response.status_code == 429:
                    logger.warning("Rate limit hit, switching model")
                self.current_model_index += 1
                if self.current_model_index >= len(self.available_models):
                    self.current_model_index = 0
        logger.error("All API attempts failed")
        return None

    def process_message(self, message: str, contact_context: str, message_type: str,
                       contact_id: str, user_id: str, db) -> AIResponse:
        """Process a message through AI or cache"""
        # Sanitize input
        message = re.sub(r'[^\w\s.,!?]', '', message.strip())
        if not message:
            logger.error("Empty message after sanitization")
            return AIResponse(
                transformed_message="I'm sorry, I couldn't process an empty message. Please share your thoughts.",
                healing_score=0,
                sentiment="neutral",
                emotional_state="unclear",
                explanation="No valid input provided."
            )

        # Validate inputs
        try:
            message_type = MessageType(message_type.lower()).value
            context_enum = RelationshipContext(contact_context.lower())
            context_desc = context_enum.description
        except ValueError:
            logger.error(f"Invalid message_type: {message_type} or contact_context: {contact_context}")
            return AIResponse(
                transformed_message="I'm sorry, I couldn't process this request. Please try again.",
                healing_score=0,
                sentiment="neutral",
                emotional_state="unclear",
                explanation="Invalid message type or context provided."
            )

        # Check cache
        message_hash = self._create_message_hash(message, contact_context, message_type)
        cached_response = db.check_cache(contact_id, message_hash, user_id)
        if cached_response and self._validate_cached_response(cached_response, message, contact_context, message_type):
            logger.info(f"Cache hit for message_hash: {message_hash}")
            return cached_response

        # Prepare API call
        system_prompt = self._get_system_prompt(message_type, context_desc)
        user_message = (
            f"{message_type.upper()} MODE: "
            f"I {'want to say something to my' if message_type == MessageType.TRANSFORM.value else 'received this message from my'} "
            f"{context_desc}: \n\n"
            f"Message: \"{message}\"\n\n"
            f"Please {'rewrite my message to be more loving and likely to be well-received' if message_type == MessageType.TRANSFORM.value else 'analyze the emotions and needs behind the message and suggest a loving, empathetic response. Provide a detailed explanation of the sender\\'s subtext and needs.'}"
        )

        payload = {
            "model": self.available_models[0],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": AppConfig.MAX_TOKENS,
            "temperature": AppConfig.TEMPERATURE,
            "response_format": {"type": "json_object"} if "gpt" in self.available_models[0].lower() else None
        }

        # Make API call
        response_data = self._make_robust_ai_request(payload)
        if response_data and "choices" in response_data and response_data["choices"]:
            try:
                content = response_data["choices"][0]["message"]["content"]
                content = content.strip().strip("```json").strip("```").strip()
                ai_data = json.loads(content)
                ai_response = AIResponse(
                    transformed_message=ai_data.get("transformed_message", ""),
                    healing_score=min(ai_data.get("healing_score", 0), 10),
                    sentiment=self._normalize_sentiment(ai_data.get("sentiment", "unknown")),
                    emotional_state=self._normalize_emotional_state(ai_data.get("emotional_state", "unclear")),
                    explanation=ai_data.get("explanation", ""),
                    subtext=ai_data.get("subtext", ""),
                    needs=ai_data.get("needs", []),
                    warnings=ai_data.get("warnings", [])
                )
                if not ai_response.transformed_message:
                    raise ValueError("No transformed message in response")
                db.save_to_cache(contact_id, message_hash, contact_context, ai_response.transformed_message,
                                user_id, ai_response)
                return ai_response
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.error(f"Error parsing API response: {str(e)}")

        # Fallback for failed API calls
        message_lower = message.lower()
        if message_type == MessageType.TRANSFORM.value:
            subtext = ""
            needs = []
            warnings = []
            if "angry" in message_lower or "frustrated" in message_lower:
                subtext = "The user is expressing frustration or anger."
                needs = ["understanding", "calmness"]
                warnings = ["Avoid escalating the tone further."]
            ai_data = {
                "transformed_message": (
                    f"I feel {self._normalize_emotional_state('hurt')} about this situation. "
                    "Can we discuss how to make things better?"
                ),
                "healing_score": 5,
                "sentiment": "neutral",
                "emotional_state": "calm",
                "explanation": (
                    "This response uses 'I' statements to express feelings without blame, "
                    "encouraging collaboration."
                ),
                "subtext": subtext,
                "needs": needs,
                "warnings": warnings
            }
        else:  # INTERPRET
            subtext = "The sender may be feeling frustrated or unheard."
            needs = ["communication", "understanding"]
            warnings = []
            if "late" in message_lower or "time" in message_lower:
                subtext = "The sender is frustrated about punctuality and may feel disrespected."
                needs = ["reliability", "respect"]
                if "father" in message_lower or "mother" in message_lower:
                    warnings.append("Personal criticism may escalate tension.")
            elif "divorce" in message_lower or "custody" in message_lower:
                subtext = "The sender may feel stressed about co-parenting responsibilities."
                needs = ["cooperation", "clarity"]
                warnings.append("Legal or emotional sensitivity detected.")
            elif "never" in message_lower or "always" in message_lower:
                subtext = "The sender feels consistently let down or ignored."
                needs = ["validation", "consistency"]
                warnings.append("Absolutist language may indicate deeper unresolved issues.")
            ai_data = {
                "transformed_message": (
                    "I hear how challenging this is for you. Can we work together to find a solution "
                    "that supports our relationship?"
                ),
                "healing_score": 6,
                "sentiment": "neutral",
                "emotional_state": "empathetic",
                "explanation": (
                    "The response acknowledges the sender's emotions, offers collaboration, and "
                    "avoids defensiveness."
                ),
                "subtext": subtext,
                "needs": needs,
                "warnings": warnings
            }

        ai_response = AIResponse(
            transformed_message=ai_data["transformed_message"],
            healing_score=ai_data["healing_score"],
            sentiment=ai_data["sentiment"],
            emotional_state=ai_data["emotional_state"],
            explanation=ai_data["explanation"],
            subtext=ai_data.get("subtext", ""),
            needs=ai_data.get("needs", []),
            warnings=ai_data.get("warnings", [])
        )
        db.save_to_cache(contact_id, message_hash, contact_context, ai_response.transformed_message,
                        user_id, ai_response)
        return ai_response
```