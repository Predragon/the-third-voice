# ai_analysis.py
# The Third Voice AI - Emotional Intelligence Engine
# "When both people are speaking from pain, someone must be the third voice."
# Built with love by Predrag Mirkovic, fighting to return to his daughter Samantha

import streamlit as st
import requests
from datetime import datetime, timezone
# CORRECT imports in ai_analysis.py (after my fix):
from ai_engine import make_robust_ai_request
from auth_backend import get_current_user_id, supabase

from ai_engine import make_robust_ai_request
from auth_backend import get_current_user_id, supabase
# --- PHASE 2: INTERPRETATION & RELATIONSHIP MEMORY FUNCTIONS ---

def interpret_message(contact_name, message, context, relationship_history=None):
    """
    Reveals emotional subtext and healing opportunities
    This is our secret weapon - showing what people REALLY mean
    
    Every interpretation prevents a family breakdown.
    Every insight brings healing where there was pain.
    """
    openrouter_api_key = st.secrets.get("openrouter", {}).get("api_key")
    if not openrouter_api_key:
        return {"error": "OpenRouter API Key not found"}
    
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

    try:
        headers = {
            "Authorization": f"Bearer {openrouter_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "google/gemma-2-9b-it:free",  # This will be automatically replaced by robust request
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this message: {message}"}
            ],
            "temperature": 0.6,
            "max_tokens": 400
        }
        
        # Use robust AI request with automatic fallback
        response = make_robust_ai_request(headers, payload, timeout=25)
        response_json = response.json()
        
        if "choices" in response_json and len(response_json["choices"]) > 0:
            interpretation = response_json["choices"][0]["message"]["content"].strip()
            
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
                "model": "auto-fallback",  # Don't expose which model was used
                "success": True
            }
        else:
            return {"error": "No interpretation generated", "success": False}
            
    except Exception as e:
        return {"error": f"Interpretation failed: {str(e)}", "success": False}

