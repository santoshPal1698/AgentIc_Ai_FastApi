from dotenv import load_dotenv
from fastapi import FastAPI

from app.routers.ai_routes import router as ai_router

load_dotenv()  # loads OPENROUTEAIKEY / CHAT_API_KEY from .env

app = FastAPI(title="AI Portfolio API")

# Mirrors: router.use("/api/ai", aiRoutes) or similar in your Express index.js
app.include_router(ai_router, prefix="/api/v1", tags=["AI"])


@app.get("/")
def root():
    return {"status": "Api is Success for Agentic Ai ok"}
