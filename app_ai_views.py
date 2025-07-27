# app_ai_views.py - The Healing Intelligence
import streamlit as st
import requests
from datetime import datetime, timezone
from core_auth_module import (
    CONTEXTS, make_robust_ai_request, get_current_user_id, 
    supabase, create_message_hash, save_message
)

# --- Emotional Interpretation Engine ---
def interpret_message(contact_name, message, context, relationship_history=None):
    """Reveal emotional truth beneath the words - our secret weapon"""
    openrouter_api_key = st.secrets.get("openrouter", {}).get("api_key")
    if not openrouter_api_key:
        return {"error": "OpenRouter API Key not found"}
    
    # Build context from relationship history
    relationship_context = ""
    if relationship_history:
        recent_messages = relationship_history[-5:]
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
            "model": "google/gemma-2-9b-it:free",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this message: {message}"}
            ],
            "temperature": 0.6,
            "max_tokens": 400
        }
        
        # AI request with automatic fallback
        response = make_robust_ai_request(headers, payload, timeout=25)
        response_json = response.json()
        
        if "choices" in response_json and len(response_json["choices"]) > 0:
            interpretation = response_json["choices"][0]["message"]["content"].strip()
            
            # Score interpretation quality
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
                "model": "auto-fallback",
                "success": True
            }
        else:
            return {"error": "No interpretation generated", "success": False}
            
    except Exception as e:
        return {"error": f"Interpretation failed: {str(e)}", "success": False}

def save_interpretation(contact_id, contact_name, original_message, interpretation, interpretation_score, model_used):
    """Preserve emotional insights for learning"""
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
        st.warning(f"Could not save interpretation: {e}")
        return False

# --- Relationship Memory System ---
def analyze_conversation_patterns(history):
    """Identify healing patterns in conversation history"""
    if not history or len(history) < 3:
        return "Limited history available"
    
    recent_scores = [msg.get('healing_score', 0) for msg in history[-5:] if msg.get('healing_score')]
    if recent_scores:
        avg_score = sum(recent_scores) / len(recent_scores)
        trend = "improving" if len(recent_scores) > 1 and recent_scores[-1] > recent_scores[0] else "stable"
        return f"Healing trend: {trend} (avg: {avg_score:.1f}/10)"
    
    return "Building relationship understanding..."

def identify_recurring_themes(history):
    """Detect relationship patterns through conversation"""
    if not history or len(history) < 2:
        return "New relationship - learning patterns"
    
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
    """Create relationship-aware prompts with memory"""
    base_prompt = f"You are a compassionate relationship guide helping with a {context} relationship with {contact_name}."
    
    if not history or len(history) < 2:
        return base_prompt + " This is an early conversation, so focus on building understanding."
    
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
    """Measure relationship health through conversations"""
    if not history:
        return 0, "No data yet"
    
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
    """Generate personalized healing insights"""
    if not history or len(history) < 3:
        return ["🌱 You're just getting started! Every conversation is a step toward healing."]
    
    insights = []
    scores = [msg.get('healing_score', 0) for msg in history if msg.get('healing_score')]
    
    # Score trend analysis
    if len(scores) >= 5:
        recent_avg = sum(scores[-5:]) / 5
        
        if len(scores) >= 10:
            older_avg = sum(scores[-10:-5]) / 5
        else:
            older_scores = scores[:-5]
            older_avg = sum(older_scores) / len(older_scores) if older_scores else recent_avg
        
        if recent_avg > older_avg + 0.5:
            insights.append("📈 Your communication is improving! Recent conversations show higher healing scores.")
        elif recent_avg < older_avg - 0.5:
            insights.append("💪 Having some challenges lately? That's normal - healing isn't always linear.")
    
    # Celebrate high scores
    high_scores = [score for score in scores if score >= 8]
    if len(high_scores) >= 3:
        insights.append(f"🌟 Amazing! You've had {len(high_scores)} conversations with healing scores of 8+!")
    
    # Consistency insights  
    if len(scores) >= 7:
        consistency = len([s for s in scores[-7:] if s >= 6]) / 7
        if consistency >= 0.7:
            insights.append("🎯 You're building consistent healthy communication patterns!")
    
    # Encourage during struggles
    if scores and max(scores[-5:]) < 6:
        insights.append("🤗 Remember: every family faces challenges. You're here working on it - that matters.")
    
    return insights if insights else ["💙 Keep going - healing happens one conversation at a time."]

