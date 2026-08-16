# AI Portfolio API — FastAPI version

Converted from your Express/Node.js API (`ai.routes.js`, `ai.controller.js`, `ai.services.js`).

## Project structure

```
fastapi_project/
├── app/
│   ├── main.py                     # FastAPI app + router mounting
│   ├── schemas.py                  # Pydantic request/response models
│   ├── controllers/
│   │   └── ai_controller.py        # chat_bot_controller, google_ai_controller
│   ├── routers/
│   │   └── ai_routes.py            # POST /ai-chatBoat, POST /google-api
│   └── services/
│       └── ai_services.py          # Gemini call, resume PDF parsing, system prompt
├── uploads/
│   └── Ai_FullStack_Dev-2026.pdf   # <-- put your resume PDF here
├── requirements.txt
└── .env.example
```

## Step-by-step setup

1. **Create and activate a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Add your resume PDF**
   Place your resume file at:
   ```
   uploads/Ai_FullStack_Dev-2026.pdf
   ```
   (same filename/path your original Node code used — `../../uploads/...` relative to the services file).

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and fill in:
   ```
   OPENROUTEAIKEY=your_openrouter_api_key_here
   CHAT_API_KEY=your_google_genai_api_key_here
   ```

5. **Run the server**
   ```bash
   uvicorn app.main:app --reload --port 8000
   http://localhost:8000/api/v1/ai-chatBoat
   
   ```

6. **Test the endpoints**

   - Interactive docs (auto-generated, unlike Express): `http://localhost:8000/docs`

   - Chatbot endpoint:
     ```bash
     curl -X POST http://localhost:8000/api/ai/ai-chatBoat \
       -H "Content-Type: application/json" \
       -d '{"messages":[{"role":"user","content":"What projects has Santosh worked on?"}]}'
     ```

   - Gemini endpoint:
     ```bash
     curl -X POST http://localhost:8000/api/ai/google-api \
       -H "Content-Type: application/json" \
       -d '{"question":"What is Generative AI?"}'
     ```

## Notes on what changed vs. the Node version

- **Bug fix**: `getResumeText()` in the original JS parsed the PDF but never returned `data.text`, so the resume was always `undefined`. The Python `get_resume_text()` now actually returns the extracted text.
- **Bug fix**: the original controller called `getResumeText()` without `await` even though it's `async`. The Python version's `get_resume_text()` is synchronous (pypdf's `PdfReader` is sync), so this class of bug can't happen — but if you want it fully async/non-blocking, wrap the PDF read in `run_in_threadpool` or use `asyncio.to_thread`.
- **Validation is automatic**: Pydantic models (`ChatRequest`, `GoogleAIRequest`) replace the manual `if (!messages || !Array.isArray(messages))` checks — FastAPI returns a 422 automatically on bad input.
- **`fetch` → `httpx`**: Node's `node-fetch` call to OpenRouter is replaced with `httpx.AsyncClient`.
- Swagger/OpenAPI docs are generated for free at `/docs` and `/redoc`.
