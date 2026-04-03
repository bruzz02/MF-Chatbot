import streamlit as st
import os
import sys
from pathlib import Path

# Add project root and Phase_2 to sys.path
root_path = str(Path(__file__).parent)
phase2_path = str(Path(__file__).parent / "Phase_2")
if root_path not in sys.path:
    sys.path.append(root_path)
if phase2_path not in sys.path:
    sys.path.append(phase2_path)

from Phase_2.chatbot import ask_chatbot

# Page Config
st.set_page_config(page_title="MF Chatbot", page_icon="💬", layout="wide")

# CUSTOM CSS for the UI matching the image
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #0d1117;
        color: #e6edf3;
    }

    /* Hide sidebar standard items */
    [data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }

    /* Top Nav Bar Emulation */
    .top-nav {
        background-color: #161b22;
        padding: 10px 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #30363d;
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 1000;
    }
    
    .nav-tabs {
        display: flex;
        gap: 20px;
        background: #1c2128;
        padding: 10px 20px;
        border-radius: 8px;
        margin-top: 60px;
        margin-bottom: 20px;
    }
    
    .nav-tab-item {
        color: #8b949e;
        font-size: 14px;
        cursor: pointer;
    }
    
    .nav-tab-item.active {
        color: #58a6ff;
        background: rgba(88, 166, 255, 0.1);
        padding: 4px 12px;
        border-radius: 6px;
    }

    /* Chat Container Layout */
    .main-container {
        display: flex;
        gap: 20px;
        margin-top: 10px;
    }

    /* Left Sidebar: Chats */
    .chat-sidebar {
        width: 300px;
        background: #161b22;
        border-radius: 12px;
        padding: 20px;
    }
    
    .sidebar-tabs {
        display: flex;
        justify-content: space-between;
        background: #1c2128;
        border-radius: 8px;
        padding: 5px;
        margin-bottom: 20px;
    }
    
    .s-tab {
        flex: 1;
        text-align: center;
        padding: 8px;
        font-size: 13px;
        color: #8b949e;
    }
    
    .s-tab.active {
        background: #58a6ff;
        color: white;
        border-radius: 6px;
    }

    /* Universal Streamlit Button Styling Fix */
    div.stButton > button {
        background-color: #314a7c !important; 
        color: #ffffff !important;
        border: 1px solid #58a6ff !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        text-align: left !important;
        padding: 0.5rem 1rem !important;
        margin-bottom: 8px !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
    }

    div.stButton > button:hover {
        background-color: #58a6ff !important;
        color: #0d1117 !important;
        border-color: #f0f6fc !important;
    }

    div.stButton > button p {
        color: inherit !important;
    }

    .avatar {
        width: 40px;
        height: 40px;
        background: #30363d;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
    }

    /* Main Chat Area */
    .chat-main {
        flex: 1;
        background: #161b22;
        border-radius: 12px;
        display: flex;
        flex-direction: column;
        height: 80vh;
        position: relative;
    }
    
    .chat-header {
        padding: 15px 25px;
        border-bottom: 1px solid #30363d;
        display: flex;
        align-items: center;
        gap: 15px;
    }

    .message-container {
        flex: 1;
        overflow-y: auto;
        padding: 20px;
        display: flex;
        flex-direction: column;
        gap: 15px;
    }

    .message {
        max-width: 70%;
        padding: 12px 18px;
        border-radius: 12px;
        font-size: 14px;
        line-height: 1.5;
    }

    .message.received {
        background: #1c2128;
        align-self: flex-start;
        border-bottom-left-radius: 2px;
    }

    .message.sent {
        background: #314a7c;
        color: white;
        align-self: flex-end;
        border-bottom-right-radius: 2px;
    }

    /* Input Bar */
    .input-bar {
        padding: 20px;
        background: #161b22;
        border-top: 1px solid #30363d;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    /* Right Sidebar */
    .right-sidebar {
        width: 280px;
        display: flex;
        flex-direction: column;
        gap: 20px;
    }
    
    .widget-box {
        background: #161b22;
        border-radius: 12px;
        padding: 20px;
    }
    
    .widget-title {
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 15px;
        color: #f0f6fc;
    }

    /* Add custom scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: #30363d;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# TOP NAVIGATION EMULATION
st.markdown("""
<div class="top-nav">
    <div style="font-size: 20px; font-weight: 700;">Chat Bot</div>
    <div style="display: flex; gap: 20px; align-items: center;">
        <span style="color: #8b949e;">Search...</span>
        <div class="avatar" style="width: 32px; height: 32px;">👤</div>
    </div>
</div>

<div class="nav-tabs">
    <div class="nav-tab-item active">Dashboard</div>
    <div class="nav-tab-item">Apps</div>
    <div class="nav-tab-item">Widgets</div>
    <div class="nav-tab-item">UI</div>
    <div class="nav-tab-item">Charts</div>
    <div class="nav-tab-item">Pages</div>
</div>
""", unsafe_allow_html=True)

# LAYOUT COLUMNS
col_left, col_main, col_right = st.columns([1, 2.2, 1])

# LEFT SIDEBAR - SUGGESTIONS
with col_left:
    st.markdown("""<div class="chat-sidebar">
<h3 style="margin-top: 0; font-size: 18px; color: #58a6ff;">Suggested Questions</h3>
<p style="font-size: 12px; color: #8b949e; margin-bottom: 20px;">Try asking these common queries:</p>
</div>""", unsafe_allow_html=True)
    
    suggestions = [
        "What is the NAV of Kotak Large Cap fund?",
        "What is the expense ratio of Kotak Midcap Fund?",
        "Which funds have 'Very High Risk'?",
        "What is the exit load for Kotak Multicap Fund?",
        "List all available Kotak Mutual Funds."
    ]

    for suggest in suggestions:
        if st.button(suggest, use_container_width=True):
            # Check if this query is already the last message to prevent loops (though less likely with buttons)
            if not st.session_state.messages or st.session_state.messages[-1]["content"] != suggest:
                # Add user message
                st.session_state.messages.append({"role": "user", "content": suggest})
                
                # Get AI response
                with st.spinner("Thinking..."):
                    response = ask_chatbot(suggest)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()

# MAIN CHAT AREA
with col_main:
    # Chat History State
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I am your Professional Mutual Fund Advisor. How can I help you with Kotak Mutual Funds today?"}
        ]

    # Header
    st.markdown("""<div style="background: #161b22; border-radius: 12px 12px 0 0; padding: 15px 25px; border-bottom: 1px solid #30363d; display: flex; align-items: center; gap: 15px;">
<div class="avatar" style="width: 48px; height: 48px; border: 2px solid #58a6ff;">IND</div>
<div>
<div style="font-weight: 600; font-size: 16px;">IND Money Chatbot</div>
<div style="font-size: 12px; color: #3fb950;">● Active Now</div>
</div>
</div>""", unsafe_allow_html=True)

    # Chat Messages Container
    chat_container = st.container(height=500)
    with chat_container:
        for m in st.session_state.messages:
            role_class = "sent" if m["role"] == "user" else "received"
            st.markdown(f'<div class="message {role_class}">{m["content"]}</div>', unsafe_allow_html=True)

    # Input handling
    user_query = st.chat_input("Say something...")
    if user_query:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_query})
        
        # Get AI response
        with st.spinner("Thinking..."):
            response = ask_chatbot(user_query)
            st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Rerun to update chat
        st.rerun()

# RIGHT SIDEBAR
with col_right:
    st.markdown("""<div class="right-sidebar">
<div class="widget-box">
<div class="widget-title">Available Funds</div>
<p style="font-size: 12px; color: #8b949e; margin-bottom: 15px;">You can ask queries about these funds:</p>
<div style="display: flex; flex-direction: column; gap: 10px;">
<div class="chat-list-item" style="padding: 8px; margin-bottom: 0;">
    <div class="avatar" style="width: 30px; height: 30px; font-size: 10px;">KL</div>
    <div style="font-size: 12px; font-weight: 500;">Kotak Large Cap Fund</div>
</div>
<div class="chat-list-item" style="padding: 8px; margin-bottom: 0;">
    <div class="avatar" style="width: 30px; height: 30px; font-size: 10px;">KM</div>
    <div style="font-size: 12px; font-weight: 500;">Kotak Midcap Fund</div>
</div>
<div class="chat-list-item" style="padding: 8px; margin-bottom: 0;">
    <div class="avatar" style="width: 30px; height: 30px; font-size: 10px;">KS</div>
    <div style="font-size: 12px; font-weight: 500;">Kotak Small Cap Fund</div>
</div>
<div class="chat-list-item" style="padding: 8px; margin-bottom: 0;">
    <div class="avatar" style="width: 30px; height: 30px; font-size: 10px;">MC</div>
    <div style="font-size: 12px; font-weight: 500;">Kotak Multicap Fund</div>
</div>
<div class="chat-list-item" style="padding: 8px; margin-bottom: 0;">
    <div class="avatar" style="width: 30px; height: 30px; font-size: 10px;">TS</div>
    <div style="font-size: 12px; font-weight: 500;">Kotak ELSS Tax Saver</div>
</div>
</div>
</div>
</div>""", unsafe_allow_html=True)
