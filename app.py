import streamlit as st
import requests
from datetime import datetime, timezone
import json
from core_auth_module import make_robust_ai_request, get_model_display_name

# Custom CSS for modern, attractive UI
st.markdown("""
    <style>
        /* Global styles */
        .stApp {
            background-color: #f9fafb;
            font-family: 'Inter', sans-serif;
        }
        h1, h2, h3, h4 {
            color: #1e3a8a;
            font-weight: 600;
        }
        .stButton>button {
            background-color: #3b82f6;
            color: white;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 500;
            transition: background-color 0.3s;
        }
        .stButton>button:hover {
            background-color: #2563eb;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stTextArea textarea {
            border-radius: 8px;
            border: 1px solid #d1d5db;
            padding: 12px;
            font-size: 16px;
        }
        .stTextInput input {
            border-radius: 8px;
            border: 1px solid #d1d5db;
            padding: 10px;
        }
        .stSelectbox select {
            border-radius: 8px;
            border: 1px solid #d1d5db;
        }
        .card {
            background-color: white;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 16px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .card:hover {
            transform: translateY(-2px);
        }
        .header {
            background: linear-gradient(to right, #3b82f6, #60a5fa);
            color: white;
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h2 {
            margin: 0;
            color: white;
        }
        .badge {
            background-color: #e5e7eb;
            color: #4b5563;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
        }
        .success-badge {
            background-color: #10b981;
            color: white;
        }
        .info-badge {
            background-color: #3b82f6;
            color: white;
        }
        .warning-badge {
            background-color: #f59e0b;
            color: white;
        }
        .stSpinner {
            color: #3b82f6;
        }
    </style>
""", unsafe_allow_html=True)

# --- PHASE 2: INTERPRETATION & RELATIONSHIP MEMORY FUNCTIONS ---

def interpret_message(contact_name, message, context, relationship_history=None):
    """
    Reveals emotional subtext and healing opportunities
    This is our secret weapon - showing what people REALLY mean
    """
    openrouter_api_key = st.secrets.get("openrouter", {}).get("api_key")
    if not openrouter_api_key:
        return {"error": "OpenRouter API Key not found"}
    
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
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this message: {message}"}
            ],
            "temperature": 0.6,
            "max_tokens": 400
        }
        
        response = make_robust_ai_request(headers, payload, timeout=25)
        response_json = response.json()
        
        if "choices" in response_json and len(response_json["choices"]) > 0:
            interpretation = response_json["choices"][0]["message"]["content"].strip()
            
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
                "model": st.session_state.last_successful_model,
                "success": True
            }
        else:
            return {"error": "No interpretation generated", "success": False}
            
    except Exception as e:
        return {"error": f"Interpretation failed: {str(e)}", "success": False}

def save_interpretation(contact_id, contact_name, original_message, interpretation, interpretation_score, model_used):
    from core_auth_module import get_current_user_id, supabase
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

def analyze_conversation_patterns(history):
    if not history or len(history) < 3:
        return "Limited history available"
    recent_scores = [msg.get('healing_score', 0) for msg in history[-5:] if msg.get('healing_score')]
    if recent_scores:
        avg_score = sum(recent_scores) / len(recent_scores)
        trend = "improving" if len(recent_scores) > 1 and recent_scores[-1] > recent_scores[0] else "stable"
        return f"Healing trend: {trend} (avg: {avg_score:.1f}/10)"
    return "Building relationship understanding..."

