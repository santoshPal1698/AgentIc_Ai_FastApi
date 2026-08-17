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




# Bulk Resume / Email Sender API (Production)

Fully dynamic multi-developer service — **nothing is hardcoded**:
- No developer's email, SMTP password, resume, or message template lives in the code.
- Each developer registers, gets their own API key, and supplies their own resume,
  template, contact list, and SMTP credentials at call time.
- SMTP credentials are used once to log in for a campaign, then discarded — never
  written to disk or the database.

## Setup

```bash
cp .env.example .env
# edit .env, set APP_SECRET_KEY (e.g. `openssl rand -hex 32`)

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open http://127.0.0.1:8000/docs for the interactive API.

## Usage flow (any developer)

1. **Register** — get your API key (shown once, save it):
   ```bash
   curl -X POST localhost:8000/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"you@example.com"}'
   ```

2. **Set your own template** (placeholders: `{hr_name} {company} {role} {your_name} {your_phone} {your_linkedin}`):
   ```bash
   curl -X POST localhost:8000/template \
     -H "X-API-Key: YOUR_KEY" -H "Content-Type: application/json" \
     -d '{"subject":"Application for {role} - {your_name}",
          "body":"Hi {hr_name}, I'\''d love to join {company} as a {role}...\n\n{your_name}\n{your_phone}"}'
   ```

3. **Upload your resume:**
   ```bash
   curl -X POST localhost:8000/resume -H "X-API-Key: YOUR_KEY" -F "file=@resume.pdf"
   ```

4. **Upload contacts** (CSV columns: `name,email,company`):
   ```bash
   curl -X POST localhost:8000/contacts -H "X-API-Key: YOUR_KEY" -F "file=@contacts.csv"
   ```

5. **Start a campaign** with your own SMTP provider (Gmail, Outlook, company relay — any):
   ```bash
   curl -X POST localhost:8000/campaigns \
     -H "X-API-Key: YOUR_KEY" -H "Content-Type: application/json" \
     -d '{
       "smtp": {"smtp_host":"smtp.gmail.com","smtp_port":465,"use_ssl":true,
                "smtp_user":"you@gmail.com","smtp_password":"app-password"},
       "your_name":"Your Name","your_role":"Agentic AI Engineer",
       "your_phone":"+91-XXXXXXXXXX","your_linkedin":"https://linkedin.com/in/you",
       "delay_seconds":20,"daily_limit":450
     }'
   ```

6. **Poll status:**
   ```bash
   curl localhost:8000/campaigns/CAMPAIGN_ID -H "X-API-Key: YOUR_KEY"
   ```

## Gmail / Outlook App Passwords

- **Gmail:** enable 2-Step Verification → Google Account → Security → App Passwords.
  Host: `smtp.gmail.com`, port `465`, `use_ssl: true`.
- **Outlook:** enable 2FA → Security → App Passwords.
  Host: `smtp.office365.com`, port `587`, `use_ssl: false` (uses STARTTLS).

## Deploy

```bash
docker build -t bulk-resume-api .
docker run -d -p 8000:8000 \
  -e APP_SECRET_KEY=$(openssl rand -hex 32) \
  -v $(pwd)/data:/app/data \
  bulk-resume-api
```

## Production hardening notes

- **HTTPS required** — SMTP passwords travel in request bodies; never run this over plain HTTP outside localhost.
- CORS is wide open (`*`) by default in `app/main.py` — restrict `allow_origins` to your real frontend domain(s).
- Rate limits (`delay_seconds` ≥ `MAX_DELAY_SECONDS`, `daily_limit` ≤ `MAX_DAILY_LIMIT`) are enforced server-side via `.env` — a misbehaving client can't blast past them.
- Campaign status lives in SQLite and background threads — fine for a single-instance deploy. For multi-instance/horizontal scaling, swap the threading approach for Celery/RQ with Redis so jobs survive process restarts and run across workers.
- API keys are stored hashed (SHA-256), never in plaintext — treat them like passwords; there's no key-recovery, only re-registration with a new email.