# --- Healing Interface Components ---
def render_interpret_section(contact_name, message, context, history):
    """Interpretation UI - reveal emotional truth"""
    if st.button("🔍 Interpret - What do they really mean?", key="interpret_btn", help="Reveal emotional subtext and healing opportunities"):
        with st.spinner("🧠 Analyzing emotional subtext..."):
            result = interpret_message(contact_name, message, context, history)
            
            if result.get("success"):
                st.session_state[f"last_interpretation_{contact_name}"] = {
                    "interpretation": result["interpretation"],
                    "score": result["interpretation_score"],
                    "timestamp": datetime.now().timestamp(),
                    "original_message": message
                }
                
                # Save to database
                contact_data = st.session_state.contacts.get(contact_name, {})
                contact_id = contact_data.get("id")
                if contact_id:
                    save_interpretation(contact_id, contact_name, message, result["interpretation"], result["interpretation_score"], result["model"])
                
                st.rerun()
            else:
                st.error(f"Could not analyze message: {result.get('error', 'Unknown error')}")

def display_interpretation_result(contact_name):
    """Show emotional analysis results"""
    interp_key = f"last_interpretation_{contact_name}"
    if interp_key in st.session_state:
        interp_data = st.session_state[interp_key]
        
        # Show if recent (within 10 minutes)
        if datetime.now().timestamp() - interp_data["timestamp"] < 600:
            with st.expander("🔍 **Emotional Analysis - What They Really Mean**", expanded=True):
                st.markdown(interp_data["interpretation"])
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    score = interp_data["score"]
                    if score >= 8:
                        st.success(f"✨ Deep Insight Score: {score}/10 - Very revealing analysis")
                    elif score >= 6:
                        st.info(f"💡 Insight Score: {score}/10 - Good understanding")
                    else:
                        st.warning(f"🔍 Insight Score: {score}/10 - Basic analysis")
                
                with col2:
                    if st.button("📋 Copy", key="copy_interpretation"):
                        st.info("Click and drag to select the analysis above, then Ctrl+C to copy")
        else:
            # Clear old interpretation
            del st.session_state[interp_key]

def display_relationship_progress(contact_name, history):
    """Visualize healing journey progress"""
    if not history:
        return
    
    with st.expander("📊 **Relationship Healing Progress**", expanded=False):
        health_score, status = calculate_relationship_health_score(history)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Relationship Health", f"{health_score}/10", help="Based on recent healing scores")
        with col2:
            st.metric("Total Conversations", len(history))
        
        st.markdown(f"**Status:** {status}")
        
        # Healing insights
        insights = get_healing_insights(history)
        st.markdown("**💙 Your Healing Journey:**")
        for insight in insights:
            st.markdown(f"• {insight}")
        
        # Recent trend visualization
        if len(history) >= 5:
            recent_scores = [msg.get('healing_score', 0) for msg in history[-5:] if msg.get('healing_score')]
            if recent_scores:
                trend_text = " → ".join([str(score) for score in recent_scores])
                st.markdown(f"**Recent Healing Scores:** {trend_text}")

