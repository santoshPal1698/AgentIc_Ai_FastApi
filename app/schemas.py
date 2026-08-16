from pydantic import BaseModel
from typing import List, Literal


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    # Matches: const { messages } = req.body;
    messages: List[ChatMessage]


class ChatResponse(BaseModel):
    reply: str


class GoogleAIRequest(BaseModel):
    # Matches: const { question } = req.body;
    question: str