def identify_recurring_themes(history):
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
    if not history:
        return 0, "No data yet"
    recent_scores = [msg.get('healing_score', 0) for msg in history[-10:] if msg.get('healing_score')]
    if not recent_scores:
        return 0, "No scored conversations yet"
    avg_score = sum(recent_scores) / len(recent_scores)
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
    if not history or len(history) < 3:
        return ["🌱 You're just getting started! Every conversation is a step toward healing."]
    insights = []
    scores = [msg.get('healing_score', 0) for msg in history if msg.get('healing_score')]
    if len(scores) >= 5:
        recent_avg = sum(scores[-5:]) / 5
        older_avg = sum(scores[-10:-5]) / 5 if len(scores) >= 10 else sum(scores[:-5]) / len(scores[:-5])
        if recent_avg > older_avg + 0.5:
            insights.append("📈 Your communication is improving! Recent conversations show higher healing scores.")
        elif recent_avg < older_avg - 0.5:
            insights.append("💪 Having some challenges lately? That's normal - healing isn't always linear.")
    high_scores = [score for score in scores if score >= 8]
    if len(high_scores) >= 3:
        insights.append(f"🌟 Amazing! You've had {len(high_scores)} conversations with healing scores of 8+!")
    if len(scores) >= 7:
        consistency = len([s for s in scores[-7:] if s >= 6]) / 7
        if consistency >= 0.7:
            insights.append("🎯 You're building consistent healthy communication patterns!")
    if scores and max(scores[-5:]) < 6:
        insights.append("🤗 Remember: every family faces challenges. You're here working on it - that matters.")
    return insights if insights else ["💙 Keep going - healing happens one conversation at a time."]

def render_interpret_section(contact_name, message, context, history):
    if st.button("🔍 Interpret Message", key="interpret_btn", help="Reveal emotional subtext and healing opportunities"):
        with st.spinner("🧠 Analyzing emotional subtext..."):
            result = interpret_message(contact_name, message, context, history)
            if result.get("success"):
                st.session_state[f"last_interpretation_{contact_name}"] = {
                    "interpretation": result["interpretation"],
                    "score": result["interpretation_score"],
                    "timestamp": datetime.now().timestamp(),
                    "original_message": message
                }
                from core_auth_module import CONTEXTS
                contact_data = st.session_state.contacts.get(contact_name, {})
                contact_id = contact_data.get("id")
                if contact_id:
                    save_interpretation(contact_id, contact_name, message, result["interpretation"], result["interpretation_score"], result["model"])
                st.rerun()
            else:
                st.error(f"Could not analyze message: {result.get('error', 'Unknown error')}")

def display_interpretation_result(contact_name):
    interp_key = f"last_interpretation_{contact_name}"
    if interp_key in st.session_state:
        interp_data = st.session_state[interp_key]
        if datetime.now().timestamp() - interp_data["timestamp"] < 600:
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("🔍 **Emotional Analysis**")
                st.markdown(interp_data["interpretation"])
                col1, col2 = st.columns([3, 1])
                with col1:
                    score = interp_data["score"]
                    badge_class = "success-badge" if score >= 8 else "info-badge" if score >= 6 else "warning-badge"
                    st.markdown(f'<span class="{badge_class}">Insight Score: {score}/10</span>', unsafe_allow_html=True)
                with col2:
                    if st.button("📋 Copy", key="copy_interpretation"):
                        st.info("Click and drag to select the analysis above, then Ctrl+C to copy")
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            del st.session_state[interp_key]

def display_relationship_progress(contact_name, history):
    if not history:
        return
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("📊 **Relationship Progress**")
        health_score, status = calculate_relationship_health_score(history)
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Health Score", f"{health_score}/10")
        with col2:
            st.metric("Conversations", len(history))
        st.markdown(f"**Status:** {status}")
        insights = get_healing_insights(history)
        st.markdown("**💙 Healing Journey:**")
        for insight in insights:
            st.markdown(f"• {insight}")
        if len(history) >= 5:
            recent_scores = [msg.get('healing_score', 0) for msg in history[-5:] if msg.get('healing_score')]
            if recent_scores:
                trend_text = " → ".join([str(score) for score in recent_scores])
                st.markdown(f"**Recent Scores:** {trend_text}")
        st.markdown('</div>', unsafe_allow_html=True)