# --- Core Message Processing ---
def process_message(contact_name, message, context):
    """Transform messages into healing opportunities"""
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
    history = contact_data.get("history", [])
    
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
            # Generate new healing response
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
                    "model": "google/gemma-2-9b-it:free",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 500
                }
                
                # AI request with automatic fallback
                response = make_robust_ai_request(headers, payload, timeout=25)
                response_json = response.json()
                
                if "choices" in response_json and len(response_json["choices"]) > 0:
                    ai_response_text = response_json["choices"][0]["message"]["content"].strip()
                    ai_sentiment = "neutral"
                    ai_emotional_state = "calm"
                    
                    # Healing score calculation
                    healing_score = 5 + (1 if len(ai_response_text) > 200 else 0)
                    healing_score += min(2, sum(1 for word in ["understand", "love", "connect", "care", "heal"] if word in ai_response_text.lower()))
                    
                    # Bonus for relationship memory usage
                    if history and any(keyword in ai_response_text.lower() for keyword in ["pattern", "before", "previously", "remember"]):
                        healing_score += 1
                    
                    healing_score = min(10, healing_score)
                    
                    # Cache the healing response
                    try:
                        cache_data = {
                            "contact_id": contact_id,
                            "message_hash": message_hash,
                            "context": context,
                            "response": ai_response_text,
                            "healing_score": healing_score,
                            "model": "auto-fallback",
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
        
        # Save the AI healing response
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
        st.session_state.last_error_message = f"Request failed: {str(e)}"

# --- Conversation Healing Interface ---
def render_conversation_view():
    """Sacred space for family healing conversations"""
    if not st.session_state.active_contact:
        st.session_state.app_mode = "contacts_list"
        st.rerun()
        return
    
    contact_name = st.session_state.active_contact
    contact_data = st.session_state.contacts.get(contact_name, {"context": "family", "history": [], "id": None})
    context = contact_data["context"]
    history = contact_data["history"]
    contact_id = contact_data.get("id")
    
    st.markdown(f"### {CONTEXTS[context]['icon']} {contact_name} - {CONTEXTS[context]['description']}")
    
    # Navigation - Healing Journey Controls
    back_col, edit_col, _ = st.columns([2, 2, 6])
    with back_col:
        if st.button("← Back", key="back_btn", use_container_width=True):
            st.session_state.app_mode = "contacts_list"
            st.session_state.active_contact = None
            st.session_state.last_error_message = None
            st.session_state.clear_conversation_input = False
            st.rerun()
    
    with edit_col:
        if st.button("✏️ Edit", key="edit_current_contact", use_container_width=True):
            st.session_state.edit_contact = {
                "id": contact_id,
                "name": contact_name,
                "context": context
            }
            st.session_state.app_mode = "edit_contact_view"
            st.rerun()
    
    # Relationship Health Dashboard
    display_relationship_progress(contact_name, history)
    
    st.markdown("---")
    
    # Input Section - Where Healing Begins
    st.markdown("#### 💭 Your Input")
    st.markdown("*Share what happened - their message or your response that needs guidance*")
    
    input_value = "" if st.session_state.clear_conversation_input else st.session_state.get("conversation_input_text", "")
    st.text_area(
        "What's happening?",
        value=input_value,
        key="conversation_input_text",
        placeholder="Examples:\n• They said: 'You never listen to me!'\n• I want to tell them: 'I'm frustrated with your attitude'\n• We had a fight about...",
        height=120
    )
    
    if st.session_state.clear_conversation_input:
        st.session_state.clear_conversation_input = False
    
    # Action Buttons - Healing Tools
    current_message = st.session_state.conversation_input_text
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        if st.button("✨ Transform with Love", key="transform_message", use_container_width=True):
            process_message(contact_name, current_message, context)
    
    with col2:
        if current_message.strip():
            render_interpret_section(contact_name, current_message, context, history)
        else:
            st.button("🔍 Interpret", disabled=True, help="Enter a message first", use_container_width=True)
    
    with col3:
        if st.button("🗑️ Clear", key="clear_input_btn", use_container_width=True):
            st.session_state.conversation_input_text = ""
            st.session_state.clear_conversation_input = False
            st.session_state.last_error_message = None
            st.rerun()
    
    # Error display
    if st.session_state.last_error_message:
        st.error(st.session_state.last_error_message)
    
    # Emotional Truth Revealed
    display_interpretation_result(contact_name)
    
    st.markdown("---")
    
    # Third Voice Guidance
    st.markdown("#### 🤖 The Third Voice Guidance")
    last_response_key = f"last_response_{contact_name}"
    
    if last_response_key in st.session_state and st.session_state[last_response_key]:
        last_resp = st.session_state[last_response_key]
        
        # Show response if recent
        if datetime.now().timestamp() - last_resp["timestamp"] < 300:
            with st.container():
                st.markdown("**Your AI Guidance:**")
                st.text_area(
                    "AI Guidance Output",
                    value=last_resp['response'],
                    height=200,
                    key="ai_response_display",
                    help="Click inside and Ctrl+A to select all, then Ctrl+C to copy",
                    disabled=False,
                    label_visibility="hidden"
                )
                
                col_score, col_model, col_copy = st.columns([2, 2, 1])
                with col_score:
                    if last_resp["healing_score"] >= 8:
                        st.success(f"✨ Healing Score: {last_resp['healing_score']}/10")
                    elif last_resp["healing_score"] >= 6:
                        st.info(f"💡 Healing Score: {last_resp['healing_score']}/10")
                    else:
                        st.warning(f"🔧 Healing Score: {last_resp['healing_score']}/10")
                
                with col_model:
                    st.caption(f"🤖 Model: Robust AI (auto-fallback)")
                
                with col_copy:
                    if st.button("📋", help="Click text area above and Ctrl+A to select all", key="copy_hint"):
                        st.info("💡 Click in text area above, then Ctrl+A and Ctrl+C to copy")
                
                if last_resp["healing_score"] >= 8:
                    st.balloons()
                    st.markdown("🌟 **High healing potential!** This guidance can really help transform your relationship.")
        else:
            del st.session_state[last_response_key]
            st.info("💭 Your Third Voice guidance will appear here after you click Transform")
    else:
        st.info("💭 Your Third Voice guidance will appear here after you click Transform")
        
        # Guidance for new conversations
        if not history:
            st.markdown("""
            **💡 How it works:**
            - Share what they said or what you want to say
            - Get compassionate guidance that heals instead of hurts
            - **🆕 Use "Interpret" to reveal what they really mean beneath their words**
            - Build stronger relationships through understanding
            """)
    
    st.markdown("---")
    
    # Conversation History - Healing Journey Archive
    st.markdown("#### 📜 Conversation History")
    
    if history:
        st.markdown(f"**Recent Messages** ({len(history)} total healing conversations)")
        
        # Show last 3 messages
        for msg in reversed(history[-3:]):
            with st.container():
                col_time, col_score = st.columns([3, 1])
                with col_time:
                    st.markdown(f"**{msg['time']}** • {msg['type'].title()}")
                with col_score:
                    score_color = "🟢" if msg['healing_score'] >= 8 else "🟡" if msg['healing_score'] >= 6 else "🔴"
                    st.markdown(f"{score_color} {msg['healing_score']}/10")
                
                st.markdown("**Your Message:**")
                st.info(msg['original'])
                
                if msg['result']:
                    st.markdown("**Third Voice Guidance:**")
                    st.text_area(
                        "Historical AI Guidance",
                        value=msg['result'],
                        height=100,
                        key=f"history_response_{msg['id']}",
                        disabled=True,
                        label_visibility="hidden"
                    )
                
                st.markdown("---")
        
        # Full history expander
        if len(history) > 3:
            with st.expander(f"📚 View All {len(history)} Conversations", expanded=False):
                for msg in reversed(history):
                    st.markdown(f"""
                    **{msg['time']}** | **{msg['type'].title()}** | Score: {msg['healing_score']}/10
                    """)
                    
                    with st.container():
                        st.markdown("**Your Message:**")
                        st.info(msg['original'])
                    
                    if msg['result']:
                        with st.container():
                            st.markdown("**Third Voice Guidance:**")
                            st.text_area(
                                "Full History AI Guidance",
                                value=msg['result'],
                                height=100,
                                key=f"full_history_response_{msg['id']}",
                                disabled=True,
                                label_visibility="hidden"
                            )
                            st.caption(f"🤖 Model: Robust AI")
                    
                    st.markdown("---")
    else:
        st.info("📝 No conversation history yet. Share what's happening above to get your first Third Voice guidance!")
    
    # Feedback for continuous healing improvement
    from core_auth_module import show_feedback_widget
    show_feedback_widget(f"conversation_{contact_name}")
