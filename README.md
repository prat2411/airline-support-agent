---
title: Airline Customer Support Agent
emoji: ✈️
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: "4.44.0"
app_file: app.py
pinned: false
---

# ✈️ Airline Customer Support Agent

A multimodal AI customer support agent for an airline — handles 
flight queries, bookings, and refund requests via natural language.

## Live Demo
Try it above ☝️

## Features
- Natural language flight query handling
- Function calling for real tool invocation
- Multi-turn conversation with memory
- Booking, refund, and complaint handling

## Tech Stack
- LangChain + Function Calling
- Groq Llama3 (free API)
- Gradio UI
- Python

## Run Locally
pip install -r requirements.txt
Add GROQ_API_KEY to .env
python app.py