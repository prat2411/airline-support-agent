"""Streamlit client for the multimodal airline support agent."""

import base64
import os
from datetime import datetime

import requests
import streamlit as st

st.set_page_config(page_title="AeroAssist | Customer Care", page_icon="✈️", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --ink: #10242d; --muted: #6b7d80; --teal: #0d7771; --mint: #dff2ed; --coral: #f4775b; --paper: #f7faf8; }
* { font-family: 'Manrope', sans-serif; }
.stApp { background: radial-gradient(circle at 84% 4%, #d7efea 0, transparent 28%), var(--paper); color: var(--ink); }
[data-testid="stSidebar"] { background: #10242d; border-right: 0; }
[data-testid="stSidebar"] * { color: #e7f3ee; }
[data-testid="stSidebar"] .stCaption { color: #a9c5c0; }
.brand { display: flex; align-items: center; gap: 12px; margin: 12px 0 42px; }
.brand-mark { width: 42px; height: 42px; display: grid; place-items: center; background: var(--coral); color: white; border-radius: 12px; font-size: 21px; transform: rotate(-8deg); }
.brand-name { font-size: 19px; font-weight: 800; letter-spacing: -.5px; }
.brand-sub { color: #9dbab5; font-size: 11px; letter-spacing: 1.5px; text-transform: uppercase; margin-top: 2px; }
.side-section { color: #86b5ae; font: 500 11px 'DM Mono', monospace; letter-spacing: 1.2px; text-transform: uppercase; margin: 22px 0 10px; }
.side-card { background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.1); border-radius: 12px; padding: 13px; margin-bottom: 9px; font-size: 13px; }
.side-card strong { display: block; color: white; margin-bottom: 4px; }
.side-card span { color: #a9c5c0; font-size: 12px; }
.hero { padding: 22px 0 12px; }
.eyebrow { color: var(--teal); font: 500 11px 'DM Mono', monospace; letter-spacing: 1.8px; text-transform: uppercase; }
.hero h1 { font-size: clamp(30px, 4vw, 54px); line-height: 1.02; letter-spacing: -2px; margin: 8px 0 12px; color: var(--ink); }
.hero p { color: var(--muted); max-width: 620px; font-size: 15px; line-height: 1.6; }
.status { display: inline-flex; align-items: center; gap: 7px; background: white; border: 1px solid #d7e6e2; padding: 8px 12px; border-radius: 999px; color: var(--teal); font-size: 12px; font-weight: 700; }
.status-dot { width: 7px; height: 7px; border-radius: 50%; background: #39b681; box-shadow: 0 0 0 4px #ddf4e9; }
.metric { background: white; border: 1px solid #e1ece8; border-radius: 14px; padding: 15px 17px; min-height: 92px; }
.metric-label { color: var(--muted); font: 500 10px 'DM Mono', monospace; text-transform: uppercase; letter-spacing: 1px; }
.metric-value { color: var(--ink); font-size: 24px; font-weight: 800; margin-top: 8px; }
.metric-note { color: var(--teal); font-size: 11px; margin-top: 3px; }
[data-testid="stChatMessage"] { border: 1px solid #e1ece8; border-radius: 16px; padding: 14px 17px; background: white; box-shadow: 0 5px 18px rgba(16,36,45,.035); }
[data-testid="stChatMessage"] p { line-height: 1.65; }
.intent-tag { display: inline-block; margin-top: 8px; padding: 4px 8px; border-radius: 5px; background: var(--mint); color: var(--teal); font: 500 10px 'DM Mono', monospace; text-transform: uppercase; }
.tool-tag { display: inline-block; margin: 8px 5px 0 0; padding: 4px 8px; border-radius: 5px; background: #fff0e9; color: #bd563e; font: 500 10px 'DM Mono', monospace; }
div[data-testid="stChatInput"] { padding-bottom: 18px; }
@media (max-width: 760px) { .hero h1 { font-size: 34px; letter-spacing: -1px; } .brand { margin-bottom: 22px; } }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="brand"><div class="brand-mark">✈</div><div><div class="brand-name">AeroAssist</div><div class="brand-sub">Customer care, reimagined</div></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="side-section">Live workspace</div>', unsafe_allow_html=True)
    st.markdown('<div class="side-card"><strong>Agent status</strong><span>Ready to route your request</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="side-card"><strong>12 support intents</strong><span>Bookings, fares, baggage and more</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="side-section">Connection</div>', unsafe_allow_html=True)
    api_url = st.text_input("Backend URL", os.getenv("AIRLINE_API_URL", "http://localhost:5000"), label_visibility="collapsed")
    st.caption("The local fallback stays available when no model key is configured.")
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

main, rail = st.columns([2.35, 1], gap="large")
with main:
    st.markdown('<div class="hero"><div class="eyebrow">Multimodal flight support</div><h1>Let’s get your journey<br>back on course.</h1><p>One calm place for bookings, flight changes, refunds, baggage issues, and the details that matter when travel gets complicated.</p><div class="status"><span class="status-dot"></span> Support desk online</div></div>', unsafe_allow_html=True)

    for item in st.session_state.messages:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])
            if item.get("intent"):
                st.markdown(f'<span class="intent-tag">{item["intent"].replace("_", " ")}</span>', unsafe_allow_html=True)
            for tool_name in item.get("tools_called", []):
                st.markdown(f'<span class="tool-tag">tool · {tool_name.replace("_", " ")}</span>', unsafe_allow_html=True)

with rail:
    st.markdown('<div class="side-section">At a glance</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric"><div class="metric-label">Conversation turns</div><div class="metric-value">{len(st.session_state.messages) // 2}</div><div class="metric-note">Context retained</div></div>', unsafe_allow_html=True)
    st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
    st.markdown('<div class="metric"><div class="metric-label">Coverage</div><div class="metric-value">12</div><div class="metric-note">Intent categories</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="side-section">Suggested starts</div>', unsafe_allow_html=True)
    for suggestion in ["What is my baggage allowance?", "I need to change my flight", "My bag did not arrive"]:
        st.markdown(f'<div class="side-card"><span>{suggestion}</span></div>', unsafe_allow_html=True)

uploaded = st.file_uploader("Attach a boarding pass, baggage photo, or document", type=["png", "jpg", "jpeg", "webp"], label_visibility="collapsed")
if uploaded:
    st.caption(f"Attachment ready: {uploaded.name}")
prompt = st.chat_input("Ask about a booking, flight, refund, bag, or complaint...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    image = None
    if uploaded:
        image = {"name": uploaded.name, "mime": uploaded.type,
                 "data": base64.b64encode(uploaded.getvalue()).decode("ascii")}
    try:
        response = requests.post(f"{api_url.rstrip('/')}/chat", json={
            "message": prompt, "history": st.session_state.messages[:-1], "image": image
        }, timeout=60)
        response.raise_for_status()
        result = response.json()
        st.session_state.messages.append({"role": "assistant", "content": result["answer"],
                          "intent": result.get("intent"),
                          "tools_called": result.get("tools_called", []),
                          "time": datetime.now().strftime("%H:%M")})
    except requests.RequestException as error:
        st.session_state.messages.append({"role": "assistant", "content": f"Backend unavailable: {error}"})
    st.rerun()