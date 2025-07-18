import streamlit as st
import json
import datetime
import requests

# 🎙️ THE THIRD VOICE - Healing families through better communication
# Built with love by a father fighting to reconnect with his daughter
# Open source - because healing should be accessible to all families

st.set_page_config(page_title="The Third Voice", page_icon="🎙️", layout="wide")

# 💝 Loving CSS - Simple but beautiful
st.markdown("""<style>
.love-msg {background:linear-gradient(45deg,#ff6b6b,#feca57);padding:1rem;border-radius:12px;color:white;text-align:center;margin:1rem 0}
.contact-card {background:rgba(76,175,80,0.15);padding:1rem;border-radius:10px;margin:0.5rem 0;border-left:4px solid #4CAF50}
.ai-response {background:rgba(76,175,80,0.1);padding:1rem;border-radius:10px;border-left:4px solid #4CAF50;margin:1rem 0}
.user-msg {background:rgba(33,150,243,0.1);padding:1rem;border-radius:10px;border-left:4px solid #2196F3}
.contact-msg {background:rgba(255,193,7,0.1);padding:1rem;border-radius:10px;border-left:4px solid #FFC107}
.heart {animation:heartbeat 1.5s ease-in-out infinite alternate}
@keyframes heartbeat {0%{transform:scale(1)} 100%{transform:scale(1.1)}}
</style>""", unsafe_allow_html=True)

# 🌟 Session state with love
if 'contacts' not in st.session_state:
    st.session_state.contacts = {'❤️ My Heart': {'context': 'family', 'history': []}}
if 'active_contact' not in st.session_state:
    st.session_state.active_contact = '❤️ My Heart'
if 'stats' not in st.session_state:
    st.session_state.stats = {'messages': 0, 'coached': 0, 'understood': 0}

# 🎯 AI Magic - Simple but powerful
def get_ai_help(message, context, mode):
    api_key = st.secrets.get("OPENROUTER_API_KEY", "")
    if not api_key: return {"error": "Add your API key to secrets"}
    
    prompts = {
        "family": "Help heal family relationships with empathy and understanding",
        "romantic": "Strengthen love bonds with gentle, caring communication", 
        "coparenting": "Focus on the children's wellbeing and healing",
        "workplace": "Professional yet warm communication",
        "friend": "Deepen friendships with authentic connection"
    }
    
    if mode == "coach":
        system = f"{prompts.get(context, 'Help communicate with love and clarity')}. Improve this message with warmth and understanding."
    else:
        system = f"{prompts.get(context, 'Translate with compassion')}. Help understand what they really mean and suggest a loving response."
    
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "google/gemma-2-9b-it:free",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": message}
                ]
            }, timeout=30)
        
        if response.status_code == 200:
            result = response.json()["choices"][0]["message"]["content"]
            return {"success": True, "result": result}
        else:
            return {"error": "AI is taking a break - try again"}
    except:
        return {"error": "Connection issue - please try again"}

# 💖 Beautiful header with mission
st.markdown('<div class="love-msg"><h1>🎙️ The Third Voice <span class="heart">💝</span></h1><p><i>Healing families through better communication</i><br>Built with love for Samantha and all families seeking connection</p></div>', unsafe_allow_html=True)

# 📱 Mobile-friendly layout
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 👥 Family & Friends")
    
    # Simple contact selection
    contacts = list(st.session_state.contacts.keys())
    selected = st.selectbox("Who are you talking to?", contacts, label_visibility="collapsed")
    st.session_state.active_contact = selected
    
    # Add new contact - simple form
    with st.expander("➕ Add Someone New"):
        name = st.text_input("Their name:")
        relationship = st.selectbox("Relationship:", ["family", "romantic", "coparenting", "workplace", "friend"])
        if st.button("Add with Love 💝") and name:
            st.session_state.contacts[name] = {'context': relationship, 'history': []}
            st.success(f"Added {name} to your heart! 💕")

with col2:
    st.markdown(f"### 💬 Talking with: **{st.session_state.active_contact}**")
    
    # Main action buttons - big and loving
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("💝 Help My Message", type="primary", use_container_width=True):
            st.session_state.mode = "coach"
    with col_b:
        if st.button("🔍 Understand Theirs", type="primary", use_container_width=True):
            st.session_state.mode = "translate"

