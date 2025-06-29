from unittest import result
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import psycopg2
import csv
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing import Annotated


os.environ["LANGCHAIN_TRACING_V2"] = "true"
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

llm = init_chat_model("openai:gpt-4.1")

@tool
def get_transactions(customer_id: str = None) -> list:
    """Returns all bank transactions as a list of dicts. Optionally filter by customer_id."""
    print("get_transactions tool called with:", customer_id)
    
    conn = psycopg2.connect(
        dbname="sarbotdb",
        user="sarbotdb_owner",
        password=os.getenv("NEON_PASS"),
        host=os.getenv("NEON_URL"),
        port=os.getenv("DB_PORT", "5432"),
        sslmode="require"
    )
    query = "SELECT * FROM public.transactions"
    cursor = conn.cursor()
    cursor.execute(query)
    transactions = cursor.fetchall()
    cursor.close()
    conn.close()
    return transactions

tools = [get_transactions]
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)
# Any time a tool is called, we return to the chatbot to decide the next step
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")
graph = graph_builder.compile()

@app.post("/api/grok")
async def grok_proxy(request: Request):
    # Add a system prompt at the start of the conversation
    system_prompt = {
        "role": "system",
        "content": (
            "You are a Suspicious Activity Report (SAR) writer at Claytons Bank. "
            "You can look up bank transactions using the get_transactions tool. "
            "When a user asks about transactions or suspicious activity, use the tool to find relevant data, "
            "then write a clear and concise SAR based on your findings."
            "You do not escalate any findings, you simply respond with a SAR for the activity."
            "After you write the SAR, your task is complete and you should not take any further action or call any tools."
        )
    }

    body = await request.json()
    messages = body.get("messages", [])
    if not messages or messages[0].get("role") != "system":
        messages = [system_prompt] + messages

    #print(messages)
    # Now use the compiled graph to invoke
    result = graph.invoke({"messages": messages})
    print(result['messages'][-1])

    last_message = result['messages'][-1]
    return {
        "choices": [
            {
                "message": {
                    "content": last_message.content
                }
            }
        ]
    }
