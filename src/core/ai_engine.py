"""
AI Engine Module - Enhanced Version
Improved message processing with better content analysis and fallback responses
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
    """AI processing engine using OpenRouter with enhanced message analysis"""
    
    def __init__(self):
        pass
    
    def _create_message_hash(self, message: str, contact_context: str, message_type: str) -> str:
        """Create a hash for caching purposes with version for cache invalidation"""
        # Updated version to fix content analysis issues
        CACHE_VERSION = "v2.0"  
        
        # Clean message to avoid whitespace issues
        clean_message = message.strip()
        combined = f"{clean_message}_{contact_context}_{message_type}_{CACHE_VERSION}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _analyze_message_content(self, message: str) -> dict:
        """Analyze message content to determine appropriate response"""
        message_lower = message.lower()
        
        # Business/project feedback analysis
        if any(word in message_lower for word in ["conceptual idea", "success lies", "plagiarized", "stolen", "corporations", "copy protected"]):
            return {
                "topic": "business_feedback",
                "sentiment": "constructive_criticism",
                "keywords": ["idea", "success", "protection", "business concerns"]
            }
        
        # Home renovation/work updates
        if any(word in message_lower for word in ["drywall", "painting", "renovation", "messy", "bloody", "hell of a"]):
            return {
                "topic": "home_work",
                "sentiment": "sharing_experience", 
                "keywords": ["work", "renovation", "effort", "completion"]
            }
        
        # Legal/case updates
        if any(word in message_lower for word in ["case", "prosecutor", "hearing", "legal"]):
            return {
                "topic": "legal_update",
                "sentiment": "informational",
                "keywords": ["legal", "process", "update", "cooperation"]
            }
        
        # Personal feelings/relationships
        if any(word in message_lower for word in ["frustrated", "never help", "appreciate", "upset", "angry"]):
            return {
                "topic": "emotional_expression",
                "sentiment": "emotional",
                "keywords": ["feelings", "relationship", "communication", "needs"]
            }
        
        # General conversation
        return {
            "topic": "general",
            "sentiment": "neutral",
            "keywords": ["conversation", "sharing", "communication"]
        }
    
    def _validate_cached_response(self, cached_response: AIResponse, message: str, 
                                 contact_context: str, message_type: str) -> bool:
        """Enhanced validation that cached response makes sense for the input"""
        
        if not cached_response or not cached_response.transformed_message:
            return False
        
        # Analyze current message content
        content_analysis = self._analyze_message_content(message)
        response_lower = cached_response.transformed_message.lower()
        
        # Check if response matches message topic
        if content_analysis["topic"] == "business_feedback":
            # Business feedback should get business-appropriate responses
            if any(word in response_lower for word in ["busy", "working on", "drywall", "painting"]):
                print("⚠️ Cache validation failed: Business feedback got work update response")
                return False
        
        elif content_analysis["topic"] == "home_work":
            # Home work should get supportive responses about the work
            if not any(word in response_lower for word in ["work", "tough", "effort", "progress", "done", "good"]):
                print("⚠️ Cache validation failed: Home work message got unrelated response")
                return False
        
        elif content_analysis["topic"] == "legal_update":
            # Legal updates should get professional acknowledgment
            if any(word in response_lower for word in ["busy", "drywall", "painting"]):
                print("⚠️ Cache validation failed: Legal update got work response")
                return False
        
        return True
    
    def _create_content_aware_fallback(self, message: str, message_type: str) -> AIResponse:
        """Create content-aware fallback responses based on message analysis"""
        
        content_analysis = self._analyze_message_content(message)
        
        if message_type == MessageType.INTERPRET.value:
            
            if content_analysis["topic"] == "business_feedback":
                return AIResponse(
                    transformed_message="I appreciate you sharing your thoughts on the Third Voice concept. You're right that protecting intellectual property is crucial for any innovative idea. Your feedback about user adoption and business protection shows you're thinking strategically about its potential.",
                    healing_score=7,
                    sentiment="positive",
                    emotional_state="appreciative",
                    explanation="They're providing thoughtful business feedback and expressing genuine concerns about the concept",
                    subtext="They see potential in your idea but want you to consider the practical challenges and protection strategies",
                    needs=["intellectual discussion", "strategic thinking", "business considerations"],
                    warnings=[]
                )
            
            elif content_analysis["topic"] == "home_work":
                return AIResponse(
                    transformed_message="Wow, drywall and painting is tough work! I can totally understand why you wouldn't love that part - it's messy and exhausting. Sounds like you pushed through and got it done though. That's real dedication! 💪",
                    healing_score=8,
                    sentiment="positive",
                    emotional_state="supportive",
                    explanation="They're sharing their work experience and looking for acknowledgment of their effort",
                    subtext="They want recognition for completing difficult, unpleasant work",
                    needs=["acknowledgment", "empathy", "encouragement"],
                    warnings=[]
                )
            
            elif content_analysis["topic"] == "legal_update":
                return AIResponse(
                    transformed_message="Thank you for keeping me informed about the legal situation. I appreciate you handling this and providing updates on the case proceedings.",
                    healing_score=7,
                    sentiment="neutral",
                    emotional_state="professional",
                    explanation="They're providing important legal updates in a professional manner",
                    subtext="They want to maintain communication and transparency about legal matters",
                    needs=["communication", "transparency", "cooperation"],
                    warnings=[]
                )
            
            elif content_analysis["topic"] == "emotional_expression":
                return AIResponse(
                    transformed_message="I can hear that you're feeling frustrated. It sounds like this situation is really affecting you. I want to understand better - can you help me see what would feel most supportive to you right now?",
                    healing_score=8,
                    sentiment="neutral",
                    emotional_state="empathetic",
                    explanation="They're expressing emotional needs and looking for understanding",
                    subtext="They need validation and want to feel heard and understood",
                    needs=["validation", "understanding", "emotional support"],
                    warnings=["Strong emotional content - respond with extra care"]
                )
            
            else:  # general
                return AIResponse(
                    transformed_message="Thank you for sharing that with me. I appreciate you taking the time to communicate and keep me in the loop.",
                    healing_score=6,
                    sentiment="neutral",
                    emotional_state="appreciative",
                    explanation="They're reaching out to share something and maintain connection",
                    subtext="They want to stay connected and share what's on their mind",
                    needs=["connection", "communication", "sharing"],
                    warnings=[]
                )
        
        else:  # TRANSFORM mode
            if "never" in message.lower() or "always" in message.lower():
                return AIResponse(
                    transformed_message="I feel unheard when this happens, and I'd love to find a way we can work together on this. Can we talk about what would work better for both of us?",
                    healing_score=7,
                    sentiment="neutral",
                    emotional_state="constructive",
                    explanation="Transformed absolute statements into collaborative requests using 'I' statements"
                )
            elif any(word in message.lower() for word in ["frustrated", "angry", "upset"]):
                return AIResponse(
                    transformed_message="I'm feeling frustrated about this situation, and I'd really value your perspective. Can we find a time to talk through this together?",
                    healing_score=7,
                    sentiment="neutral", 
                    emotional_state="vulnerable",
                    explanation="Transformed anger into vulnerability and invitation for dialogue"
                )
            else:
                return AIResponse(
                    transformed_message="I have something on my mind that I'd like to share with you. When might be a good time for us to talk?",
                    healing_score=6,
                    sentiment="neutral",
                    emotional_state="open",
                    explanation="Transformed message into an open, non-threatening conversation starter"
                )
    
    def _get_system_prompt(self, message_type: str, relationship_context: str) -> str:
        """Get enhanced system prompt based on message type and context"""
        
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
- Be specific to their actual content

ALWAYS respond with JSON in this exact format:
{{
  "transformed_message": "Your rewritten, more loving version of their message",
  "healing_score": 8,
  "sentiment": "positive",
  "emotional_state": "caring",
  "explanation": "Why this version is more healing and likely to get better results"
}}"""

        else:  # INTERPRET mode
            return f"""You are a relationship communication expert. Your job is to INTERPRET and UNDERSTAND messages someone received, then suggest how to respond appropriately.

CRITICAL: You are in INTERPRET mode. The user RECEIVED a message and needs help understanding what the sender really meant and how to respond.

Your task: Carefully analyze the ACTUAL content and meaning of the message, then suggest an appropriate response.

Context: This is for a {relationship_context} relationship.

INTERPRET ANALYSIS STEPS:
1. READ the actual message content carefully
2. IDENTIFY the main topic (business feedback, work updates, personal sharing, etc.)  
3. ANALYZE the sender's tone and intent
4. DETECT any underlying emotions or needs
5. SUGGEST a response that matches the specific content and context

CONTENT ANALYSIS:
- Business/project feedback → Acknowledge insights and engage intellectually
- Work/renovation updates → Show appreciation for effort and progress
- Personal sharing → Respond with interest and connection
- Emotional expressions → Validate feelings and show empathy
- Casual conversation → Match their energy and show engagement

ALWAYS respond with JSON in this exact format:
{{
  "transformed_message": "A response that directly addresses their actual message content",
  "healing_score": 7,
  "sentiment": "neutral",
  "emotional_state": "appropriate",
  "explanation": "What type of message this is and why this response fits the actual content",
  "subtext": "What the sender is really communicating based on their actual words",
  "needs": ["the sender's likely needs based on what they actually said"],
  "warnings": ["any concerning patterns, or empty array if none"]
}}"""

    def process_message(self, message: str, contact_context: str, message_type: str,
                       contact_id: str, user_id: str, db) -> AIResponse:
        """Process a message with AI and return structured response"""
        
        # Check cache first with enhanced validation
        message_hash = self._create_message_hash(message, contact_context, message_type)
        cached_response = db.check_cache(contact_id, message_hash, user_id)
        
        if cached_response:
            if self._validate_cached_response(cached_response, message, contact_context, message_type):
                return cached_response
            else:
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

Please analyze what they ACTUALLY said and suggest a response that directly addresses their specific content and meaning."""
            
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
                
                # Use content-aware fallback
                return self._create_content_aware_fallback(message, message_type)
            
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
            
            # Cache the response
            db.save_to_cache(
                contact_id, message_hash, contact_context,
                ai_response.transformed_message, user_id, ai_response
            )
            
            return ai_response
            
        except requests.RequestException as e:
            return self._create_content_aware_fallback(message, message_type)
            
        except Exception as e:
            return self._create_content_aware_fallback(message, message_type)
    
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
            'appreciative': 'appreciative',
            'professional': 'professional',
            'constructive': 'constructive',
            'vulnerable': 'vulnerable',
            'open': 'open',
            'appropriate': 'appropriate',
            'unclear': 'unclear',
            'error': 'error'
        }
        
        return state_map.get(emotional_state, 'neutral')
