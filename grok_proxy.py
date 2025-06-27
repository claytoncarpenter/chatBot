from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from langchain_xai import ChatXAI
import os

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

@app.post("/api/grok")
async def grok_proxy(request: Request):
    body = await request.json()
    messages = body.get("messages", [])
    # model.invoke expects a list of messages
    result = model.invoke(messages)
    return {"choices": [{"message": {"content": result}}]}
