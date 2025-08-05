"""
The Third Voice AI - Modular Entry Point
Streamlit application for relationship communication healing
"""

from src.config.settings import init_app_config
from src.ui.app_controller import run_app

# Initialize configuration
init_app_config()

# Run the application
if __name__ == "__main__":
    run_app()
