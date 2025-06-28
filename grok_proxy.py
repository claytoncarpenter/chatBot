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


class SAR(BaseModel):
    """Information about a person."""

    # ^ Doc-string for the entity Person.
    # This doc-string is sent to the LLM as the description of the schema Person,
    # and it can help to improve extraction results.

    # Note that:
    # 1. Each field is an `optional` -- this allows the model to decline to extract it!
    # 2. Each field has a `description` -- this description is used by the LLM.
    # Having a good description can help improve extraction results.
    activityType: Optional[str] = Field(default=None, description="The type of money laundering activity: e.g., structuring, placement, layering, smurfing etc.")
    accounts: Optional[list[str]] = Field(
        default=None, description="The accounts involved in the activity"
    )
    amount: Optional[list[str]] = Field(
        default=None, description="The total dollar amount involved in the activity"
    )
    narrative: Optional[str] = Field(
        default=None, description="The narrative description of the activity written to make a SAR (Suspicious Activity Report) to the authorities."
    )


prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert extraction algorithm and SAR (Suspicious Activity Report) writer."
            "Only extract relevant information from the text."
            "Write a SAR narrative based on the facts of the case."
            "If you do not know the value of an attribute asked to extract, "
            "return null for the attribute's value.",
        ),
        # Please see the how-to about improving performance with
        # reference examples.
        # MessagesPlaceholder('examples'),
        ("human", "{text}"),
    ]
)

structured_llm = model.with_structured_output(schema=SAR)

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