def save_interpretation(contact_id, contact_name, original_message, interpretation, interpretation_score, model_used):
    """
    Save interpretation to database for learning and improvement
    Every saved interpretation helps us understand families better
    """
    user_id = get_current_user_id()
    if not user_id:
        return False
    
    try:
        interpretation_data = {
            "contact_id": contact_id,
            "contact_name": contact_name,
            "original_message": original_message,
            "interpretation": interpretation,
            "interpretation_score": interpretation_score,
            "model": model_used,
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        response = supabase.table("interpretations").insert(interpretation_data).execute()
        return bool(response.data)
        
    except Exception as e:
        # For now, don't block if table doesn't exist yet
        st.warning(f"Could not save interpretation: {e}")
        return False

def analyze_conversation_patterns(history):
    """
    Identify patterns in conversation history for smarter AI responses
    
    Learning from every interaction to prevent future pain.
    Every pattern we catch is a family breakdown we prevent.
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

def identify_recurring_themes(history):
    """
    Find recurring issues and communication patterns
    
    Spotting the cycles that break families apart,
    so we can break the cycles instead.
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

def get_enhanced_system_prompt(contact_name, context, message, history):
    """
    Build relationship-aware prompts with conversation memory
    
    Every prompt carries the wisdom of past conversations,
    turning pain into healing guidance.
    """
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

def calculate_relationship_health_score(history):
    """
    Calculate overall relationship health based on conversation history
    
    Every score point represents hope.
    Every improvement is a family saved.
    """
    if not history:
        return 0, "No data yet"
    
    # Get healing scores from last 10 conversations
    recent_scores = [msg.get('healing_score', 0) for msg in history[-10:] if msg.get('healing_score')]
    
    if not recent_scores:
        return 0, "No scored conversations yet"
    
    avg_score = sum(recent_scores) / len(recent_scores)
    
    # Determine health status with hope and encouragement
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
    """
    Generate insights about healing progress
    
    Every insight is hope delivered.
    Every celebration prevents despair.
    """
    if not history or len(history) < 3:
        return ["🌱 You're just getting started! Every conversation is a step toward healing."]
    
    insights = []
    
    # Score trend analysis
    scores = [msg.get('healing_score', 0) for msg in history if msg.get('healing_score')]
    if len(scores) >= 5:
        recent_avg = sum(scores[-5:]) / 5
        
        # Fix the division by zero error
        if len(scores) >= 10:
            older_avg = sum(scores[-10:-5]) / 5
        else:
            # For scores between 5-9, compare with earlier available scores
            older_scores = scores[:-5]
            older_avg = sum(older_scores) / len(older_scores) if older_scores else recent_avg
        
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

def process_message(contact_name, message, context):
    """
    Enhanced message processing with relationship memory
    
    This is where pain transforms into healing.
    Where angry words become loving understanding.
    Every processed message is a family saved.
    """
    from auth_backend import create_message_hash, save_message
    
    st.session_state.last_error_message = None
    
    if not message.strip():
        st.session_state.last_error_message = "Input message cannot be empty. Please type something to transform."
        return
    
    # Get contact info
    contact_data = st.session_state.contacts.get(contact_name)
    if not contact_data:
        st.session_state.last_error_message = "Contact not found."
        return
    
    contact_id = contact_data["id"]
    history = contact_data.get("history", [])  # Get history for context
    
    openrouter_api_key = st.secrets.get("openrouter", {}).get("api_key")
    if not openrouter_api_key:
        st.session_state.last_error_message = "OpenRouter API Key not found in Streamlit secrets under [openrouter]. Please add it."
        return
    
    # Determine message type
    is_incoming = any(indicator in message.lower() for indicator in ["said:", "wrote:", "texted:", "told me:"])
    mode = "translate" if is_incoming else "coach"
    
    # Check cache first
    message_hash = create_message_hash(message, context)
    user_id = get_current_user_id()
    
    try:
        cache_response = supabase.table("ai_response_cache").select("*").eq("contact_id", contact_id).eq("message_hash", message_hash).eq("user_id", user_id).gte("expires_at", datetime.now(timezone.utc).isoformat()).execute()
        
        if cache_response.data:
            # Use cached response
            cached = cache_response.data[0]
            ai_response_text = cached["response"]
            healing_score = cached["healing_score"]
            ai_sentiment = cached["sentiment"]
            ai_emotional_state = cached["emotional_state"]
            
            st.info("Using cached response for faster processing")
        else:
            # Generate new response with enhanced prompts
            system_prompt = get_enhanced_system_prompt(contact_name, context, message, history)
            
            if is_incoming:
                system_prompt += " Understand what they mean and suggest a loving response."
            else:
                system_prompt += " Reframe their message to be constructive and loving."
            
            system_prompt += " Keep it concise, insightful, and actionable (2-3 paragraphs)."
            
            with st.spinner("🤖 Processing with relationship insights..."):
                headers = {
                    "Authorization": f"Bearer {openrouter_api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "google/gemma-2-9b-it:free",  # This will be automatically replaced by robust request
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 500
                }
                
                # Use robust AI request with automatic fallback
                response = make_robust_ai_request(headers, payload, timeout=25)
                response_json = response.json()
                
                if "choices" in response_json and len(response_json["choices"]) > 0:
                    ai_response_text = response_json["choices"][0]["message"]["content"].strip()
                    ai_sentiment = "neutral"
                    ai_emotional_state = "calm"
                    
                    # Enhanced healing score calculation
                    healing_score = 5 + (1 if len(ai_response_text) > 200 else 0)
                    healing_score += min(2, sum(1 for word in ["understand", "love", "connect", "care", "heal"] if word in ai_response_text.lower()))
                    
                    # Bonus for relationship memory usage
                    if history and any(keyword in ai_response_text.lower() for keyword in ["pattern", "before", "previously", "remember"]):
                        healing_score += 1
                    
                    healing_score = min(10, healing_score)
                    
                    # Cache the response
                    try:
                        cache_data = {
                            "contact_id": contact_id,
                            "message_hash": message_hash,
                            "context": context,
                            "response": ai_response_text,
                            "healing_score": healing_score,
                            "model": "auto-fallback",  # Don't expose which model was used
                            "sentiment": ai_sentiment,
                            "emotional_state": ai_emotional_state,
                            "user_id": user_id
                        }
                        supabase.table("ai_response_cache").insert(cache_data).execute()
                    except Exception as cache_error:
                        st.warning(f"Could not cache response: {cache_error}")
                    
                else:
                    st.session_state.last_error_message = f"AI API response missing 'choices': {response_json}"
                    return
        
        # Save the incoming message
        save_message(contact_id, contact_name, "incoming", message, None, "unknown", 0, "N/A")
        
        # Save the AI response
        save_message(contact_id, contact_name, mode, message, ai_response_text, ai_emotional_state, healing_score, "auto-fallback", ai_sentiment)
        
        # Store response for immediate display
        st.session_state[f"last_response_{contact_name}"] = {
            "response": ai_response_text,
            "healing_score": healing_score,
            "timestamp": datetime.now().timestamp(),
            "model": "auto-fallback"
        }
        
        st.session_state.clear_conversation_input = True
        st.rerun()
        
    except Exception as e:
        # All robust request handling is done in make_robust_ai_request
        st.session_state.last_error_message = f"Request failed: {str(e)}"

# --- HEALING ANALYTICS ---

def get_conversation_summary(history):
    """
    Generate a meaningful summary of the relationship journey
    
    Every summary tells a story of growth, 
    of pain transformed into understanding.
    """
    if not history:
        return "No conversations yet - ready to begin healing."
    
    total_conversations = len(history)
    avg_score = sum(msg.get('healing_score', 0) for msg in history) / total_conversations if history else 0
    
    # Find the journey arc
    if total_conversations >= 10:
        early_scores = [msg.get('healing_score', 0) for msg in history[:5]]
        recent_scores = [msg.get('healing_score', 0) for msg in history[-5:]]
        
        early_avg = sum(early_scores) / len(early_scores) if early_scores else 0
        recent_avg = sum(recent_scores) / len(recent_scores) if recent_scores else 0
        
        if recent_avg > early_avg + 1:
            journey = "📈 Remarkable growth - you've transformed this relationship!"
        elif recent_avg > early_avg:
            journey = "🌱 Steady improvement - keep nurturing this growth."
        else:
            journey = "💪 Working through challenges - persistence is key."
    else:
        journey = "🌟 Building foundation - every conversation matters."
    
    return f"{journey} ({total_conversations} conversations, {avg_score:.1f}/10 avg healing)"

def predict_relationship_trajectory(history):
    """
    Predict where this relationship is heading based on patterns
    
    Hope, backed by data.
    Healing, measured and projected.
    """
    if not history or len(history) < 5:
        return "Too early to predict - keep building positive patterns."
    
    recent_scores = [msg.get('healing_score', 0) for msg in history[-5:] if msg.get('healing_score')]
    if not recent_scores:
        return "Need more scored conversations for prediction."
    
    # Simple trend analysis
    if len(recent_scores) >= 3:
        trend = recent_scores[-1] - recent_scores[0]
        recent_avg = sum(recent_scores) / len(recent_scores)
        
        if trend > 1 and recent_avg >= 7:
            return "🚀 Trajectory: THRIVING - This relationship is on an excellent path!"
        elif trend > 0 and recent_avg >= 6:
            return "📈 Trajectory: IMPROVING - Strong positive momentum building."
        elif recent_avg >= 6:
            return "✨ Trajectory: STABLE & HEALTHY - Maintaining good communication."
        elif trend > 0:
            return "🌱 Trajectory: HEALING - Progress visible, keep going!"
        else:
            return "💪 Trajectory: CHALLENGING - Focus on understanding and patience."
    
    return "Building understanding of your communication patterns..."

# End of ai_analysis.py
# Every function here serves love.
# Every algorithm fights for families.
# Every line of code brings Predrag closer to Samantha.
