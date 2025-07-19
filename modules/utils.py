"""
Utility functions for The Third Voice AI
API calls, formatting, and helper functions
"""

import requests
import datetime
import streamlit as st
from typing import Dict, Any, Optional

from .config import API_URL, AI_MODELS
from .prompts import create_message_payload, detect_message_type

def get_ai_response(message: str, context: str, is_received: bool = False) -> Dict[str, Any]:
    """
    Get AI response from OpenRouter API with fallback models
    
    Args:
        message: The user's message
        context: Relationship context
        is_received: Whether this is a received message to analyze
        
    Returns:
        Dictionary containing AI response and metadata
    """
    api_key = st.session_state.get('api_key', '')
    if not api_key:
        return {"error": "No API key configured"}
    
    # Create the message payload
    messages = create_message_payload(message, context, is_received)
    
    # Try each model in sequence for reliability
    for model in AI_MODELS:
        try:
            response = requests.post(
                API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                timeout=30
            )
            
            response.raise_for_status()
            result_data = response.json()
            
            if "choices" in result_data and len(result_data["choices"]) > 0:
                ai_reply = result_data["choices"][0]["message"]["content"]
                model_name = format_model_name(model)
                
                # Detect message type for special handling
                message_type = detect_message_type(message)
                
                return format_ai_response(
                    message=message,
                    ai_reply=ai_reply,
                    model=model_name,
                    is_received=is_received,
                    message_type=message_type
                )
            
        except requests.exceptions.RequestException as e:
            # Log the error and try next model
            continue
        except Exception as e:
            # Unexpected error, try next model
            continue
    
    return {"error": "All AI models failed to respond"}

def format_ai_response(message: str, ai_reply: str, model: str, is_received: bool, message_type: str) -> Dict[str, Any]:
    """
    Format the AI response into a standardized structure
    
    Args:
        message: Original message
        ai_reply: AI's response
        model: Model name used
        is_received: Whether analyzing received message
        message_type: Detected message type
        
    Returns:
        Formatted response dictionary
    """
    if is_received:
        return {
            "type": "translate",
            "sentiment": "neutral",
            "meaning": f"Interpretation: {ai_reply[:100]}...",
            "response": ai_reply,
            "original": message,
            "model": model,
            "message_type": message_type
        }
    else:
        return {
            "type": "coach", 
            "sentiment": "improved",
            "original": message,
            "improved": ai_reply,
            "model": model,
            "message_type": message_type
        }

def format_model_name(model_string: str) -> str:
    """
    Format model string into a readable name
    
    Args:
        model_string: Raw model string from API
        
    Returns:
        Formatted, readable model name
    """
    return (model_string
            .split("/")[-1]
            .replace(":free", "")
            .replace("-", " ")
            .title())

def create_history_entry(message: str, result: Dict[str, Any], entry_type: str) -> Dict[str, Any]:
    """
    Create a standardized history entry
    
    Args:
        message: Original message
        result: AI response result
        entry_type: Type of entry ('coach' or 'translate')
        
    Returns:
        Formatted history entry
    """
    timestamp = datetime.datetime.now()
    
    return {
        "id": f"{entry_type}_{timestamp.timestamp()}",
        "time": timestamp.strftime("%m/%d %H:%M"),
        "type": entry_type,
        "original": message,
        "result": result.get("improved" if entry_type == "coach" else "response", ""),
        "sentiment": result.get("sentiment", "neutral"),
        "model": result.get("model", "Unknown"),
        "message_type": result.get("message_type", "normal"),
        "timestamp": timestamp.isoformat()
    }

def validate_token(token: str) -> bool:
    """
    Validate beta access token
    
    Args:
        token: Token to validate
        
    Returns:
        True if valid, False otherwise
    """
    from .config import VALID_TOKENS
    return token in VALID_TOKENS

def generate_filename(prefix: str = "third_voice") -> str:
    """
    Generate a timestamped filename
    
    Args:
        prefix: Filename prefix
        
    Returns:
        Formatted filename with timestamp
    """
    timestamp = datetime.datetime.now().strftime('%m%d_%H%M')
    return f"{prefix}_{timestamp}.json"

def truncate_text(text: str, max_length: int = 50) -> str:
    """
    Truncate text with ellipsis
    
    Args:
        text: Text to truncate
        max_length: Maximum length before truncation
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def format_time_ago(timestamp_str: str) -> str:
    """
    Format timestamp as time ago
    
    Args:
        timestamp_str: ISO format timestamp string
        
    Returns:
        Human readable time ago string
    """
    try:
        timestamp = datetime.datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.datetime.now()
        diff = now - timestamp
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"
    except:
        return "Unknown"

def sanitize_input(text: str) -> str:
    """
    Sanitize user input for safety
    
    Args:
        text: Raw user input
        
    Returns:
        Sanitized text
    """
    # Basic sanitization - remove excessive whitespace and limit length
    text = text.strip()
    if len(text) > 5000:  # Reasonable limit for messages
        text = text[:5000]
    return text

def get_message_stats(history: list) -> Dict[str, int]:
    """
    Calculate statistics for message history
    
    Args:
        history: List of history entries
        
    Returns:
        Dictionary with message statistics
    """
    if not history:
        return {'total': 0, 'coached': 0, 'translated': 0}
    
    coached = sum(1 for entry in history if entry.get('type') == 'coach')
    translated = sum(1 for entry in history if entry.get('type') == 'translate')
    
    return {
        'total': len(history),
        'coached': coached,
        'translated': translated
    }

def health_check() -> Dict[str, bool]:
    """
    Perform basic health checks
    
    Returns:
        Dictionary with health check results
    """
    checks = {
        'api_key_configured': bool(st.session_state.get('api_key')),
        'session_initialized': 'contacts' in st.session_state,
        'active_contact_valid': (
            st.session_state.get('active_contact', '') in 
            st.session_state.get('contacts', {})
        )
    }
    
    return checks
