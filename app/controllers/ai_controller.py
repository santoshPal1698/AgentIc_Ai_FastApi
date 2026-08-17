import os
import httpx
from fastapi import HTTPException
# from app.schemas import ChatRequest, ChatResponse, GoogleAIRequest
from app.services.ai_services import generate_from_google, get_resume_text, get_system_prompt

from app.schemas import ChatRequest, ChatResponse, GoogleAIRequest


async def chat_bot_controller(body: ChatRequest) -> ChatResponse:
    """Equivalent of chatBotController in ai.controller.js"""
    resume_text = get_resume_text()
    print("Resume data",resume_text)
    if not resume_text:
        raise HTTPException(status_code=500, detail="Resume not loaded")

    try:
        system_prompt = get_system_prompt(resume_text)

        payload = {
            "model": "openrouter/free",
            "messages": [
                {"role": "system", "content": system_prompt},
                *[m.model_dump() for m in body.messages],
            ],
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {os.getenv('OPENROUTEAIKEY')}",
                },
                json=payload,
            )

        data = response.json()

        if response.status_code >= 400:
            error_message = (data.get("error") or {}).get("message", "API Error")
            raise HTTPException(status_code=500, detail=error_message)

        reply = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "No response")
        )
        return ChatResponse(reply=reply)

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def google_ai_controller(body: GoogleAIRequest):
    """Equivalent of googleAIController in ai.controller.js"""
    try:
        result = await generate_from_google(body.question)
        return result
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={"message": "Server Error", "error": str(error)},
        )
