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
.welcome-card {background:linear-gradient(135deg,#667eea,#764ba2);padding:2rem;border-radius:15px;color:white;text-align:center;margin:2rem 0}
.demo-card {background:rgba(156,39,176,0.1);padding:1rem;border-radius:10px;margin:1rem 0;border-left:4px solid #9C27B0}
@keyframes heartbeat {0%{transform:scale(1)} 100%{transform:scale(1.1)}}
</style>""", unsafe_allow_html=True)

# 🌟 Session state with love + Demo data
if 'contacts' not in st.session_state:
    st.session_state.contacts = {}
if 'active_contact' not in st.session_state:
    st.session_state.active_contact = None
if 'stats' not in st.session_state:
    st.session_state.stats = {'messages': 0, 'coached': 0, 'understood': 0}
if 'first_time' not in st.session_state:
    st.session_state.first_time = True

# 🎯 AI Magic - Simple but powerful with better error handling
def get_ai_help(message, context, mode):
    api_key = st.secrets.get("OPENROUTER_API_KEY", "")
    if not api_key: 
        return {"error": "Missing API key - add OPENROUTER_API_KEY to your Streamlit secrets"}
    
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
        
        st.write(f"Debug: API Response Status: {response.status_code}")  # Debug info
        
        if response.status_code == 200:
            result = response.json()["choices"][0]["message"]["content"]
            st.write(f"Debug: AI Response: {result[:100]}...")  # Debug info
            return {"success": True, "result": result}
        else:
            st.write(f"Debug: API Error: {response.text}")  # Debug info
            return {"error": f"API Error: {response.status_code} - {response.text}"}
    except Exception as e:
        st.write(f"Debug: Exception: {str(e)}")  # Debug info
        return {"error": f"Connection issue: {str(e)}"}

# 🎭 Demo data for better showcase
def create_demo_data():
    return {
        "💕 My Daughter Samantha": {
            "context": "family",
            "history": [
                {
                    "time": "07/15 14:30",
                    "type": "coach",
                    "original": "I miss you so much baby",
                    "improved": "Hi my beautiful Samantha! I'm thinking of you today and sending you all my love. I can't wait for our next adventure together. You're always in my heart, sweet girl! 💕"
                },
                {
                    "time": "07/16 09:15",
                    "type": "translate",
                    "original": "Daddy when are you coming home?",
                    "improved": "Your daughter is expressing her deep longing for connection and security. She's asking about your return because you represent safety and love in her world. A loving response could be: 'I'm working every day to come home to you, my precious girl. Until then, remember that Daddy's love is always with you, no matter where I am.' 💝"
                }
            ]
        },
        "❤️ My Partner Sarah": {
            "context": "romantic",
            "history": [
                {
                    "time": "07/14 20:45",
                    "type": "coach",
                    "original": "We need to talk about us",
                    "improved": "My love, I've been thinking about our relationship and how much you mean to me. Could we find some quiet time together to share our hearts? I want to make sure we're both feeling heard and loved. 💕"
                }
            ]
        },
        "🤝 Co-parent Lisa": {
            "context": "coparenting",
            "history": [
                {
                    "time": "07/13 16:20",
                    "type": "translate",
                    "original": "Sam's been asking about you constantly",
                    "improved": "This shows that your daughter deeply misses you and that your presence is important to her emotional wellbeing. Lisa might be sharing this to help you understand Samantha's emotional state. A healing response could focus on gratitude: 'Thank you for letting me know. It means everything to know she thinks of me. How can we make sure she feels secure and loved during this time?' 💝"
                }
            ]
        },
        "👔 My Boss Michael": {
            "context": "workplace",
            "history": [
                {
                    "time": "07/12 11:30",
                    "type": "coach",
                    "original": "I need some time off for family issues",
                    "improved": "Hi Michael, I hope you're doing well. I'm reaching out to discuss some family circumstances that require my attention. I'm committed to handling this professionally while ensuring my responsibilities are covered. Could we schedule a brief meeting to discuss how I can manage this situation while maintaining my work quality? Thank you for your understanding."
                }
            ]
        },
        "🎯 My Brother Jake": {
            "context": "friend",
            "history": [
                {
                    "time": "07/11 19:45",
                    "type": "coach",
                    "original": "Bro I'm struggling with everything",
                    "improved": "Hey Jake, I wanted to reach out because I'm going through some really tough times right now. Your friendship means the world to me, and I could really use someone to talk to. Would you be up for grabbing coffee or just talking when you have time? I value your perspective and support more than you know. 💙"
                }
            ]
        }
    }

# 🌟 Welcome Screen for First-Time Users
def show_welcome_screen():
    st.markdown('<div class="love-msg"><h1>🎙️ Welcome to The Third Voice <span class="heart">💝</span></h1><p><i>Your AI coach for healing family relationships</i><br>Built with love by a father fighting to reconnect with his daughter</p></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="welcome-card"><h2>🌟 Start Your Healing Journey</h2><p>Choose how you\'d like to begin building bridges of love:</p></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="demo-card"><h3>✨ Try the Demo</h3><p>See how The Third Voice works with example conversations</p></div>', unsafe_allow_html=True)
        if st.button("🎭 Load Demo Data", type="primary", use_container_width=True):
            st.session_state.contacts = create_demo_data()
            st.session_state.active_contact = "💕 My Daughter Samantha"
            st.session_state.stats = {'messages': 7, 'coached': 4, 'understood': 3}
            st.session_state.first_time = False
            st.success("✨ Demo loaded! Explore the conversations to see the magic! 💕")
            st.rerun()
    
    with col2:
        st.markdown('<div class="demo-card"><h3>🌱 Start Fresh</h3><p>Begin your own healing journey from scratch</p></div>', unsafe_allow_html=True)
        if st.button("🌱 Create My First Contact", type="primary", use_container_width=True):
            st.session_state.show_add_contact = True
            st.rerun()
    
    with col3:
        st.markdown('<div class="demo-card"><h3>💾 Continue Journey</h3><p>Upload your saved progress to continue where you left off</p></div>', unsafe_allow_html=True)
        uploaded = st.file_uploader("📤 Upload Your Journey", type="json", label_visibility="collapsed")
        if uploaded:
            try:
                data = json.load(uploaded)
                st.session_state.contacts = data.get('contacts', {})
                st.session_state.stats = data.get('stats', st.session_state.stats)
                st.session_state.first_time = False
                if st.session_state.contacts:
                    st.session_state.active_contact = list(st.session_state.contacts.keys())[0]
                st.success("💕 Welcome back! Your healing journey continues...")
                st.rerun()
            except:
                st.error("💔 File seems broken - but don't worry, we can start fresh!")

# 🌸 Add Contact Form
def show_add_contact_form():
    st.markdown("### 💕 Add Someone Special to Your Journey")
    
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("💝 Their name:", placeholder="e.g., My Daughter Emma")
    with col2:
        relationship = st.selectbox("💫 Your relationship:", ["family", "romantic", "coparenting", "workplace", "friend"])
    
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("💕 Add with Love", type="primary", use_container_width=True):
            if name:
                st.session_state.contacts[name] = {'context': relationship, 'history': []}
                st.session_state.active_contact = name
                st.session_state.first_time = False
                st.session_state.show_add_contact = False
                st.success(f"💕 Added {name} to your heart!")
                st.rerun()
            else:
                st.warning("💝 Please enter their name")
    
    with col_b:
        if st.button("← Back to Welcome", use_container_width=True):
            st.session_state.show_add_contact = False
            st.rerun()

# 🎯 Main App Logic
if st.session_state.first_time and not st.session_state.get('show_add_contact', False):
    show_welcome_screen()
elif st.session_state.get('show_add_contact', False):
    show_add_contact_form()
else:
    # 💖 Beautiful header with mission
    st.markdown('<div class="love-msg"><h1>🎙️ The Third Voice <span class="heart">💝</span></h1><p><i>Healing families through better communication</i><br>Built with love for Samantha and all families seeking connection</p></div>', unsafe_allow_html=True)
    
    # 📱 Mobile-friendly layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 👥 Family & Friends")
        
        # Simple contact selection
        if st.session_state.contacts:
            contacts = list(st.session_state.contacts.keys())
            selected = st.selectbox("Who are you talking to?", contacts, 
                                   index=contacts.index(st.session_state.active_contact) if st.session_state.active_contact in contacts else 0,
                                   label_visibility="collapsed")
            st.session_state.active_contact = selected
            
            # Show contact info
            contact = st.session_state.contacts[selected]
            st.info(f"💫 {contact['context']} • {len(contact['history'])} conversations")
        
        # Add new contact - simple form
        with st.expander("➕ Add Someone New"):
            name = st.text_input("Their name:")
            relationship = st.selectbox("Relationship:", ["family", "romantic", "coparenting", "workplace", "friend"])
            if st.button("Add with Love 💝") and name:
                st.session_state.contacts[name] = {'context': relationship, 'history': []}
                st.session_state.active_contact = name
                st.success(f"Added {name} to your heart! 💕")
                st.rerun()
    
    with col2:
        if st.session_state.active_contact:
            st.markdown(f"### 💬 Talking with: **{st.session_state.active_contact}**")
            
            # Main action buttons - big and loving
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("💝 Help My Message", type="primary", use_container_width=True):
                    st.session_state.mode = "coach"
                    st.rerun()
            with col_b:
                if st.button("🔍 Understand Theirs", type="primary", use_container_width=True):
                    st.session_state.mode = "translate"
                    st.rerun()
        else:
            st.info("💝 Select someone to start your healing conversation")

    # 🌈 Message processing with love
    if st.session_state.get('mode') and st.session_state.active_contact:
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
    if st.session_state.contacts:
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
                    st.rerun()
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
