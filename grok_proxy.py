from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from langchain_xai import ChatXAI

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

model = ChatXAI(
    model="grok-3-mini",
    api_key="xai-jdJtcE72wGZHTKvhzB6Yl9nDRiNWcAiYFP0cQNVreh0Bcz2j2D5UKuqb8lk129xrOzVICUlgO1CuAdM1"
)

@app.post("/api/grok")
async def grok_proxy(request: Request):
    body = await request.json()
    messages = body.get("messages", [])
    # model.invoke expects a list of messages
    result = model.invoke(messages)
    return {"choices": [{"message": {"content": result}}]}