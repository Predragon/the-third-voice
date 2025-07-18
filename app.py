import streamlit as st
import json
import datetime
import requests

# Constants
CONTEXTS = ["general", "romantic", "coparenting", "workplace", "family", "friend"]
REQUIRE_TOKEN = False

# Setup
st.set_page_config(page_title="The Third Voice", page_icon="🎙️", layout="wide")
st.markdown("""
<style>
.contact-card {background:rgba(76,175,80,0.1);padding:0.8rem;border-radius:8px;border-left:4px solid #4CAF50;margin:0.5rem 0;cursor:pointer}
.ai-response {background:rgba(76,175,80,0.1);padding:1rem;border-radius:8px;border-left:4px solid #4CAF50;margin:0.5rem 0}
.user-msg {background:rgba(33,150,243,0.1);padding:0.8rem;border-radius:8px;border-left:4px solid #2196F3;margin:0.3rem 0}
.contact-msg {background:rgba(255,193,7,0.1);padding:0.8rem;border-radius:8px;border-left:4px solid #FFC107;margin:0.3rem 0}
.pos {background:rgba(76,175,80,0.2);padding:0.5rem;border-radius:5px;margin:0.2rem 0}
.neg {background:rgba(244,67,54,0.2);padding:0.5rem;border-radius:5px;margin:0.2rem 0}
.neu {background:rgba(33,150,243,0.2);padding:0.5rem;border-radius:5px;margin:0.2rem 0}
.journal-section {background:rgba(156,39,176,0.1);padding:1rem;border-radius:8px;margin:0.5rem 0}
.main-actions {display:flex;gap:1rem;margin:1rem 0}
.main-actions button {flex:1;padding:0.8rem;font-size:1.1rem}
.feedback-section {background:rgba(0,150,136,0.1);padding:1rem;border-radius:8px;margin:1rem 0}
.stats-card {background:rgba(63,81,181,0.1);padding:1rem;border-radius:8px;margin:0.5rem 0;text-align:center}
</style>""", unsafe_allow_html=True)

# Session defaults
defaults = {
    'token_validated': not REQUIRE_TOKEN,
    'api_key': st.secrets.get("OPENROUTER_API_KEY", ""),
    'contacts': {'General': {'context': 'general', 'history': []}},
    'active_contact': 'General',
    'journal_entries': {},
    'feedback_data': {},
    'user_stats': {'total_messages': 0, 'coached_messages': 0, 'translated_messages': 0}
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Token gate
if REQUIRE_TOKEN and not st.session_state.token_validated:
    st.markdown("# 🎙️ The Third Voice")
    st.markdown("*Your AI Communication Coach*")
    st.warning("🔐 Access restricted. Enter beta token to continue.")
    token = st.text_input("Token:", type="password")
    if st.button("Validate"):
        if token in ["ttv-beta-001", "ttv-beta-002", "ttv-beta-003"]:
            st.session_state.token_validated = True
            st.success("✅ Authorized")
            st.rerun()
        else:
            st.error("Invalid token")
    st.stop()

# API function
def get_ai_response(message, context, is_received=False):
    if not st.session_state.api_key:
        return {"error": "No API key"}
    
    prompts = {
        "general": "You are an emotionally intelligent communication coach. Help improve this message for clarity and empathy.",
        "romantic": "You help reframe romantic messages with empathy and clarity while maintaining intimacy.",
        "coparenting": "You offer emotionally safe responses for coparenting focused on the children's wellbeing.",
        "workplace": "You translate workplace messages for professional tone and clear intent.",
        "family": "You understand family dynamics and help rephrase for better family relationships.",
        "friend": "You assist with friendship communication to strengthen bonds and resolve conflicts."
    }
    
    if is_received:
        system_prompt = f"{prompts.get(context, prompts['general'])} Analyze this received message and suggest how to respond."
    else:
        system_prompt = f"{prompts.get(context, prompts['general'])} Improve this message before sending."
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Message: {message}"}
    ]
    
    models = [
        "google/gemma-2-9b-it:free",
        "meta-llama/llama-3.2-3b-instruct:free",
        "microsoft/phi-3-mini-128k-instruct:free"
    ]
    
    for model in models:
        try:
            r = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                headers={"Authorization": f"Bearer {st.session_state.api_key}"},
                json={"model": model, "messages": messages}, timeout=30)
            r.raise_for_status()
            reply = r.json()["choices"][0]["message"]["content"]
            
            model_name = model.split("/")[-1].replace(":free", "").replace("-", " ").title()
            
            if is_received:
                return {
                    "type": "translate",
                    "sentiment": "neutral",
                    "meaning": f"Interpretation: {reply[:100]}...",
                    "response": reply,
                    "model": model_name
                }
            else:
                return {
                    "type": "coach",
                    "sentiment": "improved",
                    "original": message,
                    "improved": reply,
                    "model": model_name
                }
        except Exception as e:
            continue
    
    return {"error": "All models failed"}

