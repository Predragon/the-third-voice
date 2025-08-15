"""
Demo Manager Module
Handles demo account functionality for The Third Voice AI
"""

import streamlit as st
from ..data.models import AIResponse

class DemoManager:
    DEMO_USER_ID = "demo_user"
    DEMO_USER_EMAIL = "demo@example.com"

    @staticmethod
    def sign_in(db=None):
        """Sign in as demo user and initialize session state"""
        st.session_state.user = type("DemoUser", (), {
            "id": DemoManager.DEMO_USER_ID,
            "email": DemoManager.DEMO_USER_EMAIL
        })()
        if "demo_messages" not in st.session_state:
            st.session_state.demo_messages = []

    @staticmethod
    def is_demo():
        """Check if current session is demo"""
        user = getattr(st.session_state, "user", None)
        return user and getattr(user, "id", None) == DemoManager.DEMO_USER_ID

    @staticmethod
    def get_demo_contacts():
        """Return demo contacts with contexts and descriptions"""
        return [
            {
                "id": "demo_ex_coparenting", 
                "name": "💔 Sarah (Ex-Wife)", 
                "context": "coparenting",
                "description": "Your ex-wife and co-parent of your 8-year-old daughter. Communication has been tense since the divorce, but you need to coordinate custody and school events."
            },
            {
                "id": "demo_current_partner", 
                "name": "💕 Mike (Current Partner)", 
                "context": "romantic",
                "description": "Your current boyfriend of 6 months. You're navigating blending families and he sometimes doesn't understand the co-parenting dynamics."
            },
            {
                "id": "demo_difficult_mother", 
                "name": "🏠 Mom", 
                "context": "family",
                "description": "Your mother who has strong opinions about your divorce and new relationship. She means well but often says hurtful things."
            },
            {
                "id": "demo_workplace_boss", 
                "name": "🏢 Jennifer (Boss)", 
                "context": "workplace",
                "description": "Your manager who's been unsympathetic about your need for flexible scheduling due to custody arrangements."
            },
            {
                "id": "demo_supportive_friend", 
                "name": "🤝 Lisa (Best Friend)", 
                "context": "friend",
                "description": "Your best friend since college who's been your rock through the divorce but sometimes gives harsh advice."
            }
        ]

    @staticmethod
    def get_demo_examples(contact_id):
        """Return example messages for each demo contact"""
        examples = {
            "demo_ex_coparenting": [
                "You're being unreasonable about the school pickup schedule again. This is exactly why our marriage didn't work.",
                "I can't believe you're putting Emma in the middle of this by telling her I'm 'too busy' for her recital.",
                "Your boyfriend doesn't get to make decisions about MY daughter's bedtime routine."
            ],
            "demo_current_partner": [
                "You just don't understand how complicated co-parenting is and you keep making it harder.",
                "I feel like you're jealous of the time I have to spend dealing with Sarah and Emma's needs.",
                "Why can't you just support me instead of always questioning how I handle things with my ex?"
            ],
            "demo_difficult_mother": [
                "I told you that divorce would ruin Emma's life and now look what's happening.",
                "Mike seems nice but you really should focus on fixing your family instead of dating around.",
                "You're being selfish putting your own happiness before your daughter's stability."
            ],
            "demo_workplace_boss": [
                "I can't keep covering for your constant schedule changes because of your personal problems.",
                "Other employees don't get special treatment for their custody arrangements, why should you?",
                "Your productivity has really declined since your divorce and it's affecting the whole team."
            ],
            "demo_supportive_friend": [
                "Honestly, you need to stop letting Sarah walk all over you and stand up for yourself.",
                "Mike is great but maybe you're moving too fast when you should focus on being a single mom.",
                "I'm tired of hearing you complain about the same problems but never taking my advice."
            ]
        }
        return examples.get(contact_id, [])

    @staticmethod
    def add_message(user_input, ai_response, contact, mode):
        """Store demo chat messages in session state"""
        if "demo_messages" not in st.session_state:
            st.session_state.demo_messages = []

        st.session_state.demo_messages.append({
            "input": user_input,
            "response": ai_response,
            "contact": contact,
            "mode": mode
        })
