# data_manager.py - The Third Voice AI Data Management
# Supabase database operations with mobile-friendly caching

import streamlit as st
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from .auth_manager import auth_manager
from .utils import utils
from .ui.components import display_error, display_success, show_feedback_widget
from .config import CACHE_TTL

class DataManager:
    # [Previous methods unchanged, omitted for brevity]
    
    def save_interpretation(self, contact_id: str, contact_name: str, original_message: str, 
                          interpretation: str, interpretation_score: int, model_used: str) -> bool:
        """
        Save interpretation to messages table with type 'interpretation'
        
        Args:
            contact_id: Contact ID
            contact_name: Contact name
            original_message: Original message
            interpretation: AI interpretation
            interpretation_score: Interpretation quality score
            model_used: AI model used
            
        Returns:
            True if successful, False otherwise
        """
        user_id = auth_manager.get_current_user_id()
        if not user_id:
            display_error("Cannot save interpretation: User not logged in.")
            return False
        
        try:
            interpretation_data = {
                "contact_id": contact_id,
                "contact_name": contact_name,
                "type": "interpretation",
                "original": original_message,
                "result": interpretation,
                "healing_score": interpretation_score,
                "model": model_used,
                "sentiment": "neutral",
                "emotional_state": "calm",
                "user_id": user_id,
                "created_at": utils.get_current_utc_timestamp()
            }
            
            response = self.supabase.table("messages").insert(interpretation_data).execute()
            if response.data:
                self.clear_cache()
                return True
            else:
                display_error("Failed to save interpretation")
                return False
            
        except Exception as e:
            display_error(f"Could not save interpretation: {e}")
            return False
    
    # [Rest of the class unchanged]
```