# Sidebar - Contact Management
st.sidebar.markdown("### 👥 Your Contacts")

# Add new contact
with st.sidebar.expander("➕ Add Contact"):
    new_name = st.text_input("Name:")
    new_context = st.selectbox("Relationship:", CONTEXTS)
    if st.button("Add") and new_name and new_name not in st.session_state.contacts:
        st.session_state.contacts[new_name] = {'context': new_context, 'history': []}
        st.session_state.active_contact = new_name
        st.success(f"Added {new_name}")
        st.rerun()

# Contact selection
contact_names = list(st.session_state.contacts.keys())
if contact_names:
    selected = st.sidebar.radio("Select Contact:", contact_names, 
                               index=contact_names.index(st.session_state.active_contact))
    st.session_state.active_contact = selected

# Contact info
if st.session_state.active_contact in st.session_state.contacts:
    contact = st.session_state.contacts[st.session_state.active_contact]
    st.sidebar.markdown(f"**Context:** {contact['context']}")
    st.sidebar.markdown(f"**Messages:** {len(contact['history'])}")

# Delete contact
if st.sidebar.button("🗑️ Delete Contact") and st.session_state.active_contact != "General":
    del st.session_state.contacts[st.session_state.active_contact]
    st.session_state.active_contact = "General"
    st.rerun()

# File management
st.sidebar.markdown("---")
st.sidebar.markdown("### 💾 Data Management")
uploaded = st.sidebar.file_uploader("📤 Load History", type="json")
if uploaded:
    try:
        data = json.load(uploaded)
        st.session_state.contacts = data.get('contacts', st.session_state.contacts)
        st.session_state.journal_entries = data.get('journal_entries', {})
        st.session_state.feedback_data = data.get('feedback_data', {})
        st.session_state.user_stats = data.get('user_stats', st.session_state.user_stats)
        st.sidebar.success("✅ Data loaded!")
    except:
        st.sidebar.error("❌ Invalid file")

if st.sidebar.button("💾 Save All"):
    save_data = {
        'contacts': st.session_state.contacts,
        'journal_entries': st.session_state.journal_entries,
        'feedback_data': st.session_state.feedback_data,
        'user_stats': st.session_state.user_stats,
        'saved_at': datetime.datetime.now().isoformat()
    }
    filename = f"third_voice_{datetime.datetime.now().strftime('%m%d_%H%M')}.json"
    st.sidebar.download_button(
        "📥 Download File", 
        json.dumps(save_data, indent=2),
        filename,
        "application/json",
        use_container_width=True
    )

# Header
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    try:
        st.image("logo.svg", width=200)
    except:
        st.markdown("# 🎙️ The Third Voice")
    st.markdown("<div style='text-align: center'><i>Created by Predrag Mirković</i></div>", unsafe_allow_html=True)

st.markdown(f"### 💬 Communicating with: **{st.session_state.active_contact}**")

# Main action buttons
col1, col2 = st.columns(2)
with col1:
    if st.button("📤 Coach My Message", type="primary", use_container_width=True):
        st.session_state.active_mode = "coach"
        st.rerun()
with col2:
    if st.button("📥 Understand Their Message", type="primary", use_container_width=True):
        st.session_state.active_mode = "translate"
        st.rerun()

# Initialize mode
if 'active_mode' not in st.session_state:
    st.session_state.active_mode = None