# 🌈 Message processing with love
if st.session_state.get('mode'):
    mode = st.session_state.mode
    
    if st.button("← Back to Love"):
        del st.session_state.mode
        st.rerun()
    
    # Beautiful input area
    if mode == "coach":
        st.markdown('<div class="user-msg"><strong>💝 Your message (let\'s make it even more loving):</strong></div>', unsafe_allow_html=True)
        placeholder = "What do you want to say? I'll help make it more loving..."
    else:
        st.markdown('<div class="contact-msg"><strong>🔍 Their message (let\'s understand their heart):</strong></div>', unsafe_allow_html=True)
        placeholder = "What did they say? I'll help you understand..."
    
    message = st.text_area("", height=100, placeholder=placeholder, label_visibility="collapsed")
    
    if st.button(f"✨ {'Make It More Loving' if mode == 'coach' else 'Help Me Understand'}", type="secondary"):
        if message.strip():
            with st.spinner("💫 The Third Voice is working with love..."):
                contact = st.session_state.contacts[st.session_state.active_contact]
                result = get_ai_help(message, contact['context'], mode)
                
                if result.get("success"):
                    st.markdown("### 🎙️ Here's what your heart is saying:")
                    st.markdown(f'<div class="ai-response">{result["result"]}</div>', unsafe_allow_html=True)
                    
                    # Save with love
                    entry = {
                        "time": datetime.datetime.now().strftime("%m/%d %H:%M"),
                        "type": mode,
                        "original": message,
                        "improved": result["result"]
                    }
                    contact['history'].append(entry)
                    
                    # Update stats with celebration
                    st.session_state.stats['messages'] += 1
                    if mode == "coach":
                        st.session_state.stats['coached'] += 1
                    else:
                        st.session_state.stats['understood'] += 1
                    
                    # Celebration for healing
                    if st.session_state.stats['messages'] % 5 == 0:
                        st.balloons()
                        st.success("🎉 You've helped heal 5 more conversations! You're building bridges of love! 💕")
                    
                else:
                    st.error(f"💔 {result['error']}")
        else:
            st.warning("💝 Please share your message first")

# 📊 Love-filled tabs
tab1, tab2, tab3 = st.tabs(["💕 Our Journey", "📊 Healing Stats", "💾 Save Progress"])

with tab1:
    st.markdown(f"### 💕 Your healing journey with {st.session_state.active_contact}")
    contact = st.session_state.contacts[st.session_state.active_contact]
    
    if not contact['history']:
        st.info("🌱 Your healing journey starts here! Use the buttons above to begin building bridges of love.")
    else:
        for entry in reversed(contact['history'][-5:]):  # Show last 5
            with st.expander(f"💝 {entry['time']} - {entry['original'][:30]}..."):
                st.markdown(f'<div class="user-msg">Original: {entry["original"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="ai-response">With Love: {entry["improved"]}</div>', unsafe_allow_html=True)

with tab2:
    st.markdown("### 📊 Your Journey of Healing")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💝 Messages Healed", st.session_state.stats['messages'])
    with col2:
        st.metric("✨ Coached", st.session_state.stats['coached'])
    with col3:
        st.metric("🔍 Understood", st.session_state.stats['understood'])
    
    # Progress celebration
    if st.session_state.stats['messages'] > 0:
        st.progress(min(st.session_state.stats['messages'] / 50, 1.0))
        st.caption("🌟 Building bridges of love, one message at a time!")

with tab3:
    st.markdown("### 💾 Save Your Healing Journey")
    
    # Simple save/load with love
    save_data = {
        'contacts': st.session_state.contacts,
        'stats': st.session_state.stats,
        'saved_with_love': datetime.datetime.now().isoformat()
    }
    
    # Download with love
    filename = f"third_voice_love_{datetime.datetime.now().strftime('%m%d_%H%M')}.json"
    st.download_button(
        "💾 Save My Journey",
        json.dumps(save_data, indent=2),
        filename,
        "application/json",
        help="Save your progress to continue healing later 💕"
    )
    
    # Upload with love
    uploaded = st.file_uploader("📤 Continue My Journey", type="json")
    if uploaded:
        try:
            data = json.load(uploaded)
            st.session_state.contacts = data.get('contacts', st.session_state.contacts)
            st.session_state.stats = data.get('stats', st.session_state.stats)
            st.success("💕 Welcome back! Your healing journey continues...")
        except:
            st.error("💔 File seems broken - but don't worry, we can start fresh!")

# 🌟 Footer with love and mission
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 2rem; background: linear-gradient(45deg, #667eea, #764ba2); border-radius: 15px; color: white; margin: 2rem 0;'>
    <h3>💝 Built with Love</h3>
    <p><i>Created by a father fighting to reconnect with his 6-year-old daughter Samantha</i></p>
    <p>🌟 <strong>Open Source</strong> - Because healing should be accessible to all families</p>
    <p>💕 Every message you heal brings families closer together</p>
    <p><small>You're not just fixing communication - you're building bridges of love 🌈</small></p>
</div>
""", unsafe_allow_html=True)
