from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import psycopg2
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing import Annotated
import json


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

from pydantic import BaseModel, Field
class ResponseFormatter(BaseModel):
    """Always use this tool to structure your response to the user."""
    customer_ids: list[str] = Field(description="A list of customer_ids associated with the suspicious activity")
    account_numbers: list[str] = Field(description="A list of account_numbers associated with the customer")
    transactions: str = Field(description="All transactions associated with the customer, including customer_id, account_number, transaction_date, amount, and credit_debit")
    amount: str = Field(description="The total amount of suspicious activity, formatted as a string with currency symbol")
    narrative: str = Field(description="A narrative of the suspicious activity")
    
model_with_structured_output = llm.with_structured_output(ResponseFormatter)

@tool
def get_transactions(customer_id: str = None) -> list:
    """Returns all bank transactions as a list of dicts. Optionally filter by customer_id.
    The table has columns in the following order: id, customer_id, account_number, transaction_date, amount, credit_debit"""
    print("get_transactions tool called with:", customer_id)
    
    conn = psycopg2.connect(
        dbname="sarbotdb",
        user="sarbotdb_owner",
        password=os.getenv("NEON_PASS"),
        host=os.getenv("NEON_URL"),
        port=os.getenv("DB_PORT", "5432"),
        sslmode="require"
    )
    if customer_id:
        query = f"SELECT * FROM public.transactions WHERE customer_id = {customer_id}"
    else:
        query = "SELECT * FROM public.transactions"
    cursor = conn.cursor()
    cursor.execute(query)
    transactions = cursor.fetchall()
    cursor.close()
    conn.close()
    return transactions

@tool(return_direct=True)
def respond(state: State = None) -> dict:
    """Structures the response to the user based on the transactions, narrative, and customer information."""
    print("respond tool called!")
    # Accept both dict with "messages" or just a list of messages
    if isinstance(state, dict) and "messages" in state:
        messages = state["messages"]
    elif isinstance(state, list):
        messages = state
    else:
        raise ValueError("Invalid state type for respond tool")
    response = model_with_structured_output.invoke(messages)
    if hasattr(response, "dict"):
        return response.model_dump()
    return response


tools = [get_transactions, respond]
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

graph_builder.add_node("chatbot", chatbot)

# Add respond as a tool node if not already
tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

# Add an edge from chatbot to tools (for tool calls)
graph_builder.add_conditional_edges("chatbot", tools_condition)

# Add an edge from tools to chatbot (for LLM to process tool output)
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
            "The get_transactions tool returns a list of transactions with the columns: id, customer_id, account_number, transaction_date, amount, credit_debit"
            "customer_id is a unique identifier for each customer, and account_number is a unique identifier for each bank account."
            "When a user asks about transactions or suspicious activity, use the tool to find relevant data, "
            "then write a clear and concise SAR based on your findings."
            "You do not escalate any findings, you simply respond with a SAR for the activity."
            "After you write the SAR, you call the respond tool and send the output to the end user."
        )
    }

    body = await request.json()
    messages = body.get("messages", [])
    if not messages or messages[0].get("role") != "system":
        messages = [system_prompt] + messages

    #print(messages)
    # Now use the compiled graph to invoke
    result = graph.invoke({"messages": messages})
    #print(result['messages'][-1])

    last_message = result['messages'][-2]
    

    # If the content is a string that looks like a dict, parse it
    try:
        content = last_message.content
        if isinstance(content, str) and content.startswith("{") and content.endswith("}"):
            content = eval(content)  # or use json.loads if it's valid JSON
    except Exception:
        pass

    
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps(content)
                }
            }
        ]
    }