# Message input and processing
if st.session_state.active_mode:
    mode = st.session_state.active_mode
    
    # Back button
    if st.button("← Back"):
        st.session_state.active_mode = None
        st.rerun()
    
    # Color-coded input area
    input_class = "user-msg" if mode == "coach" else "contact-msg"
    st.markdown(f'<div class="{input_class}"><strong>{"📤 Your message to send:" if mode == "coach" else "📥 Message you received:"}</strong></div>', unsafe_allow_html=True)
    
    message = st.text_area("", height=120, key=f"{mode}_input", label_visibility="collapsed", 
                          placeholder="Type your message here..." if mode == "coach" else "Paste their message here...")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        process_btn = st.button(f"{'🚀 Improve My Message' if mode == 'coach' else '🔍 Analyze & Respond'}", type="secondary")
    with col2:
        if st.button("Clear", type="secondary"):
            st.session_state[f"{mode}_input"] = ""
            st.rerun()
    
    if process_btn and message.strip():
        with st.spinner("🎙️ The Third Voice is analyzing..."):
            contact = st.session_state.contacts[st.session_state.active_contact]
            result = get_ai_response(message, contact['context'], mode == "translate")
            
            if "error" not in result:
                st.markdown("### 🎙️ The Third Voice says:")
                
                if mode == "coach":
                    st.markdown(f'<div class="ai-response"><strong>✨ Your improved message:</strong><br><br>{result["improved"]}<br><br><small><i>Generated by: {result["model"]}</i></small></div>', unsafe_allow_html=True)
                    st.session_state.user_stats['coached_messages'] += 1
                else:
                    st.markdown(f'<div class="ai-response"><strong>🔍 What they really mean:</strong><br>{result["response"]}<br><br><small><i>Generated by: {result["model"]}</i></small></div>', unsafe_allow_html=True)
                    st.session_state.user_stats['translated_messages'] += 1
                
                # Save to history
                history_entry = {
                    "id": f"{mode}_{len(contact['history'])}_{datetime.datetime.now().timestamp()}",
                    "time": datetime.datetime.now().strftime("%m/%d %H:%M"),
                    "type": mode,
                    "original": message,
                    "result": result.get("improved" if mode == "coach" else "response", ""),
                    "sentiment": result.get("sentiment", "neutral"),
                    "model": result.get("model", "Unknown")
                }
                
                contact['history'].append(history_entry)
                st.session_state.user_stats['total_messages'] += 1
                
                # Simple feedback
                st.markdown("### 📊 Was this helpful?")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("👍 Yes", key=f"good_{history_entry['id']}"):
                        st.session_state.feedback_data[history_entry['id']] = "positive"
                        st.success("Thanks for the feedback!")
                
                with col2:
                    if st.button("👌 Okay", key=f"ok_{history_entry['id']}"):
                        st.session_state.feedback_data[history_entry['id']] = "neutral"
                        st.success("Thanks for the feedback!")
                
                with col3:
                    if st.button("👎 No", key=f"bad_{history_entry['id']}"):
                        st.session_state.feedback_data[history_entry['id']] = "negative"
                        st.success("Thanks for the feedback!")
                
                st.success("✅ Saved to history")
                
            else:
                st.error(f"❌ {result['error']}")
    
    elif process_btn:
        st.warning("⚠️ Please enter a message first.")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📜 History", "📘 Journal", "📊 Stats", "ℹ️ About"])

with tab1:
    st.markdown(f"### 📜 History with {st.session_state.active_contact}")
    contact = st.session_state.contacts[st.session_state.active_contact]
    
    if not contact['history']:
        st.info(f"No messages yet with {st.session_state.active_contact}. Use the buttons above to get started!")
    else:
        # Filter options
        filter_type = st.selectbox("Filter:", ["All", "Coached Messages", "Understood Messages"])
        
        filtered_history = contact['history']
        if filter_type == "Coached Messages":
            filtered_history = [h for h in contact['history'] if h['type'] == 'coach']
        elif filter_type == "Understood Messages":
            filtered_history = [h for h in contact['history'] if h['type'] == 'translate']
        
        for i, entry in enumerate(reversed(filtered_history)):
            with st.expander(f"**{entry['time']}** • {entry['type'].title()} • {entry['original'][:50]}..."):
                if entry['type'] == 'coach':
                    st.markdown(f'<div class="user-msg">📤 <strong>Original:</strong> {entry["original"]}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="ai-response">🎙️ <strong>Improved:</strong> {entry["result"]}<br><small><i>by {entry.get("model", "Unknown")}</i></small></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="contact-msg">📥 <strong>They said:</strong> {entry["original"]}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="ai-response">🎙️ <strong>Analysis:</strong> {entry["result"]}<br><small><i>by {entry.get("model", "Unknown")}</i></small></div>', unsafe_allow_html=True)
                
                # Show feedback if available
                if entry.get('id') in st.session_state.feedback_data:
                    feedback = st.session_state.feedback_data[entry['id']]
                    emoji = {"positive": "👍", "neutral": "👌", "negative": "👎"}
                    st.markdown(f"*Your feedback: {emoji.get(feedback, '❓')}*")

