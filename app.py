"""Flask API for the multimodal airline support agent."""

import base64
import os
import re
import sqlite3
from typing import Any

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq

load_dotenv(override=True)

app = Flask(__name__)
DB = os.path.join(os.path.dirname(__file__), "prices.db")
MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
MAX_HISTORY = 20

INTENTS = {
    "ticket_price": ("price", "cost", "fare", "how much"),
    "booking": ("book", "booking", "reserve", "reservation"),
    "flight_status": ("status", "delayed", "delay", "on time", "cancelled"),
    "baggage_policy": ("baggage policy", "luggage allowance", "carry-on", "checked bag"),
    "cancellation": ("cancel", "cancellation"),
    "refund": ("refund", "money back", "reimburse"),
    "change_flight": ("change flight", "reschedule", "change my flight"),
    "check_in": ("check in", "check-in", "boarding pass"),
    "lost_baggage": ("lost baggage", "missing luggage", "luggage is missing", "bag did not arrive", "bag is missing", "baggage is missing"),
    "complaint": ("complaint", "complain", "unhappy", "terrible service"),
    "accessibility": ("wheelchair", "accessible", "special assistance"),
    "other": (),
}


def _init_db() -> None:
    prices = {"london": 650, "paris": 750, "tokyo": 1200, "sydney": 1500,
              "new york": 1000, "dubai": 1300, "singapore": 1400, "barcelona": 800}
    with sqlite3.connect(DB) as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS prices (city TEXT PRIMARY KEY, price REAL)")
        connection.executemany("INSERT OR IGNORE INTO prices VALUES (?, ?)", prices.items())


@tool
def get_ticket_price(destination_city: str) -> str:
    """Retrieve the ticket price for a destination city from the airline database."""
    with sqlite3.connect(DB) as connection:
        result = connection.execute(
            "SELECT price FROM prices WHERE city = ?", (destination_city.strip().lower(),)
        ).fetchone()
    return (f"The current ticket price to {destination_city.title()} is ${result[0]:.0f}."
            if result else f"I do not have a fare listed for {destination_city.title()} yet.")


@tool
def create_support_case(intent: str, summary: str) -> str:
    """Create a support case for refunds, complaints, lost bags, or accessibility requests."""
    return f"I opened a {intent.replace('_', ' ')} support case. Reference: AS-{abs(hash(summary)) % 100000:05d}."


TOOLS = [get_ticket_price, create_support_case]
_init_db()


def detect_intent(message: str) -> str:
    text = message.lower()
    for intent, keywords in INTENTS.items():
        if any(keyword in text for keyword in keywords):
            return intent
    return "other"


def _destination(message: str) -> str | None:
    match = re.search(r"(?:to|for|in)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)", message, re.I)
    return match.group(1).strip() if match else None


def fallback_response(message: str, image_name: str | None = None) -> tuple[str, str, list[str]]:
    intent = detect_intent(message)
    if intent == "ticket_price":
        city = _destination(message)
        return (get_ticket_price.invoke({"destination_city": city}) if city else
                "Which destination city should I price for?", intent, ["get_ticket_price"] if city else [])
    if intent in {"refund", "complaint", "lost_baggage", "accessibility"}:
        return create_support_case.invoke({"intent": intent, "summary": message}), intent, ["create_support_case"]
    responses = {
        "booking": "I can help arrange a booking. Please share your origin, destination, travel date, and passenger count.",
        "flight_status": "Please share your flight number and travel date so I can check its status.",
        "baggage_policy": "You can bring one cabin bag and one personal item; checked allowance depends on your fare.",
        "cancellation": "I can explain cancellation options. Please share your booking reference.",
        "change_flight": "I can help reschedule your flight. Please share your booking reference and preferred date.",
        "check_in": "Online check-in opens 24 hours before departure. Please share your flight number if you need help.",
        "other": "I can help with bookings, fares, flight status, baggage, refunds, changes, check-in, and complaints. What do you need?",
    }
    suffix = f" I received the image {image_name}." if image_name else ""
    return responses[intent] + suffix, intent, []


def _history_messages(history: list[dict[str, Any]]) -> list[HumanMessage]:
    messages = []
    for item in history[-MAX_HISTORY:]:
        content = item.get("content", "")
        if item.get("role") in {"user", "human"}:
            messages.append(HumanMessage(content=content))
        elif item.get("role") in {"assistant", "ai"}:
            messages.append(AIMessage(content=content))
    return messages


def answer(message: str, history: list[dict[str, Any]] | None = None,
           image: dict[str, str] | None = None) -> dict[str, Any]:
    history = history or []
    image_name = image.get("name") if image else None
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        text, intent, called_tools = fallback_response(message, image_name)
        return {"answer": text, "intent": intent, "tools_called": called_tools, "fallback": True}

    try:
        model = ChatGroq(model=MODEL, temperature=0, groq_api_key=api_key).bind_tools(TOOLS)
        content: Any = message
        if image and image.get("data"):
            content = [{"type": "text", "text": message}, {"type": "image_url",
                       "image_url": {"url": f"data:{image.get('mime', 'image/jpeg')};base64,{image['data']}"}}]
        messages = [SystemMessage(content=("You are a concise airline support agent. Use tools when useful. "
                                            "Handle bookings, refunds, complaints, and 12 intents with empathy."))]
        messages.extend(_history_messages(history))
        messages.append(HumanMessage(content=content))
        called_tools = []
        response = model.invoke(messages)
        for call in getattr(response, "tool_calls", []):
            called_tools.append(call["name"])
            selected_tool = next((candidate for candidate in TOOLS if candidate.name == call["name"]), None)
            if selected_tool:
                messages.append(response)
                messages.append(ToolMessage(content=str(selected_tool.invoke(call["args"])), tool_call_id=call["id"]))
        if called_tools:
            response = model.invoke(messages)
        text = response.content if isinstance(response.content, str) else str(response.content)
        return {"answer": text, "intent": detect_intent(message), "tools_called": called_tools, "fallback": False}
    except Exception:
        text, intent, called_tools = fallback_response(message, image_name)
        return {"answer": text, "intent": intent, "tools_called": called_tools, "fallback": True}


@app.get("/health")
def health() -> Any:
    return jsonify({"status": "ok", "service": "airline-support-agent"})


@app.post("/chat")
def chat() -> Any:
    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message", "")).strip()
    if not message:
        return jsonify({"error": "message is required"}), 400
    image = payload.get("image")
    if image and image.get("data"):
        try:
            base64.b64decode(image["data"], validate=True)
        except Exception:
            return jsonify({"error": "image data must be valid base64"}), 400
    return jsonify(answer(message, payload.get("history", []), image))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
