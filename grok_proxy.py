from unittest import result
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from langchain_xai import ChatXAI
from langchain_openai import ChatOpenAI
import os
import csv
import json
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langgraph.graph import MessageGraph
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
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
def get_deposits(customer_id: str = None) -> list:
    """Returns all bank deposits as a list of dicts. Optionally filter by customer_id."""
    print("get_deposits tool called with:", customer_id)
    with open("src/assets/Deposits.csv", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        deposits = list(reader)
    if customer_id:
        deposits = [d for d in deposits if d.get("CustomerID") == customer_id]
    return deposits

tools = [get_deposits]
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
            "You can look up bank transactions using the get_deposits tool. "
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
