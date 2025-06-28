from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from langchain_xai import ChatXAI
import os
import csv
import json
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langgraph.graph import MessageGraph
from langgraph.prebuilt import ToolNode
os.environ["LANGCHAIN_TRACING_V2"] = "true"
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

model = ChatXAI(
    model="grok-3-mini",
    api_key=os.getenv("XAI_API_KEY")
)

modelOpenAI = init_chat_model("openai:gpt-4.1")

@tool
def getDeposits(CustomerID: str = None, **kwargs) -> list:
    """Returns all bank deposits as a list of dicts. Optionally filter by CustomerID."""
    print("Fetching deposits...")
    with open("C:/Users/clayt/astro/wandering-wavelength/src/assets/Deposits.csv", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        deposits = list(reader)
    if CustomerID:
        deposits = [d for d in deposits if d.get("CustomerID") == CustomerID]
    return deposits
    

tools = [getDeposits]

# Build the LangGraph
graph = MessageGraph()
graph.add_node("llm", model)
graph.add_node("tools", ToolNode(tools))
graph.add_edge("llm", "tools")
graph.add_edge("tools", "llm")
graph.set_entry_point("llm")
graph.set_finish_point("llm")

# Compile the graph to get a runnable object
compiled_graph = graph.compile()

@app.post("/api/grok")
async def grok_proxy(request: Request):
    body = await request.json()
    messages = body.get("messages", [])

    # Add a system prompt at the start of the conversation
    system_prompt = {
        "role": "system",
        "content": (
            "You are a Suspicious Activity Report (SAR) writer at Claytons Bank. "
            "You can look up bank transactions using the getDeposits tool. "
            "When a user asks about transactions or suspicious activity, use the tool to find relevant data, "
            "then write a clear and concise SAR based on your findings."
        )
    }

    # Only keep the system prompt and the latest user message
    user_message = next((m for m in reversed(messages) if m.get("role") == "user"), None)
    if user_message:
        messages = [system_prompt, user_message]
    else:
        messages = [system_prompt]

    # Now use the compiled graph to invoke
    result = compiled_graph.invoke(messages)
    print(result)
    # The result is a list of messages; return the last one as the assistant's reply
    return result