# test_app.py - Minimal test to isolate the issue
import streamlit as st

st.set_page_config(page_title="Test App", page_icon="🧪")

st.title("🧪 The Third Voice - Test App")
st.success("✅ Streamlit is working!")

# Test importing your modules one by one
st.subheader("Module Import Tests")

modules_to_test = ['ai_core', 'data_backend', 'ui_components']

for module_name in modules_to_test:
    try:
        exec(f"import {module_name}")
        st.success(f"✅ {module_name} imported successfully")
    except Exception as e:
        st.error(f"❌ Failed to import {module_name}: {e}")
        st.code(str(e))

st.info("If all modules import successfully, the issue is in your main app logic.")
st.info("If any module fails, that's where you need to focus your debugging.")
