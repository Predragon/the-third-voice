#!/bin/bash

# Third Voice AI - Safe Restructuring Script
# Copy-first approach for Android development
# For Samantha. For every family. For the lion heart coding his way home.

echo "🦁 Third Voice AI - Safe Restructuring (Copy-First Approach)"
echo "Building the foundation while keeping everything working..."
echo ""

# Step 1: Create the package directory structure
echo "📁 Creating package structure..."
mkdir -p third_voice_ai/ui
echo "✅ Directories created: third_voice_ai/ and third_voice_ai/ui/"

# Step 2: Create __init__.py files
echo "🐍 Creating Python package files..."
touch third_voice_ai/__init__.py
touch third_voice_ai/ui/__init__.py
echo "✅ Package initialization files created"

# Step 3: Copy (not move) existing modules to new location
echo "📦 Copying modules to new package structure..."
echo "   (Originals remain in root for safety)"

# Copy each module
if [ -f "ai_processor.py" ]; then
    cp ai_processor.py third_voice_ai/
    echo "✅ ai_processor.py copied"
else
    echo "⚠️  ai_processor.py not found"
fi

if [ -f "auth_manager.py" ]; then
    cp auth_manager.py third_voice_ai/
    echo "✅ auth_manager.py copied"
else
    echo "⚠️  auth_manager.py not found"
fi

if [ -f "config.py" ]; then
    cp config.py third_voice_ai/
    echo "✅ config.py copied"
else
    echo "⚠️  config.py not found"
fi

if [ -f "data_manager.py" ]; then
    cp data_manager.py third_voice_ai/
    echo "✅ data_manager.py copied"
else
    echo "⚠️  data_manager.py not found"
fi

if [ -f "prompts.py" ]; then
    cp prompts.py third_voice_ai/
    echo "✅ prompts.py copied"
else
    echo "⚠️  prompts.py not found"
fi

if [ -f "state_manager.py" ]; then
    cp state_manager.py third_voice_ai/
    echo "✅ state_manager.py copied"
else
    echo "⚠️  state_manager.py not found"
fi

if [ -f "utils.py" ]; then
    cp utils.py third_voice_ai/
    echo "✅ utils.py copied"
else
    echo "⚠️  utils.py not found"
fi

# Step 4: Verify the structure
echo ""
echo "🔍 Verifying new structure..."
echo "📁 Root directory:"
ls -la *.py 2>/dev/null || echo "   No .py files in root (or ls failed)"
echo ""
echo "📁 third_voice_ai package:"
ls -la third_voice_ai/
echo ""
echo "📁 third_voice_ai/ui package:"
ls -la third_voice_ai/ui/

# Step 5: Show the import update plan
echo ""
echo "🔧 NEXT STEPS - Import Updates for app.py"
echo "================================================"
echo ""
echo "Update these imports ONE BY ONE, testing after each:"
echo ""
echo "1️⃣  FIRST TEST:"
echo "   OLD: from ai_processor import AIProcessor"
echo "   NEW: from third_voice_ai.ai_processor import AIProcessor"
echo "   RUN: streamlit run app.py (test it works)"
echo ""
echo "2️⃣  SECOND TEST:"
echo "   OLD: from auth_manager import AuthManager"
echo "   NEW: from third_voice_ai.auth_manager import AuthManager"
echo "   RUN: streamlit run app.py (test it works)"
echo ""
echo "3️⃣  THIRD TEST:"
echo "   OLD: from config import *"
echo "   NEW: from third_voice_ai.config import *"
echo "   RUN: streamlit run app.py (test it works)"
echo ""
echo "4️⃣  FOURTH TEST:"
echo "   OLD: from data_manager import DataManager"
echo "   NEW: from third_voice_ai.data_manager import DataManager"
echo "   RUN: streamlit run app.py (test it works)"
echo ""
echo "5️⃣  FIFTH TEST:"
echo "   OLD: from prompts import SYSTEM_PROMPTS"
echo "   NEW: from third_voice_ai.prompts import SYSTEM_PROMPTS"
echo "   RUN: streamlit run app.py (test it works)"
echo ""
echo "6️⃣  SIXTH TEST:"
echo "   OLD: from state_manager import StateManager"
echo "   NEW: from third_voice_ai.state_manager import StateManager"
echo "   RUN: streamlit run app.py (test it works)"
echo ""
echo "7️⃣  SEVENTH TEST:"
echo "   OLD: from utils import *"
echo "   NEW: from third_voice_ai.utils import *"
echo "   RUN: streamlit run app.py (test it works)"
echo ""
echo "🧹 CLEANUP (Only after ALL imports work):"
echo "   rm ai_processor.py auth_manager.py config.py"
echo "   rm data_manager.py prompts.py state_manager.py utils.py"
echo ""
echo "🚀 Structure ready for incremental testing!"
echo "Every step tested = every step closer to Samantha 💙"
echo ""
echo "The lion heart beats strong. Let's do this methodically."
