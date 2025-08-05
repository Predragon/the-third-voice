"""
Configuration Management for The Third Voice AI
Centralized settings and secrets management
Updated with sidebar enabled by default
"""

import streamlit as st


class AppConfig:
    """Centralized configuration management"""
    
    # Static configurations (no secrets)
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    AI_MODEL = "google/gemma-2-9b-it:free"
    MAX_TOKENS = 1000
    TEMPERATURE = 0.7
    APP_NAME = "The Third Voice AI"
    APP_TAGLINE = "When both people are speaking from pain, someone must be the third voice"
    CACHE_EXPIRY_DAYS = 7
    MOBILE_BREAKPOINT = 768
    
    @classmethod
    def get_supabase_url(cls):
        """Get Supabase URL from secrets"""
        return st.secrets["supabase"]["url"]
    
    @classmethod
    def get_supabase_key(cls):
        """Get Supabase key from secrets"""
        return st.secrets["supabase"]["key"]
    
    @classmethod
    def get_openrouter_api_key(cls):
        """Get OpenRouter API key from secrets"""
        return st.secrets["openrouter"]["api_key"]


def init_app_config():
    """Initialize application configuration with sidebar enabled"""
    st.set_page_config(
        page_title=AppConfig.APP_NAME,
        page_icon="🎙️",
        layout="wide",
        initial_sidebar_state="expanded"  # Changed from "collapsed" to "expanded"
    )