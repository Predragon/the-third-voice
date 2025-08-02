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
from .prompts import get_transformation_prompt, get_interpretation_prompt
from . import get_logger

class AIProcessor:
    def __init__(self):
        """Initialize AI processor"""
        self.api_url = API_URL
        self.model = MODEL
        self.temperature = DEFAULT_TEMPERATURE
        self.max_tokens = DEFAULT_MAX_TOKENS
        self.timeout = API_TIMEOUT
    
    def _get_api_key(self) -> Optional[str]:
        try:
            return st.secrets["openrouter"]["api_key"]
        except KeyError:
            return None
    
    def _make_api_request(self, messages: List[Dict[str, str]], temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> Dict[str, Any]:
        self.logger = get_logger("ai_processor")
        api_key = self._get_api_key()
        if not api_key:
            self.logger.error("No OpenRouter API key found in secrets")
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
            self.logger.debug(f"Sending API request: model={self.model}, messages={messages[:100]}...")
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
            response_json = response.json()
            
            if "choices" in response_json and len(response_json["choices"]) > 0:
                result = {
                    "response": response_json["choices"][0]["message"]["content"].strip(),
                    "model": self.model,
                    "success": True
                }
                self.logger.info(f"API request successful: response_length={len(result['response'])}")
                return result
            else:
                self.logger.error(f"API response missing 'choices': {response_json}")
                return {"error": f"API response missing 'choices': {response_json}", "success": False}
                
        except requests.exceptions.Timeout:
            self.logger.error(f"API request timed out after {self.timeout} seconds")
            return {"error": ERROR_MESSAGES["network_timeout"], "success": False}
        except requests.exceptions.ConnectionError:
            self.logger.error("API request failed due to connection error")
            return {"error": ERROR_MESSAGES["connection_error"], "success": False}
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {str(e)}")
            return {"error": f"Network error: {e}", "success": False}
        except Exception as e:
            self.logger.exception(f"Unexpected error in API request: {str(e)}")
            return {"error": f"Unexpected error: {e}", "success": False}
    
    def process_message(self, contact_name: str, message: str, context: str, history: List[Dict] = None, is_incoming: bool = False, instruction: Optional[str] = None) -> Dict[str, Any]:
        from .state_manager import state_manager
        self.logger = get_logger("ai_processor")
        
        if not message.strip():
            self.logger.warning("Empty message provided")
            return {"error": ERROR_MESSAGES["empty_message"], "success": False}
        
        # Check cache first
        message_hash = utils.create_message_hash(message, context)
        contact_data = state_manager.get_contact_data(contact_name)
        contact_id = contact_data.get("id")
        
        if contact_id:
            cached_response = data_manager.get_cached_ai_response(contact_id, message_hash)
            if cached_response:
                self.logger.info(f"Returning cached response for {contact_name}, hash: {message_hash}")
                return {
                    "response": cached_response["response"],
                    "healing_score": cached_response["healing_score"],
                    "sentiment": cached_response["sentiment"],
                    "emotional_state": cached_response["emotional_state"],
                    "model": cached_response["model"],
                    "message_type": "coach" if not is_incoming else "interpretation",
                    "cached": True,
                    "success": True
                }
        
        # Generate new response
        system_prompt = instruction or get_transformation_prompt(contact_name, context, message, history, is_incoming)
        self.logger.debug(f"Prompt: {system_prompt[:200]}...")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        result = self._make_api_request(messages, temperature=0.8 if is_incoming else self.temperature, max_tokens=400 if is_incoming else self.max_tokens)
        
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
            
            self.logger.info(f"Generated new response for {contact_name}, healing_score: {healing_score}")
            return {
                "response": result["response"],
                "healing_score": healing_score,
                "sentiment": sentiment,
                "emotional_state": emotional_state,
                "model": result["model"],
                "message_type": "coach" if not is_incoming else "interpretation",
                "cached": False,
                "success": True
            }
        else:
            self.logger.error(f"AI processing failed for {contact_name}: {result['error']}")
            return result
    
    def interpret_message(self, contact_name: str, message: str, context: str, history: List[Dict] = None) -> Dict[str, Any]:
        return self.process_message(
            contact_name=contact_name,
            message=message,
            context=context,
            history=history,
            is_incoming=True,
            instruction="Analyze the emotional subtext of this incoming message from {contact_name}. Identify underlying emotions, unmet needs, and suggest actionable ways to respond that foster healing in the {context} context."
        )
