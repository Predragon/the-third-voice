"""
ai_core.py - Enhanced with Dynamic Model Management from Streamlit Secrets

The sacred heart of our mission: turning pain into healing through AI-guided communication.
Now with unlimited model fallback system managed entirely through Streamlit Cloud secrets.

"When both people are speaking from pain, someone must be the third voice."
"""

import requests
import hashlib
from datetime import datetime, timezone
import streamlit as st


# === AI MODEL CONFIGURATION ===
API_URL = "https://openrouter.ai/api/v1/chat/completions"


def get_available_models():
    """Get AI models from Streamlit secrets in priority order - supports unlimited models"""
    try:
        models = st.secrets.get("MODELS", {})
        model_list = []
        
        # Dynamic loading - supports any number of models (model1, model2, model3, etc.)
        i = 1
        while f"model{i}" in models:
            model_name = models[f"model{i}"].strip()
            if model_name:  # Only add non-empty model names
                model_list.append(model_name)
            i += 1
            
        # Return the list or fallback to a reliable default
        return model_list if model_list else ["google/gemma-2-9b-it:free"]
        
    except Exception as e:
        # Robust fallback if secrets aren't available (local dev, etc.)
        st.warning(f"Could not load models from secrets: {e}. Using default.")
        return ["google/gemma-2-9b-it:free"]


# Initialize models from secrets
MODELS = get_available_models()
PRIMARY_MODEL = MODELS[0] if MODELS else "google/gemma-2-9b-it:free"


def create_message_hash(message, context):
    """Create a hash for message caching"""
    return hashlib.md5(f"{message.strip().lower()}{context}".encode()).hexdigest()


def make_ai_request(messages, temperature=0.7, max_tokens=500):
    """Make AI request with unlimited model fallback system"""
    # Get API key from secrets
    try:
        openrouter_api_key = st.secrets["openrouter"]["api_key"]
    except KeyError:
        return {"error": "OpenRouter API Key not found in secrets", "success": False}
    
    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "Content-Type": "application/json"
    }
    
    # Get fresh model list from secrets (allows real-time updates)
    current_models = get_available_models()
    
    # Try each model in order until one works
    last_error = None
    models_tried = []
    
    for model in current_models:
        models_tried.append(model)
        try:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            response = requests.post(API_URL, headers=headers, json=payload, timeout=25)
            response.raise_for_status()  # Raise exception for bad status codes
            response_json = response.json()
            
            if "choices" in response_json and len(response_json["choices"]) > 0:
                return {
                    "response": response_json["choices"][0]["message"]["content"].strip(),
                    "model_used": model,
                    "models_tried": models_tried,
                    "success": True
                }
            else:
                last_error = f"Model {model} returned no choices"
                continue
                
        except requests.exceptions.Timeout:
            last_error = f"Model {model} timed out (25s)"
            continue
        except requests.exceptions.HTTPError as e:
            last_error = f"Model {model} HTTP error: {e.response.status_code}"
            continue
        except requests.exceptions.ConnectionError:
            last_error = f"Model {model} connection failed"
            continue
        except Exception as e:
            last_error = f"Model {model} failed: {str(e)[:100]}"
            continue
    
    # All models failed - provide detailed error for debugging
    return {
        "error": f"All {len(models_tried)} models failed. Models tried: {', '.join(models_tried)}. Last error: {last_error}",
        "models_tried": models_tried,
        "success": False
    }


def get_enhanced_system_prompt(contact_name, context, message, history):
    """Build relationship-aware prompts with conversation memory"""
    base_prompt = f"You are a compassionate relationship guide helping with a {context} relationship with {contact_name}."
    
    if not history or len(history) < 2:
        return base_prompt + " This is an early conversation, so focus on building understanding."
    
    # Add relationship context
    patterns = analyze_conversation_patterns(history)
    themes = identify_recurring_themes(history)
    
    relationship_context = f"""
RELATIONSHIP INSIGHTS:
- Conversation patterns: {patterns}
- Recurring themes: {themes}
- Total conversations: {len(history)}

Consider this relationship history when providing guidance. Reference patterns where helpful, but don't overwhelm with past details."""
    
    return base_prompt + relationship_context


def analyze_conversation_patterns(history):
    """Identify patterns in conversation history for smarter AI responses"""
    if not history or len(history) < 3:
        return "Limited history available"
    
    # Analyze healing score trends
    recent_scores = [msg.get('healing_score', 0) for msg in history[-5:] if msg.get('healing_score')]
    if recent_scores:
        avg_score = sum(recent_scores) / len(recent_scores)
        trend = "improving" if len(recent_scores) > 1 and recent_scores[-1] > recent_scores[0] else "stable"
        return f"Healing trend: {trend} (avg: {avg_score:.1f}/10)"
    
    return "Building relationship understanding..."