with tab2:
    st.markdown(f"### 📘 Communication Journal - {st.session_state.active_contact}")
    contact_key = st.session_state.active_contact
    
    if contact_key not in st.session_state.journal_entries:
        st.session_state.journal_entries[contact_key] = {
            'what_worked': '', 'what_didnt': '', 'insights': '', 'patterns': ''
        }
    
    journal = st.session_state.journal_entries[contact_key]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="journal-section">', unsafe_allow_html=True)
        st.markdown("**💚 What worked well?**")
        journal['what_worked'] = st.text_area("", value=journal['what_worked'], key=f"worked_{contact_key}", height=100, placeholder="Communication strategies that were successful...")
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown('<div class="journal-section">', unsafe_allow_html=True)
        st.markdown("**🔍 Key insights?**")
        journal['insights'] = st.text_area("", value=journal['insights'], key=f"insights_{contact_key}", height=100, placeholder="Important realizations about this relationship...")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="journal-section">', unsafe_allow_html=True)
        st.markdown("**⚠️ What didn't work?**")
        journal['what_didnt'] = st.text_area("", value=journal['what_didnt'], key=f"didnt_{contact_key}", height=100, placeholder="What caused issues or misunderstandings...")
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown('<div class="journal-section">', unsafe_allow_html=True)
        st.markdown("**📊 Patterns noticed?**")
        journal['patterns'] = st.text_area("", value=journal['patterns'], key=f"patterns_{contact_key}", height=100, placeholder="Communication patterns you've observed...")
        st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.markdown("### 📊 Your Communication Stats")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f'<div class="stats-card"><h3>{st.session_state.user_stats["total_messages"]}</h3><p>Total Messages</p></div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'<div class="stats-card"><h3>{st.session_state.user_stats["coached_messages"]}</h3><p>Messages Coached</p></div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'<div class="stats-card"><h3>{st.session_state.user_stats["translated_messages"]}</h3><p>Messages Understood</p></div>', unsafe_allow_html=True)
    
    # Contact breakdown
    st.markdown("### 👥 By Contact")
    for name, contact in st.session_state.contacts.items():
        if contact['history']:
            coached = sum(1 for h in contact['history'] if h['type'] == 'coach')
            translated = sum(1 for h in contact['history'] if h['type'] == 'translate')
            st.markdown(f"**{name}:** {len(contact['history'])} total ({coached} coached, {translated} understood)")
    
    # Feedback summary
    if st.session_state.feedback_data:
        st.markdown("### 📝 Feedback Summary")
        positive = sum(1 for f in st.session_state.feedback_data.values() if f == "positive")
        neutral = sum(1 for f in st.session_state.feedback_data.values() if f == "neutral")
        negative = sum(1 for f in st.session_state.feedback_data.values() if f == "negative")
        
        st.markdown(f"👍 Positive: {positive} | 👌 Neutral: {neutral} | 👎 Negative: {negative}")

with tab4:
    st.markdown("""### ℹ️ About The Third Voice
    
**The communication coach that's there when you need it most.**

Instead of repairing relationships after miscommunication damage, The Third Voice helps you communicate better in real-time.

**How it works:**
1. **Select your contact** - Each relationship gets personalized coaching
2. **Coach your messages** - Improve what you're about to send
3. **Understand their messages** - Decode the real meaning behind their words
4. **Build better patterns** - Journal and learn from each interaction

**Key Features:**
- 🎯 Context-aware coaching for different relationships
- 📊 Track your communication progress
- 📘 Personal journal for insights
- 💾 Export/import your data
- 🔒 Privacy-first design

**Privacy First:** All data stays on your device. Save and load your own files.

**Beta v1.0.0** — Built with ❤️ to heal relationships through better communication.

*"When both people are talking from pain, someone needs to be the third voice."*

---

**Support & Community:**
- 💬 Join discussions at our community forum
- 📧 Report bugs or suggest features
- 🌟 Share your success stories

**Technical Details:**
- Powered by OpenRouter API
- Uses multiple AI models for reliability
- Built with Streamlit for easy deployment
    """)
