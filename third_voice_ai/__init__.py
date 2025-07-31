import logging
import sys

def _setup_persistent_logging():
    """Setup logging that persists across Streamlit app refreshes"""
    logger = logging.getLogger('third_voice_ai')
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        logger.propagate = False
        logger.info("Third Voice AI logging initialized")
    
    return logger

_logger = _setup_persistent_logging()

def get_logger(module_name=None):
    """Get configured logger for a module"""
    if module_name:
        return logging.getLogger(f'third_voice_ai.{module_name}')
    return logging.getLogger('third_voice_ai')
