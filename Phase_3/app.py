import streamlit as st
import sys
import os

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from Phase_4.advanced_rag import AdvancedMFRagBot
import time

# Page Configuration
st.set_page_config(
    page_title="MF Chatbot - Advanced Mutual Fund Assistant",
    page_icon="📈",
    layout="centered"
)

# Sidebar for UI settings
with st.sidebar:
    st.title("MF Chatbot Settings")
    st.markdown("---")
    st.info("Phase 4 Integrated: Now using Hybrid Search (Vector + BM25) for better accuracy.")
    
    # Clear conversation button
    if st.button("Clear History"):
        st.session_state.messages = []
        st.rerun()

# Title and context
st.title("📈 Mutual Fund Assistant (v2)")
st.caption("Advanced RAG with Hybrid Search enabled.")

# Initialize Chatbot
@st.cache_resource
def get_bot():
    return AdvancedMFRagBot()

try:
    bot = get_bot()
except Exception as e:
    st.error(f"Error initializing chatbot: {e}")
    st.stop()

# Initialize session state for messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display conversation history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User query input
if prompt := st.chat_input("Ask about a fund (e.g., NAV, Risk, Benchmark)..."):
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Response with bot
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Simulating "Thinking..." (Optional but adds to UX)
        with st.status("Hybrid Search in progress...", expanded=False) as status:
            response = bot.ask(prompt)
            status.update(label="Analysis complete!", state="complete", expanded=False)
        
        # Display response with a typing effect
        for chunk in response.split():
            full_response += chunk + " "
            time.sleep(0.04)
            message_placeholder.markdown(full_response + "▌")
        
        message_placeholder.markdown(full_response)
        
    # Add bot response to history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
