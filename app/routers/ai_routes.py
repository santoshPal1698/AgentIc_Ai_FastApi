from fastapi import APIRouter

from app.controllers.ai_controller import chat_bot_controller, google_ai_controller
from app.schemas import ChatRequest, ChatResponse, GoogleAIRequest

# All AI Routes Declared here
router = APIRouter()


@router.post("/ai-chatBoat", response_model=ChatResponse)
async def ai_chat_boat(body: ChatRequest):
    return await chat_bot_controller(body)


@router.post("/google-api")
async def google_api(body: GoogleAIRequest):
    return await google_ai_controller(body)