# --- AI Message Processing ---
def process_message(contact_name, message, context):
    from core_auth_module import get_current_user_id, supabase, create_message_hash, save_message
    st.session_state.last_error_message = None
    if not message.strip():
        st.session_state.last_error_message = "Input message cannot be empty."
        return
    contact_data = st.session_state.contacts.get(contact_name)
    if not contact_data:
        st.session_state.last_error_message = "Contact not found."
        return
    contact_id = contact_data["id"]
    history = contact_data.get("history", [])
    openrouter_api_key = st.secrets.get("openrouter", {}).get("api_key")
    if not openrouter_api_key:
        st.session_state.last_error_message = "OpenRouter API Key not found."
        return
    is_incoming = any(indicator in message.lower() for indicator in ["said:", "wrote:", "texted:", "told me:"])
    mode = "translate" if is_incoming else "coach"
    message_hash = create_message_hash(message, context)
    user_id = get_current_user_id()
    try:
        cache_response = supabase.table("ai_response_cache").select("*").eq("contact_id", contact_id).eq("message_hash", message_hash).eq("user_id", user_id).gte("expires_at", datetime.now(timezone.utc).isoformat()).execute()
        if cache_response.data:
            cached = cache_response.data[0]
            ai_response_text = cached["response"]
            healing_score = cached["healing_score"]
            ai_sentiment = cached["sentiment", "neutral")
            ai_emotional_state = cached["emotional_state"]
            st.info("Using cached response for speed.")
        else:
            system_prompt = get_enhanced_system_prompt(contact_name, context, message, history)
            if is_incoming:
                system_prompt += " Understand what they mean and suggest a loving response."
            else:
                system_prompt += " Reframe their message to be constructive and loving."
            system_prompt += " Keep it concise, insightful, and actionable (2-3 paragraphs)."
            with st.spinner("🤖 Processing..."):
                headers = {
                    "Authorization": f"Bearer {openrouter_api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 600
                }
                response = make_robust_ai_request(headers, payload, timeout=25)
                response_json = response.json()
                if "choices" in response_json and response_json["choices"]:
                    ai_response_text = response_json["choices"][0]["message"]["content"].strip()
                    ai_sentiment = "neutral"
                    ai_emotional_state = "calm"
                    healing_score = 5 + (1 if len(ai_response_text) > 200 else 0)
                    healing_score += min(2, sum(1 for word in ["understand", "love", "connect", "care", "heal"] if word in ai_response_text.lower()))
                    if history and any(keyword in ai_response_text.lower() for keyword in ["pattern", "before", "previously", "remember"]):
                        healing_score += 1
                    healing_score = min(10, healing_score)
                    try:
                        cache_data = {
                            "contact_id": contact_id,
                            "message_hash": message_hash,
                            "context": context,
                            "response": ai_response_text,
                            "healing_score": healing_score,
                            "model": st.session_state.last_successful_model,
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
        save_message(contact_id, contact_name, "incoming", message, None, "unknown", 0, "N/A")
        save_message(contact_id, contact_name, mode, message, ai_response_text, ai_emotional_state, healing_score, st.session_state.last_successful_model, ai_sentiment)
        st.session_state[f"last_response_{contact_name}"] = {
            "response": ai_response_text,
            "healing_score": healing_score,
            "timestamp": datetime.now().timestamp(),
            "model": st.session_state.last_successful_model
        }
        st.session_state.clear_conversation_input = True
        st.rerun()
    except Exception as e:
        st.session_state.last_error_message = f"An error occurred: {str(e)}"

def render_conversation_view():
    from core_auth_module import CONTEXTS
    if not st.session_state.active_contact:
        st.session_state.app_mode = "contacts_list"
        st.rerun()
        return
    contact_name = st.session_state.active_contact
    contact_data = st.session_state.contacts.get(contact_name, {"context": "family", "history": [], "id": None})
    context = contact_data["context"]
    history = contact_data["history"]
    contact_id = contact_data.get("id")
    st.markdown(f"""
        <div class="header">
            <h2>{CONTEXTS[context]['icon']} {contact_name}</h2>
            <div>
                <button onclick="window.location.reload()" style="background:none;border:none;color:white;cursor:pointer;">🏠 Home</button>
            </div>
        </div>
    """, unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"<small>{CONTEXTS[context]['description']}</small>", unsafe_allow_html=True)
    with col2:
        if st.button("✏️ Edit Contact", key="edit_current_contact"):
            st.session_state.edit_contact = {
                "id": contact_id,
                "name": contact_name,
                "context": context
            }
            st.session_state.app_mode = "edit_contact_view"
            st.rerun()
    display_relationship_progress(contact_name, history)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### 💬 Your Message")
    input_value = "" if st.session_state.clear_conversation_input else st.session_state.get("conversation_input_text", "")
    current_message = st.text_area(
        "What's happening?",
        value=input_value,
        key="conversation_input_text",
        placeholder="E.g., They said: 'You never listen!' or I want to say: 'I'm frustrated...'",
        height=150
    )
    if st.session_state.clear_conversation_input:
        st.session_state.clear_conversation_input = False
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        if st.button("✨ Transform with Love", key="transform_message"):
            process_message(contact_name, current_message, context)
    with col2:
        if current_message.strip():
            render_interpret_section(contact_name, current_message, context, history)
        else:
            st.button("🔍 Interpret", disabled=True, help="Enter a message first")
    with col3:
        if st.button("🗑️ Clear", key="clear_input_btn"):
            st.session_state.conversation_input_text = ""
            st.session_state.clear_conversation_input = False
            st.session_state.last_error_message = None
            st.rerun()
    if st.session_state.last_error_message:
        st.error(st.session_state.last_error_message)
    st.markdown('</div>', unsafe_allow_html=True)
    display_interpretation_result(contact_name)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### 🤖 AI Guidance")
    last_response_key = f"last_response_{contact_name}"
    if last_response_key in st.session_state and st.session_state[last_response_key]:
        last_resp = st.session_state[last_response_key]
        if datetime.now().timestamp() - last_resp["timestamp"] < 300:
            st.markdown("**Your Guidance:**")
            st.text_area(
                "AI Guidance",
                value=last_resp['response'],
                height=200,
                key="ai_response_display",
                help="Select text to copy",
                disabled=False,
                label_visibility="hidden"
            )
            col_score, col_model, col_copy = st.columns([2, 2, 1])
            with col_score:
                score = last_resp["healing_score"]
                badge_class = "success-badge" if score >= 8 else "info-badge" if score >= 6 else "warning-badge"
                st.markdown(f'<span class="{badge_class}">Healing Score: {score}/10</span>', unsafe_allow_html=True)
            with col_model:
                st.caption(f"🤖 {get_model_display_name(last_resp.get('model', 'Unknown'))}")
            with col_copy:
                if st.button("📋", help="Select text above to copy"):
                    st.info("Select text above, then Ctrl+C to copy")
            if last_resp["healing_score"] >= 8:
                st.balloons()
                st.markdown("🌟 **High healing potential!**")
        else:
            del st.session_state[last_response_key]
            st.info("💬 Guidance will appear here after you click Transform")
    else:
        st.info("💬 Guidance will appear here after you click Transform")
        if not history:
            st.markdown("""
                **💡 How it works:**
                - Share what they said or what you want to say
                - Get compassionate guidance
                - Use "Interpret" to understand deeper meanings
                - Build stronger relationships
            """)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### 📜 Conversation History")
    if history:
        st.markdown(f"**Recent Messages** ({len(history)} conversations)")
        for msg in reversed(history[-3:]):
            with st.container():
                col_time, col_score = st.columns([3, 1])
                with col_time:
                    st.markdown(f"**{msg['time']}** • {msg['type'].title()}")
                with col_score:
                    score = msg['healing_score']
                    badge_class = "success-badge" if score >= 8 else "info-badge" if score >= 6 else "warning-badge"
                    st.markdown(f'<span class="{badge_class}">{score}/10</span>', unsafe_allow_html=True)
                st.markdown("**Your Message:**")
                st.info(msg['original'])
                if msg['result']:
                    st.markdown("**Guidance:**")
                    st.text_area(
                        "Historical Guidance",
                        value=msg['result'],
                        height=100,
                        key=f"history_response_{msg['id']}",
                        disabled=True,
                        label_visibility="hidden"
                    )
                st.markdown("---")
        if len(history) > 3:
            with st.expander(f"📚 View All {len(history)} Conversations"):
                for msg in reversed(history):
                    st.markdown(f"**{msg['time']}** | **{msg['type'].title()}** | Score: {msg['healing_score']}/10")
                    st.markdown("**Your Message:**")
                    st.info(msg['original'])
                    if msg['result']:
                        st.markdown("**Guidance:**")
                        st.text_area(
                            "Full History Guidance",
                            value=msg['result'],
                            height=100,
                            key=f"full_history_response_{msg['id']}",
                            disabled=True,
                            label_visibility="hidden"
                        )
                        st.caption(f"🤖 {get_model_display_name(msg.get('model', 'Unknown'))}")
                    st.markdown("---")
    else:
        st.info("📝 No history yet. Share a message to start!")
    st.markdown('</div>', unsafe_allow_html=True)
    from core_auth_module import show_feedback_widget
    show_feedback_widget(f"conversation_{contact_name}")

# --- Main Application Flow Integration ---
def main():
    from core_auth_module import (
        init_session_state, get_current_user_id, supabase, sign_out,
        verification_notice_page, login_page, signup_page, render_first_time_screen,
        render_contacts_list_view, render_add_contact_view, render_edit_contact_view,
        load_contacts_and_history
    )
    st.set_page_config(
        page_title="The Third Voice AI",
        page_icon="🎙️",
        layout="wide",
        initial_sidebar_state="auto"
    )
    def restore_session():
        try:
            session = supabase.auth.get_session()
            if session and session.user:
                if not st.session_state.get("authenticated", False):
                    st.session_state.authenticated = True
                    st.session_state.user = session.user
                    st.session_state.contacts = load_contacts_and_history()
                    if st.session_state.contacts:
                        st.session_state.app_mode = "contacts_list"
                    else:
                        st.session_state.app_mode = "first_time_setup"
        except Exception as e:
            st.warning(f"Could not restore session: {e}")
    init_session_state()
    restore_session()
    with st.sidebar:
        st.markdown('<div class="header"><h2>🎙️ The Third Voice</h2></div>', unsafe_allow_html=True)
        if st.session_state.authenticated:
            st.markdown(f"**{st.session_state.user.email}**")
            if st.button("🏠 My Contacts", use_container_width=True):
                st.session_state.app_mode = "contacts_list"
                st.session_state.active_contact = None
                st.rerun()
            if st.button("🚪 Logout", use_container_width=True):
                sign_out()
        st.markdown("---")
        st.markdown("### 💙 Our Mission")
        st.markdown("""
            *"When both people speak from pain, someone must be the third voice."*
            **We help families heal through better conversations.**
        """)
        if st.checkbox("🔧 Debug Info"):
            try:
                session = supabase.auth.get_session()
                user_resp = supabase.auth.get_user()
                user = user_resp.user if user_resp else None
                debug_info = {
                    "Connection": "✅" if session else "❌",
                    "User ID": user.id[:8] + "..." if user else None,
                    "Email": user.email if user else None,
                    "Contacts": len(st.session_state.contacts),
                    "Active": st.session_state.active_contact,
                    "Mode": st.session_state.app_mode,
                    "Current Model": get_model_display_name(st.session_state.last_successful_model) if st.session_state.last_successful_model else "None",
                    "Secrets": {
                        "Supabase URL": "✅" if st.secrets.get("supabase", {}).get("url") else "❌",
                        "Supabase Key": "✅" if st.secrets.get("supabase", {}).get("key") else "❌",
                        "OpenRouter API": "✅" if st.secrets.get("openrouter", {}).get("api_key") else "❌",
                        "Models Configured": len(get_available_models())
                    }
                }
                try:
                    test_query = supabase.table("contacts").select("id").limit(1).execute()
                    debug_info["DB Test"] = f"✅ {len(test_query.data)} visible"
                except Exception as e:
                    debug_info["DB Test"] = f"❌ {str(e)[:20]}..."
                st.code(json.dumps(debug_info, indent=2, default=str), language="json")
            except Exception as e:
                st.error(f"Debug error: {e}")
    if st.session_state.authenticated:
        if st.session_state.app_mode == "first_time_setup":
            render_first_time_screen()
        elif st.session_state.app_mode == "contacts_list":
            render_contacts_list_view()
        elif st.session_state.app_mode == "conversation_view":
            render_conversation_view()
        elif st.session_state.app_mode == "edit_contact_view":
            render_edit_contact_view()
        elif st.session_state.app_mode == "add_contact_view":
            render_add_contact_view()
        else:
            st.session_state.app_mode = "contacts_list"
            st.rerun()
    else:
        if st.session_state.app_mode == "signup":
            signup_page()
        elif st.session_state.app_mode == "verification_notice":
            verification_notice_page()
        else:
            login_page()

if __name__ == "__main__":
    main()
