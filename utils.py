# utils.py - The Third Voice AI Utilities
# Helper functions, error handling, and common operations

import streamlit as st
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from config import HEALING_SCORE_THRESHOLDS, CONTEXTS

class Utils:
    """Utility functions for The Third Voice AI"""
    
    @staticmethod
    def create_message_hash(message: str, context: str) -> str:
        """
        Create a hash for message caching
        
        Args:
            message: The message content
            context: The relationship context
            
        Returns:
            MD5 hash string
        """
        return hashlib.md5(f"{message.strip().lower()}{context}".encode()).hexdigest()
    
    @staticmethod
    def format_timestamp(timestamp: datetime) -> str:
        """
        Format timestamp for display
        
        Args:
            timestamp: DateTime object
            
        Returns:
            Formatted string (MM/DD HH:MM)
        """
        return timestamp.strftime("%m/%d %H:%M")
    
    @staticmethod
    def get_current_utc_timestamp() -> str:
        """
        Get current UTC timestamp as ISO string
        
        Returns:
            ISO formatted timestamp string
        """
        return datetime.now(timezone.utc).isoformat()
    
    @staticmethod
    def parse_timestamp(timestamp_str: str) -> datetime:
        """
        Parse timestamp string to datetime object
        
        Args:
            timestamp_str: ISO timestamp string
            
        Returns:
            DateTime object
        """
        # Handle both formats: with and without 'Z'
        if timestamp_str.endswith('Z'):
            timestamp_str = timestamp_str.replace('Z', '+00:00')
        return datetime.fromisoformat(timestamp_str)
    
    @staticmethod
    def calculate_healing_score(ai_response: str, context: str, history: List[Dict] = None) -> int:
        """
        Calculate healing score for AI response
        
        Args:
            ai_response: The AI generated response
            context: Relationship context
            history: Conversation history (optional)
            
        Returns:
            Healing score (1-10)
        """
        score = 5  # Base score
        
        # Length bonus
        if len(ai_response) > 200:
            score += 1
        
        # Content quality bonus
        healing_words = ["understand", "love", "connect", "care", "heal", "support", "listen"]
        score += min(2, sum(1 for word in healing_words if word in ai_response.lower()))
        
        # Relationship memory bonus
        if history and any(keyword in ai_response.lower() for keyword in ["pattern", "before", "previously", "remember"]):
            score += 1
        
        # Context-specific bonus
        if context == "romantic" and any(word in ai_response.lower() for word in ["partner", "relationship", "together"]):
            score += 1
        elif context == "coparenting" and any(word in ai_response.lower() for word in ["children", "kids", "parenting"]):
            score += 1
        
        return min(10, score)
    
    @staticmethod
    def get_healing_score_color(score: int) -> str:
        """
        Get color indicator for healing score
        
        Args:
            score: Healing score (1-10)
            
        Returns:
            Color emoji string
        """
        if score >= HEALING_SCORE_THRESHOLDS["excellent"]:
            return "🟢"
        elif score >= HEALING_SCORE_THRESHOLDS["good"]:
            return "🟡"
        else:
            return "🔴"
    
    @staticmethod
    def get_healing_score_message(score: int) -> str:
        """
        Get descriptive message for healing score
        
        Args:
            score: Healing score (1-10)
            
        Returns:
            Descriptive message
        """
        if score >= HEALING_SCORE_THRESHOLDS["excellent"]:
            return f"✨ Healing Score: {score}/10 - Very revealing analysis"
        elif score >= HEALING_SCORE_THRESHOLDS["good"]:
            return f"💡 Healing Score: {score}/10 - Good understanding"
        else:
            return f"🔧 Healing Score: {score}/10 - Basic analysis"
    
    @staticmethod
    def detect_message_type(message: str) -> str:
        """
        Detect if message is incoming or outgoing
        
        Args:
            message: The message content
            
        Returns:
            "translate" for incoming, "coach" for outgoing
        """
        incoming_indicators = ["said:", "wrote:", "texted:", "told me:", "they said", "he said", "she said"]
        is_incoming = any(indicator in message.lower() for indicator in incoming_indicators)
        return "translate" if is_incoming else "coach"
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
        """
        Truncate text to specified length
        
        Args:
            text: Text to truncate
            max_length: Maximum length
            suffix: Suffix to add if truncated
            
        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Basic email validation
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid format, False otherwise
        """
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        """
        Validate password strength
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < 6:
            return False, "Password must be at least 6 characters long."
        return True, ""
    
    @staticmethod
    def clean_contact_name(name: str) -> str:
        """
        Clean and validate contact name
        
        Args:
            name: Contact name to clean
            
        Returns:
            Cleaned contact name
        """
        return name.strip().title()
    
    @staticmethod
    def get_context_display_name(context_key: str) -> str:
        """
        Get display name for context
        
        Args:
            context_key: Context key from CONTEXTS
            
        Returns:
            Formatted display name
        """
        context_data = CONTEXTS.get(context_key, {"icon": "💬", "description": "Unknown"})
        return f"{context_data['icon']} {context_key.title()}"
    
    @staticmethod
    def safe_json_serialize(obj: Any) -> str:
        """
        Safely serialize object to JSON
        
        Args:
            obj: Object to serialize
            
        Returns:
            JSON string or error message
        """
        try:
            return json.dumps(obj, indent=2, default=str)
        except (TypeError, ValueError) as e:
            return f"<Serialization Error: {e}>"
    
    @staticmethod
    def handle_error(error: Exception, context: str = "Unknown", user_friendly: bool = True) -> str:
        """
        Handle and format errors consistently
        
        Args:
            error: The exception that occurred
            context: Context where error occurred
            user_friendly: Whether to return user-friendly message
            
        Returns:
            Formatted error message
        """
        error_msg = str(error)
        
        if user_friendly:
            # Convert technical errors to user-friendly messages
            if "timeout" in error_msg.lower():
                return "Request timed out. Please try again."
            elif "connection" in error_msg.lower():
                return "Connection error. Please check your internet connection."
            elif "authentication" in error_msg.lower():
                return "Authentication failed. Please check your credentials."
            else:
                return f"An error occurred in {context}. Please try again."
        else:
            return f"Error in {context}: {error_msg}"
    
    @staticmethod
    def is_mobile_device() -> bool:
        """
        Detect if user is on mobile device (simple check)
        
        Returns:
            True if likely mobile, False otherwise
        """
        # This is a simple check - in a real app you might use user agent detection
        # For now, we'll assume mobile-first design
        return True
    
    @staticmethod
    def format_conversation_preview(message: str, max_length: int = 40) -> str:
        """
        Format message for conversation list preview
        
        Args:
            message: Message to format
            max_length: Maximum preview length
            
        Returns:
            Formatted preview string
        """
        if not message:
            return "Start your first conversation!"
        
        # Clean up the message
        cleaned = message.replace('\n', ' ').strip()
        return Utils.truncate_text(cleaned, max_length)
    
    @staticmethod
    def get_relationship_health_status(avg_score: float) -> str:
        """
        Get relationship health status based on average healing score
        
        Args:
            avg_score: Average healing score
            
        Returns:
            Health status description
        """
        if avg_score >= 8:
            return "Thriving - Excellent communication patterns"
        elif avg_score >= 6:
            return "Growing - Good progress with room to improve"
        elif avg_score >= 4:
            return "Healing - Working through challenges together"
        else:
            return "Struggling - Focus on understanding and patience"

# Global utils instance
utils = Utils()
