from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from langchain_xai import ChatXAI
import os
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

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


from typing import Optional

from pydantic import BaseModel, Field


class Car(BaseModel):
    """Information about a person."""

    # ^ Doc-string for the entity Person.
    # This doc-string is sent to the LLM as the description of the schema Person,
    # and it can help to improve extraction results.

    # Note that:
    # 1. Each field is an `optional` -- this allows the model to decline to extract it!
    # 2. Each field has a `description` -- this description is used by the LLM.
    # Having a good description can help improve extraction results.
    brand: Optional[str] = Field(default=None, description="The make or brand of the car")
    color: Optional[str] = Field(
        default=None, description="The color of the car"
    )
    bodyType: Optional[str] = Field(
        default=None, description="The type of the car, e.g., sedan, SUV, etc."
    )


prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert extraction algorithm. "
            "Only extract relevant information from the text. "
            "If you do not know the value of an attribute asked to extract, "
            "return null for the attribute's value.",
        ),
        # Please see the how-to about improving performance with
        # reference examples.
        # MessagesPlaceholder('examples'),
        ("human", "{text}"),
    ]
)

structured_llm = model.with_structured_output(schema=Car)

@app.post("/api/grok")
async def grok_proxy(request: Request):
    body = await request.json()
    messages = body.get("messages", [])
    #print(f"Received messages: {messages[-1]['content']}")
    # model.invoke expects a list of messages
    prompt = prompt_template.invoke({"text": messages[-1]['content']})
    print(prompt)
    result = structured_llm.invoke(prompt)
    print(f"Result: {str(result)}")
    return {"choices": [{"message": {"content": str(result)}}]}
