# mo# modules/prompts.py

def get_prompt(context: str, message: str) -> str:
    """
    Generate prompt based on context and user message.
    """
    base_instruction = {
        "general": "Respond helpfully and kindly:",
        "romantic": "Give a warm and loving reply:",
        "coparenting": "Reply supportively, keep things child-focused:",
        "workplace": "Be professional and constructive:",
        "family": "Respond with empathy and understanding:",
        "friend": "Sound like a caring and honest friend:",
    }.get(context, "Respond appropriately:")

    return f"{base_instruction} {message}"
