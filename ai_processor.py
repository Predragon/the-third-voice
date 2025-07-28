# ai_processor.py - The Third Voice AI Processing Engine
# OpenRouter integration with mobile-optimized error handling

import streamlit as st
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List
from config import API_URL, MODEL, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS, API_TIMEOUT, ERROR_MESSAGES
from utils import utils
from auth_manager import auth_manager
from data_manager import data_manager

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
        api_key = self._get_api_key()
        if not api_key:
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
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=self.timeout)
            response_json = response.json()
            
            if "choices" in response_json and len(response_json["choices"]) > 0:
                return {
                    "response": response_json["choices"][0]["message"]["content"].strip(),
                    "model": self.model,
                    "success": True
                }
            else:
                return {"error": f"API response missing 'choices': {response_json}", "success": False}
                
        except requests.exceptions.Timeout:
            return {"error": ERROR_MESSAGES["network_timeout"], "success": False}
        except requests.exceptions.ConnectionError:
            return {"error": ERROR_MESSAGES["connection_error"], "success": False}
        except requests.exceptions.RequestException as e:
            return {"error": f"Network error: {e}", "success": False}
        except Exception as e:
            return {"error": f"Unexpected error: {e}", "success": False}
    
    def get_enhanced_system_prompt(self, contact_name: str, context: str, message: str, history: List[Dict] = None) -> str:
        """
        Build relationship-aware prompts with conversation memory
        
        Args:
            contact_name: Name of the contact
            context: Relationship context
            message: Current message
            history: Conversation history
            
        Returns:
            Enhanced system prompt
        """
        base_prompt = f"You are a compassionate relationship guide helping with a {context} relationship with {contact_name}."
        
        if not history or len(history) < 2:
            return base_prompt + " This is an early conversation, so focus on building understanding."
        
        # Add relationship context
        patterns = self.analyze_conversation_patterns(history)
        themes = self.identify_recurring_themes(history)
        
        relationship_context = f"""
RELATIONSHIP INSIGHTS:
- Conversation patterns: {patterns}
- Recurring themes: {themes}
- Total conversations: {len(history)}

Consider this relationship history when providing guidance. Reference patterns where helpful, but don't overwhelm with past details."""
        
        return base_prompt + relationship_context
    
    def analyze_conversation_patterns(self, history: List[Dict]) -> str:
        """
        Identify patterns in conversation history
        
        Args:
            history: Conversation history
            
        Returns:
            Pattern analysis string
        """
        if not history or len(history) < 3:
            return "Limited history available"
        
        # Analyze healing score trends
        recent_scores = [msg.get('healing_score', 0) for msg in history[-5:] if msg.get('healing_score')]
        if recent_scores:
            avg_score = sum(recent_scores) / len(recent_scores)
            trend = "improving" if len(recent_scores) > 1 and recent_scores[-1] > recent_scores[0] else "stable"
            return f"Healing trend: {trend} (avg: {avg_score:.1f}/10)"
        
        return "Building relationship understanding..."
    
    def identify_recurring_themes(self, history: List[Dict]) -> str:
        """
        Find recurring issues and communication patterns
        
        Args:
            history: Conversation history
            
        Returns:
            Themes analysis string
        """
        if not history or len(history) < 2:
            return "New relationship - learning patterns"
        
        # Simple keyword analysis for common themes
        all_messages = " ".join([msg.get('original', '').lower() for msg in history])
        
        themes = []
        theme_keywords = {
            "communication": ["listen", "understand", "hear", "talk"],
            "respect": ["respect", "appreciate", "value", "disrespect"],
            "time": ["time", "busy", "schedule", "priority"],
            "emotions": ["feel", "hurt", "angry", "sad", "frustrated"],
            "trust": ["trust", "honest", "lie", "truth"]
        }
        
        for theme, keywords in theme_keywords.items():
            if sum(word in all_messages for word in keywords) >= 2:
                themes.append(theme)
        
        return ", ".join(themes) if themes else "Varied conversation topics"
    
    def process_message(self, contact_name: str, message: str, context: str, history: List[Dict] = None) -> Dict[str, Any]:
        """
        Process a message with AI guidance
        
        Args:
            contact_name: Name of the contact
            message: Message to process
            context: Relationship context
            history: Conversation history
            
        Returns:
            Processing result dictionary
        """
        if not message.strip():
            return {"error": ERROR_MESSAGES["empty_message"], "success": False}
        
        # Determine message type
        message_type = utils.detect_message_type(message)
        
        # Check cache first
        message_hash = utils.create_message_hash(message, context)
        
        # Get contact data
        from state_manager import state_manager
        contact_data = state_manager.get_contact_data(contact_name)
        contact_id = contact_data.get("id")
        
        if contact_id:
            cached_response = data_manager.get_cached_ai_response(contact_id, message_hash)
            if cached_response:
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
        system_prompt = self.get_enhanced_system_prompt(contact_name, context, message, history)
        
        if message_type == "translate":
            system_prompt += " Understand what they mean and suggest a loving response."
        else:
            system_prompt += " Reframe their message to be constructive and loving."
        
        system_prompt += " Keep it concise, insightful, and actionable (2-3 paragraphs)."
        
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
        if not message.strip():
            return {"error": ERROR_MESSAGES["empty_message"], "success": False}
        
        # Build relationship context from history
        relationship_context = ""
        if history:
            recent_messages = history[-5:]  # Last 5 interactions
            patterns = []
            for msg in recent_messages:
                if msg.get('original') and msg.get('healing_score'):
                    patterns.append(f"Previous: '{msg['original'][:50]}...' (Score: {msg['healing_score']}/10)")
            
            if patterns:
                relationship_context = f"\nRELATIONSHIP CONTEXT:\n" + "\n".join(patterns[-3:])
        
        system_prompt = f"""You are an expert relationship therapist analyzing emotional subtext with deep compassion.

For this {context} relationship message from {contact_name}: "{message}"
{relationship_context}

Provide insights in exactly this format:

**🎭 EMOTIONAL SUBTEXT**
What they're really feeling beneath the words (1-2 sentences)

**💔 UNMET NEEDS** 
What they actually need but can't express (1-2 sentences)

**🌱 HEALING OPPORTUNITIES**
Specific ways to address their deeper needs (2-3 actionable suggestions)

**⚠️ WATCH FOR**
Relationship patterns or warning signs (1 sentence)

Be direct but loving. This person is trying to heal their family."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze this message: {message}"}
        ]
        
        result = self._make_api_request(messages, temperature=0.6, max_tokens=400)
        
        if result["success"]:
            # Calculate interpretation score (how revealing/useful)
            interpretation_score = 5
            interpretation = result["response"]
            
            if len(interpretation) > 300:
                interpretation_score += 1
            if any(word in interpretation.lower() for word in ["fear", "hurt", "love", "safe", "understand"]):
                interpretation_score += 2
            if "healing opportunities" in interpretation.lower():
                interpretation_score += 2
            interpretation_score = min(10, interpretation_score)
            
            return {
                "interpretation": interpretation,
                "interpretation_score": interpretation_score,
                "model": result["model"],
                "success": True
            }
        else:
            return result
    
    def calculate_relationship_health_score(self, history: List[Dict]) -> tuple[float, str]:
        """
        Calculate overall relationship health based on conversation history
        
        Args:
            history: Conversation history
            
        Returns:
            Tuple of (health_score, status_description)
        """
        if not history:
            return 0.0, "No data yet"
        
        # Get healing scores from last 10 conversations
        recent_scores = [msg.get('healing_score', 0) for msg in history[-10:] if msg.get('healing_score')]
        
        if not recent_scores:
            return 0.0, "No scored conversations yet"
        
        avg_score = sum(recent_scores) / len(recent_scores)
        status = utils.get_relationship_health_status(avg_score)
        
        return round(avg_score, 1), status
    
    def get_healing_insights(self, history: List[Dict]) -> List[str]:
        """
        Generate insights about healing progress
        
        Args:
            history: Conversation history
            
        Returns:
            List of insight strings
        """
        if not history or len(history) < 3:
            return ["🌱 You're just getting started! Every conversation is a step toward healing."]
        
        insights = []
        
        # Score trend analysis
        scores = [msg.get('healing_score', 0) for msg in history if msg.get('healing_score')]
        if len(scores) >= 5:
            recent_avg = sum(scores[-5:]) / 5
            older_avg = sum(scores[-10:-5]) / 5 if len(scores) >= 10 else sum(scores[:-5]) / len(scores[:-5])
            
            if recent_avg > older_avg + 0.5:
                insights.append("📈 Your communication is improving! Recent conversations show higher healing scores.")
            elif recent_avg < older_avg - 0.5:
                insights.append("💪 Having some challenges lately? That's normal - healing isn't always linear.")
        
        # High score celebrations
        high_scores = [score for score in scores if score >= 8]
        if len(high_scores) >= 3:
            insights.append(f"🌟 Amazing! You've had {len(high_scores)} conversations with healing scores of 8+!")
        
        # Consistency insights  
        if len(scores) >= 7:
            consistency = len([s for s in scores[-7:] if s >= 6]) / 7
            if consistency >= 0.7:
                insights.append("🎯 You're building consistent healthy communication patterns!")
        
        # Encourage if struggling
        if scores and max(scores[-5:]) < 6:
            insights.append("🤗 Remember: every family faces challenges. You're here working on it - that matters.")
        
        return insights if insights else ["💙 Keep going - healing happens one conversation at a time."]

# Global AI processor instance
ai_processor = AIProcessor()
