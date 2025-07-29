# third_voice_ai/ui/components.py
# UI component functions for The Third Voice AI

import streamlit as st
from typing import Optional


def show_feedback_widget(context: str = "general") -> None:
    """
    Display feedback widget for user input
    
    Args:
        context: Context identifier for the feedback (used for unique keys)
    """
    with st.expander("💭 Share Feedback", expanded=False):
        feedback = st.text_area(
            "How can we improve?", 
            key=f"feedback_{context}",
            placeholder="Your feedback helps us build better healing conversations..."
        )
        if st.button("Submit Feedback", key=f"submit_{context}"):
            if feedback.strip():
                st.success("Thank you for your feedback! Your input helps us improve.")
                # TODO: In production, save feedback to database
                # data_manager.save_feedback(context, feedback)
            else:
                st.warning("Please enter some feedback first.")


def display_error(message: str) -> None:
    """
    Display error message with consistent formatting
    
    Args:
        message: Error message to display
    """
    st.error(f"❌ {message}")


def display_success(message: str) -> None:
    """
    Display success message with consistent formatting
    
    Args:
        message: Success message to display
    """
    st.success(f"✅ {message}")


def display_info(message: str) -> None:
    """
    Display info message with consistent formatting
    
    Args:
        message: Info message to display
    """
    st.info(f"ℹ️ {message}")


def display_warning(message: str) -> None:
    """
    Display warning message with consistent formatting
    
    Args:
        message: Warning message to display
    """
    st.warning(f"⚠️ {message}")


def show_loading_spinner(message: str = "Processing...") -> None:
    """
    Show loading spinner with message
    
    Args:
        message: Loading message to display
    """
    with st.spinner(message):
        pass


def create_two_column_layout():
    """
    Create consistent two-column layout
    
    Returns:
        Tuple of two Streamlit columns
    """
    return st.columns(2)


def create_three_column_layout():
    """
    Create consistent three-column layout
    
    Returns:
        Tuple of three Streamlit columns
    """
    return st.columns(3)


def create_metric_card(title: str, value: str, delta: Optional[str] = None):
    """
    Create a metric card display
    
    Args:
        title: Metric title
        value: Metric value
        delta: Optional delta value for comparison
    """
    st.metric(title, value, delta)


def show_contact_card(name: str, context_icon: str, preview: str, time_str: str, key: str):
    """
    Display a contact card button
    
    Args:
        name: Contact name
        context_icon: Icon for relationship context
        preview: Message preview
        time_str: Time string
        key: Unique key for the button
        
    Returns:
        Boolean: True if button was clicked
    """
    return st.button(
        f"{context_icon} **{name}** • {time_str}\n_{preview}_",
        key=key,
        use_container_width=True
    )


def show_navigation_button(label: str, key: str, use_container_width: bool = True):
    """
    Display a navigation button with consistent styling
    
    Args:
        label: Button label
        key: Unique key for the button
        use_container_width: Whether to use full container width
        
    Returns:
        Boolean: True if button was clicked
    """
    return st.button(label, key=key, use_container_width=use_container_width)


def show_form_input(label: str, key: str, input_type: str = "text", **kwargs):
    """
    Display form input with consistent styling
    
    Args:
        label: Input label
        key: Unique key for the input
        input_type: Type of input (text, password, textarea)
        **kwargs: Additional arguments for the input widget
        
    Returns:
        Input value
    """
    if input_type == "password":
        return st.text_input(label, type="password", key=key, **kwargs)
    elif input_type == "textarea":
        return st.text_area(label, key=key, **kwargs)
    else:
        return st.text_input(label, key=key, **kwargs)


def show_selectbox(label: str, options: list, key: str, format_func=None, **kwargs):
    """
    Display selectbox with consistent styling
    
    Args:
        label: Selectbox label
        options: List of options
        key: Unique key for the selectbox
        format_func: Optional function to format options
        **kwargs: Additional arguments
        
    Returns:
        Selected value
    """
    return st.selectbox(label, options, key=key, format_func=format_func, **kwargs)


def show_expandable_section(title: str, content_func, expanded: bool = False):
    """
    Display expandable section with consistent styling
    
    Args:
        title: Section title
        content_func: Function to render content inside expander
        expanded: Whether section should be expanded by default
    """
    with st.expander(title, expanded=expanded):
        content_func()


def show_sidebar_section(title: str, content_func):
    """
    Display sidebar section with consistent styling
    
    Args:
        title: Section title
        content_func: Function to render content in sidebar
    """
    st.sidebar.markdown(f"### {title}")
    content_func()


def show_conversation_message(message_data: dict, key_prefix: str):
    """
    Display a conversation message with consistent formatting
    
    Args:
        message_data: Dictionary containing message data
        key_prefix: Prefix for unique keys
    """
    col_time, col_score = st.columns([3, 1])
    
    with col_time:
        st.markdown(f"**{message_data['time']}** • {message_data['type'].title()}")
    
    with col_score:
        score = message_data.get('healing_score', 0)
        score_color = "🟢" if score >= 8 else "🟡" if score >= 6 else "🔴"
        st.markdown(f"{score_color} {score}/10")
    
    st.markdown("**Your Message:**")
    st.info(message_data['original'])
    
    if message_data.get('result'):
        st.markdown("**Third Voice Guidance:**")
        st.text_area(
            "AI Guidance",
            value=message_data['result'],
            height=100,
            key=f"{key_prefix}_{message_data.get('id', hash(message_data['original']))}",
            disabled=True,
            label_visibility="hidden"
        )
        
        if message_data.get('model'):
            st.caption(f"🤖 Model: {message_data['model']}")


def show_healing_score_display(score: int, show_balloons: bool = False):
    """
    Display healing score with appropriate styling
    
    Args:
        score: Healing score (0-10)
        show_balloons: Whether to show balloons for high scores
    """
    if score >= 8:
        st.success(f"✨ Healing Score: {score}/10")
        if show_balloons:
            st.balloons()
    elif score >= 6:
        st.info(f"💡 Healing Score: {score}/10")
    else:
        st.warning(f"🔧 Healing Score: {score}/10")


def show_copy_button(label: str = "📋", key: str = "copy_btn", help_text: str = "Click text area above and Ctrl+A to select all"):
    """
    Display copy button with help text
    
    Args:
        label: Button label
        key: Unique key for button
        help_text: Help text for the button
        
    Returns:
        Boolean: True if button was clicked
    """
    if st.button(label, help=help_text, key=key):
        st.info("💡 Click in text area above, then Ctrl+A and Ctrl+C to copy")
        return True
    return False
