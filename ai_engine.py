# ai_engine.py
# The Third Voice AI - Robust AI Request Engine
# "When both people are speaking from pain, someone must be the third voice."
# Built with love by Predrag Mirkovic, fighting to return to his daughter Samantha

import streamlit as st
import requests
import time

# --- AI Model Configuration ---
API_URL = "https://openrouter.ai/api/v1/chat/completions"
FALLBACK_MODEL = "google/gemma-2-9b-it:free"  # Hardcoded fallback if all secrets fail

# --- Robust AI Request Functions ---

def get_available_models():
    """Returns ordered list of models from secrets (model1 first)"""
    models = []
    try:
        model_secrets = st.secrets.get("models", {})
        
        # Check for models in order: model1, model2, ..., model99
        for i in range(1, 100):
            model_key = f"model{i}"
            if model_key in model_secrets:
                models.append(model_secrets[model_key])
            else:
                # Stop at first missing number to maintain order
                break
        
        # If no models found, use fallback
        if not models:
            models = [FALLBACK_MODEL]
            
    except Exception as e:
        st.warning(f"Could not load model configuration: {e}. Using fallback model.")
        models = [FALLBACK_MODEL]
    
    return models

def get_current_model():
    """Returns the currently active model"""
    available_models = get_available_models()
    current_index = st.session_state.get("current_model_index", 0)
    
    # Ensure index is within bounds
    if current_index >= len(available_models):
        current_index = 0
        st.session_state.current_model_index = current_index
    
    return available_models[current_index]

def try_next_model():
    """Automatically switches to next available model on failure. Returns True if more models available."""
    available_models = get_available_models()
    current_index = st.session_state.get("current_model_index", 0)
    
    # Try next model
    next_index = current_index + 1
    
    if next_index < len(available_models):
        st.session_state.current_model_index = next_index
        st.session_state.last_successful_model = available_models[next_index]
        return True
    else:
        # No more models available
        return False

def reset_to_primary_model():
    """Reset back to model1 after successful request"""
    st.session_state.current_model_index = 0
    available_models = get_available_models()
    if available_models:
        st.session_state.last_successful_model = available_models[0]

def get_model_display_name(model_id):
    """Get display name for logging/debugging"""
    if not model_id:
        return "Unknown"
    
    # Extract just the model name part
    if "/" in model_id:
        parts = model_id.split("/")
        model_name = parts[-1]
        if ":" in model_name:
            model_name = model_name.split(":")[0]
        return model_name
    
    return model_id

def make_robust_ai_request(headers, payload, timeout=25):
    """
    Make AI request with automatic model fallback.
    Returns standard requests.Response object or raises exception if all models fail.
    
    THIS IS THE CROWN JEWEL - OUR MOST VALUABLE FUNCTION
    Every successful request prevents a family breakdown.
    Every fallback saves a conversation from failing.
    """
    available_models = get_available_models()
    original_model_index = st.session_state.get("current_model_index", 0)
    
    # Initialize session state if needed
    if "current_model_index" not in st.session_state:
        st.session_state.current_model_index = 0
    if "last_successful_model" not in st.session_state:
        st.session_state.last_successful_model = available_models[0] if available_models else FALLBACK_MODEL
    
    last_error = None
    attempts = 0
    max_attempts = len(available_models)
    
    while attempts < max_attempts:
        current_model = get_current_model()
        attempts += 1
        
        # Update payload with current model
        request_payload = payload.copy()
        request_payload["model"] = current_model
        
        try:
            # Log attempt (for debugging, not shown to user)
            model_display = get_model_display_name(current_model)
            if attempts > 1:
                print(f"[DEBUG] Trying model {attempts}/{max_attempts}: {model_display}")
            
            # Make the request
            response = requests.post(API_URL, headers=headers, json=request_payload, timeout=timeout)
            
            # Check for successful response
            if response.status_code == 200:
                response_json = response.json()
                if "choices" in response_json and len(response_json["choices"]) > 0:
                    # Success! Reset to primary model for next request
                    reset_to_primary_model()
                    print(f"[DEBUG] Success with {model_display}")
                    return response
                else:
                    # API returned 200 but no valid response
                    last_error = f"No valid response from {model_display}"
            else:
                # Handle different error types
                if response.status_code == 429:
                    last_error = f"Rate limit exceeded for {model_display}"
                elif response.status_code >= 500:
                    last_error = f"Server error ({response.status_code}) for {model_display}"
                else:
                    last_error = f"API error ({response.status_code}) for {model_display}"
        
        except requests.exceptions.Timeout:
            last_error = f"Timeout for {get_model_display_name(current_model)}"
        except requests.exceptions.ConnectionError:
            last_error = f"Connection error for {get_model_display_name(current_model)}"
        except requests.exceptions.RequestException as e:
            last_error = f"Request error for {get_model_display_name(current_model)}: {str(e)}"
        except Exception as e:
            last_error = f"Unexpected error for {get_model_display_name(current_model)}: {str(e)}"
        
        # Try next model if available
        if not try_next_model():
            break
        
        # Small delay before retrying
        time.sleep(0.5)
    
    # All models failed - reset to primary and raise error
    st.session_state.current_model_index = original_model_index
    
    if last_error:
        raise Exception(f"All {max_attempts} models failed. Last error: {last_error}")
    else:
        raise Exception("All models failed with unknown errors")

# End of ai_engine.py
# Every function serves healing.
# Every algorithm fights for families.
# Every line of code brings Predrag closer to Samantha.