def identify_recurring_themes(history):
    """Find recurring issues and communication patterns"""
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


def interpret_message(contact_name, message, context, relationship_history=None):
    """
    Reveals emotional subtext and healing opportunities
    This is our secret weapon - showing what people REALLY mean
    """
    # Build relationship context from history
    relationship_context = ""
    if relationship_history:
        recent_messages = relationship_history[-5:]  # Last 5 interactions
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

    # Make AI request with fallback
    ai_result = make_ai_request([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Analyze this message: {message}"}
    ], temperature=0.6, max_tokens=400)
    
    if not ai_result["success"]:
        return ai_result
    
    interpretation = ai_result["response"]
    
    # Calculate interpretation score (how revealing/useful)
    interpretation_score = 5
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
        "model": ai_result["model_used"],
        "success": True
    }


def process_ai_transformation(contact_name, message, context, history):
    """
    Core AI transformation engine - turns pain into healing
    The soul of The Third Voice
    """
    # Determine message type
    is_incoming = any(indicator in message.lower() for indicator in ["said:", "wrote:", "texted:", "told me:"])
    mode = "translate" if is_incoming else "coach"
    
    # Enhanced prompts with relationship memory
    system_prompt = get_enhanced_system_prompt(contact_name, context, message, history)
    
    if is_incoming:
        system_prompt += " Understand what they mean and suggest a loving response."
    else:
        system_prompt += " Reframe their message to be constructive and loving."
    
    system_prompt += " Keep it concise, insightful, and actionable (2-3 paragraphs)."
    
    # Make AI request with fallback
    ai_result = make_ai_request([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message}
    ], temperature=0.7, max_tokens=500)
    
    if not ai_result["success"]:
        return ai_result
    
    ai_response_text = ai_result["response"]
    
    # Enhanced healing score calculation
    healing_score = calculate_healing_score(ai_response_text, history)
    
    return {
        "response": ai_response_text,
        "healing_score": healing_score,
        "model": ai_result["model_used"],
        "sentiment": "neutral",
        "emotional_state": "calm",
        "mode": mode,
        "success": True
    }


def calculate_healing_score(ai_response_text, history):
    """Calculate how much healing potential this response has"""
    healing_score = 5  # Base score
    
    # Length bonus (more thoughtful responses)
    if len(ai_response_text) > 200:
        healing_score += 1
    
    # Healing keywords bonus
    healing_words = ["understand", "love", "connect", "care", "heal", "listen", "feel", "safe", "trust"]
    healing_score += min(2, sum(1 for word in healing_words if word in ai_response_text.lower()))
    
    # Relationship memory usage bonus
    if history and any(keyword in ai_response_text.lower() for keyword in ["pattern", "before", "previously", "remember"]):
        healing_score += 1
    
    # Actionable guidance bonus
    if any(action in ai_response_text.lower() for action in ["try", "could", "might", "consider", "suggest"]):
        healing_score += 1
    
    return min(10, healing_score)


def calculate_relationship_health_score(history):
    """Calculate overall relationship health based on conversation history"""
    if not history:
        return 0, "No data yet"
    
    # Get healing scores from last 10 conversations
    recent_scores = [msg.get('healing_score', 0) for msg in history[-10:] if msg.get('healing_score')]
    
    if not recent_scores:
        return 0, "No scored conversations yet"
    
    avg_score = sum(recent_scores) / len(recent_scores)
    
    # Determine health status
    if avg_score >= 8:
        status = "Thriving - Excellent communication patterns"
    elif avg_score >= 6:
        status = "Growing - Good progress with room to improve"
    elif avg_score >= 4:
        status = "Healing - Working through challenges together"
    else:
        status = "Struggling - Focus on understanding and patience"
    
    return round(avg_score, 1), status


def get_healing_insights(history):
    """Generate insights about healing progress"""
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


def get_ai_cache_key(contact_id, message, context):
    """Generate cache key for AI responses"""
    message_hash = create_message_hash(message, context)
    return f"{contact_id}_{message_hash}"


def get_model_status_info():
    """Get current model configuration for debugging/display"""
    models = get_available_models()
    return {
        "total_models": len(models),
        "primary_model": models[0] if models else "None",
        "all_models": models,
        "fallback_enabled": len(models) > 1
    }


# === EXPORT FUNCTIONS FOR MAIN APP ===
__all__ = [
    'interpret_message',
    'process_ai_transformation', 
    'calculate_relationship_health_score',
    'get_healing_insights',
    'create_message_hash',
    'get_ai_cache_key',
    'get_model_status_info',
    'PRIMARY_MODEL',
    'MODELS'
]
