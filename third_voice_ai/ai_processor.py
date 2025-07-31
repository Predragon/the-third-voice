import logging
import logging
# ai_processor.py - The Third Voice AI Processing Engine
# OpenRouter integration with mobile-optimized error handling

import streamlit as st
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List
from .config import API_URL, MODEL, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS, API_TIMEOUT, ERROR_MESSAGES
from .utils import utils
from .auth_manager import auth_manager
from .data_manager import data_manager
from .prompts import get_transformation_prompt, get_interpretation_prompt  # Using standalone functions

class AIProcessor:
    """
    AI processing engine for The Third Voice AI
    Handles OpenRouter API calls with intelligent caching and error handling
    """
    
    def __init__(self):
        """Initialize AI processor"""
        self.api_url = API_URL
        self.model = MODEL
        self.temperature = DEFAULT_TEMPERATURE
        self.max_tokens = DEFAULT_MAX_TOKENS
        self.timeout = API_TIMEOUT
    
    def _get_api_key(self) -> Optional[str]:
        """
        Get OpenRouter API key from secrets
        
        Returns:
            API key or None if not found
        """
        try:
            return st.secrets["openrouter"]["api_key"]
        except KeyError:
            return None
    
    def _make_api_request(self, messages: List[Dict[str, str]], temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Make API request to OpenRouter
        
        Args:
            messages: List of message dictionaries
            temperature: Override default temperature
            max_tokens: Override default max tokens
            
        Returns:
            API response dictionary
        """
        logger = logging.getLogger(__name__)
        api_key = self._get_api_key()
        if not api_key:
            logger.error("No OpenRouter API key found in secrets")
            return {"error": ERROR_MESSAGES["no_api_key"], "success": False}
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature or self.temperature,
            "max_tokens": max_tokens or self.max_tokens
        }
        
        try:
            logger.debug(f"Sending API request: model={self.model}, messages={messages[:100]}...")
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
            response_json = response.json()
            
            if "choices" in response_json and len(response_json["choices"]) > 0:
                result = {
                    "response": response_json["choices"][0]["message"]["content"].strip(),
                    "model": self.model,
                    "success": True
                }
                logger.info(f"API request successful: response_length={len(result['response'])}")
                return result
            else:
                logger.error(f"API response missing 'choices': {response_json}")
                return {"error": f"API response missing 'choices': {response_json}", "success": False}
                
        except requests.exceptions.Timeout:
            logger.error(f"API request timed out after {self.timeout} seconds")
            return {"error": ERROR_MESSAGES["network_timeout"], "success": False}
        except requests.exceptions.ConnectionError:
            logger.error("API request failed due to connection error")
            return {"error": ERROR_MESSAGES["connection_error"], "success": False}
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return {"error": f"Network error: {e}", "success": False}
        except Exception as e:
            logger.exception(f"Unexpected error in API request: {str(e)}")
            return {"error": f"Unexpected error: {e}", "success": False}
    
    def process_message(self, contact_name: str, message: str, context: str, history: List[Dict] = None, is_incoming: bool = False) -> Dict[str, Any]:
        """
        Process a message with AI guidance
        
        Args:
            contact_name: Name of the contact
            message: Message to process
            context: Relationship context
            history: Conversation history
            is_incoming: Whether the message is incoming (translate) or outgoing (coach)
            
        Returns:
            Processing result dictionary
        """
        from .state_manager import state_manager
        logger = logging.getLogger(__name__)
        
        if not message.strip():
            logger.warning("Empty message provided")
            return {"error": ERROR_MESSAGES["empty_message"], "success": False}
        
        # Determine message type
        message_type = utils.detect_message_type(message)
        logger.debug(f"Detected message type: {message_type}, is_incoming: {is_incoming}")
        
        # Check cache first
        message_hash = utils.create_message_hash(message, context)
        contact_data = state_manager.get_contact_data(contact_name)
        contact_id = contact_data.get("id")
        
        if contact_id:
            cached_response = data_manager.get_cached_ai_response(contact_id, message_hash)
            if cached_response:
                logger.info(f"Returning cached response for {contact_name}, hash: {message_hash}")
                return {
                    "response": cached_response["response"],
                    "healing_score": cached_response["healing_score"],
                    "sentiment": cached_response["sentiment"],
                    "emotional_state": cached_response["emotional_state"],
                    "model": cached_response["model"],
                    "message_type": message_type,
                    "cached": True,
                    "success": True
                }
        
        # Generate new response
        system_prompt = get_transformation_prompt(contact_name, context, message, history, is_incoming)
        logger.debug(f"Transformation prompt: {system_prompt[:200]}...")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        result = self._make_api_request(messages)
        
        if result["success"]:
            # Calculate healing score
            healing_score = utils.calculate_healing_score(result["response"], context, history)
            
            # Default sentiment and emotional state
            sentiment = "neutral"
            emotional_state = "calm"
            
            # Cache the response
            if contact_id:
                data_manager.cache_ai_response(
                    contact_id, message_hash, context, result["response"],
                    healing_score, result["model"], sentiment, emotional_state
                )
            
            logger.info(f"Generated new response for {contact_name}, healing_score: {healing_score}")
            return {
                "response": result["response"],
                "healing_score": healing_score,
                "sentiment": sentiment,
                "emotional_state": emotional_state,
                "model": result["model"],
                "message_type": message_type,
                "cached": False,
                "success": True
            }
        else:
            logger.error(f"AI processing failed for {contact_name}: {result['error']}")
            return result
    
    def interpret_message(self, contact_name: str, message: str, context: str, history: List[Dict] = None) -> Dict[str, Any]:
        """
        Interpret emotional subtext and healing opportunities
        
        Args:
            contact_name: Name of the contact
            message: Message to interpret
            context: Relationship context
            history: Conversation history
            
        Returns:
            Interpretation result dictionary
        """
        from .state_manager import state_manager
        logger = logging.getLogger(__name__)
        
        if not message.strip():
            logger.warning("Empty message provided for interpretation")
            return {"error": ERROR_MESSAGES["empty_message"], "success": False}
        
        system_prompt = get_interpretation_prompt(contact_name, context, message, history)
        logger.debug(f"Interpretation prompt: {system_prompt[:200]}...")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze this message: {message}"}
        ]
        
        result = self._make_api_request(messages, temperature=0.8, max_tokens=400)
        
        if result["success"]:
            # Calculate interpretation score
            interpretation_score = 5
            interpretation = result["response"]
            
            if len(interpretation) > 300:
                interpretation_score += 1
            if any(word in interpretation.lower() for word in ["fear", "hurt", "love", "safe", "understand"]):
                interpretation_score += 2
            if "healing opportunities" in interpretation.lower():
                interpretation_score += 2
            interpretation_score = min(10, interpretation_score)
            
            logger.info(f"Generated interpretation for {contact_name}, score: {interpretation_score}, response_length: {len(interpretation)}")
            return {
                "interpretation": interpretation,
                "interpretation_score": interpretation_score,
                "model": result["model"],
                "success": True
            }
        else:
            logger.error(f"Interpretation failed for {contact_name}: {result['error']}")
            return result
    
    def calculate_relationship_health_score(self, history: List[Dict]) -> tuple[float, str]:
        """
        Calculate overall relationship health based on conversation history
        
        Args:
            history: Conversation history
            
        Returns:
            Tuple of (health_score, status_description)
        """
        logger = logging.getLogger(__name__)
        if not history:
            logger.debug("No history provided for health score calculation")
            return 0.0, "No data yet"
        
        recent_scores = [msg.get('healing_score', 0) for msg in history[-10:] if msg.get('healing_score')]
        
        if not recent_scores:
            logger.debug("No scored conversations in history")
            return 0.0, "No scored conversations yet"
        
        avg_score = sum(recent_scores) / len(recent_scores)
        status = utils.get_relationship_health_status(avg_score)
        
        logger.debug(f"Calculated health score: {avg_score}, status: {status}")
        return round(avg_score, 1), status
    
    def get_healing_insights(self, history: List[Dict]) -> List[str]:
        """
        Generate insights about healing progress
        
        Args:
            history: Conversation history
            
        Returns:
            List of insight strings
        """
        logger = logging.getLogger(__name__)
        if not history or len(history) < 3:
            logger.debug("Insufficient history for insights")
            return ["🌱 You're just getting started! Every conversation is a step toward healing."]
        
        insights = []
        
        scores = [msg.get('healing_score', 0) for msg in history if msg.get('healing_score')]
        if len(scores) >= 5:
            recent_avg = sum(scores[-5:]) / 5
            older_avg = sum(scores[-10:-5]) / 5 if len(scores) >= 10 else sum(scores[:-5]) / len(scores[:-5])
            
            if recent_avg > older_avg + 0.5:
                insights.append("📈 Your communication is improving! Recent conversations show higher healing scores.")
            elif recent_avg < older_avg - 0.5:
                insights.append("💪 Having some challenges lately? That's normal - healing isn't linear.")
        
        high_scores = [score for score in scores if score >= 8]
        if len(high_scores) >= 3:
            insights.append(f"🌟 Amazing! You've had {len(high_scores)} conversations with healing scores of 8+!")
        
        if len(scores) >= 7:
            consistency = len([s for s in scores[-7:] if s >= 6]) / 7
            if consistency >= 0.7:
                insights.append("🎯 You're building consistent healthy communication patterns!")
        
        if scores and max(scores[-5:]) < 6:
            insights.append("🤗 Remember: every family faces challenges. You're here working on it - that matters.")
        
        logger.debug(f"Generated insights: {insights}")
        return insights if insights else ["💙 Keep going - healing happens one conversation at a time."]

# Global AI processor instance
ai_processor = AIProcessor()
