"""Streamlit client for the Flask airline support agent."""

import base64
import os

import requests
import streamlit as st

st.set_page_config(page_title="FlightAI Support", page_icon="✈️", layout="centered")
st.title("FlightAI Support")
st.caption("Bookings, fares, refunds, baggage, and flight help in one conversation.")
api_url = st.sidebar.text_input("Backend URL", os.getenv("AIRLINE_API_URL", "http://localhost:5000"))

if "messages" not in st.session_state:
    st.session_state.messages = []

for item in st.session_state.messages:
    with st.chat_message(item["role"]):
        st.markdown(item["content"])
        if item.get("intent"):
            st.caption(f"Intent: {item['intent']}")

uploaded = st.file_uploader("Attach a boarding pass, baggage photo, or document", type=["png", "jpg", "jpeg", "webp"])
prompt = st.chat_input("How can we help with your journey?")
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
                                          "intent": result.get("intent")})
    except requests.RequestException as error:
        st.session_state.messages.append({"role": "assistant", "content": f"Backend unavailable: {error}"})
    st.rerun()