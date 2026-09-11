# ✈️ Multimodal Airline Customer Support Agent

A Flask backend and Streamlit client for an agent that handles flight bookings,
fares, refunds, baggage, and complaints through natural language and image attachments.

## Features
- 12 intent categories: booking, fare, status, baggage policy, cancellation, refund,
  flight changes, check-in, lost baggage, complaint, accessibility, and other
- LangChain tool calling for fare lookup and support-case creation
- Multi-turn history retained by the Streamlit client
- Multimodal image upload for boarding passes, baggage photos, and documents
- Deterministic local fallback when `GROQ_API_KEY` is not configured

## Tech Stack
- Flask API
- LangChain + Groq tool calling
- Streamlit UI
- Python

## Run Locally
pip install -r requirements.txt
Add GROQ_API_KEY to .env
python app.py

# In another terminal
streamlit run streamlit_app.py

The backend exposes `GET /health` and `POST /chat`. Set `GROQ_MODEL` if a
different Groq model is available for multimodal input. Without a key, the API
still runs with local intent routing and database-backed fare lookup.
