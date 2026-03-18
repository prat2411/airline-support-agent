import os
import requests
import json
from openai import OpenAI
from dotenv import load_dotenv
from langchain_groq import ChatGroq
import gradio as gr
import sqlite3

load_dotenv(override=True)
groq_api_key = os.getenv('GROQ_API_KEY')
if groq_api_key:
    print(f"Groq API Key exists and begins {groq_api_key[:4]}")

openai = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)


system_message = """
You are FlightAI's airline assistant.

When a user asks for a ticket price:
- You MUST call the get_ticket_price function.
- Do NOT tell the user to call the API.
- Do NOT explain the function.
- Return the function result as the final answer.

Respond in one short sentence.
"""
DB = "prices.db"
conn = sqlite3.connect(DB)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS prices (city TEXT PRIMARY KEY, price REAL)')
cursor.execute("INSERT OR IGNORE INTO prices VALUES ('london', 650)")
cursor.execute("INSERT OR IGNORE INTO prices VALUES ('paris', 750)")
cursor.execute("INSERT OR IGNORE INTO prices VALUES ('tokyo', 1200)")
cursor.execute("INSERT OR IGNORE INTO prices VALUES ('sydney', 1500)")
cursor.execute("INSERT OR IGNORE INTO prices VALUES ('new york', 1000)")
cursor.execute("INSERT OR IGNORE INTO prices VALUES ('dubai', 1300)")
cursor.execute("INSERT OR IGNORE INTO prices VALUES ('singapore', 1400)")
cursor.execute("INSERT OR IGNORE INTO prices VALUES ('barcelona', 800)")
conn.commit()
conn.close()


MODEL = "llama-3.1-8b-instant"

def get_ticket_price(city):
    print(f"DATABASE TOOL CALLED: Getting price for {city}", flush=True)
    if not city:
            return "No city provided"
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT price FROM prices WHERE city = ?', (city.lower(),))
        #cursor.execute('SELECT price FROM prices WHERE city = ?', (city.lower(),))
        result = cursor.fetchone()
        return f"Ticket price to {city} is ${result[0]}" if result else "No price data available for this city"


price_function = {
    "name": "get_ticket_price",
    "description": "Use this function to retrieve the ticket price for a destination city from the airline database. Always call this function when a user asks for a ticket price.",
    "parameters": {
        "type": "object",
        "properties": {
            "destination_city": {
                "type": "string",
                "description": "The city that the customer wants to travel to",
            },
        },
        "required": ["destination_city"],
        "additionalProperties": False
    }
}
tools = [{"type": "function", "function": price_function}]
tools

def chat(message, history):
    history = [{"role":h["role"], "content":h["content"]} for h in history]
    messages = [{"role": "system", "content": system_message}] + history + [{"role": "user", "content": message}]
    response = openai.chat.completions.create(model=MODEL, messages=messages, tools=tools, tool_choice="auto")

    max_tool_calls = 3
    tool_count = 0
    while response.choices[0].finish_reason=="tool_calls" and tool_count < max_tool_calls:
        message = response.choices[0].message
        responses = handle_tool_calls(message)

        messages.append(message)
        messages.extend(responses)
        response = openai.chat.completions.create(
                    model=MODEL,
                     messages=messages, 
                     tools=tools,
                     tool_choice="auto")
        tool_count += 1
    
    return response.choices[0].message.content

def handle_tool_calls(message):
    responses = []
    for tool_call in message.tool_calls:
        if tool_call.function.name != "get_ticket_price":
            continue
        arguments = json.loads(tool_call.function.arguments)
        city = arguments.get('destination_city')
        price_details = get_ticket_price(city)
        responses.append({
            "role": "tool",
            "content": price_details,
           "tool_call_id": tool_call.id
            })
    return responses

gr.ChatInterface(fn=chat).launch(server_name="0.0.0.0", server_port=7860)
