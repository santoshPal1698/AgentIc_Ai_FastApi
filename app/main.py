"""
Production Bulk Resume/Email Sender API — fully dynamic, multi-developer.

Nothing is hardcoded:
- No email address, SMTP provider, password, resume, or template lives in
  the code. Every developer registers, gets an API key, and supplies their
  own resume, template, contact list, and SMTP credentials at call time.
- SMTP credentials are used once per campaign to log in, then discarded —
  never written to disk or the database.

Run:
    uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

import uuid
import threading
import os
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from app import database as db
from app.auth import require_user
from app.config import DATA_DIR
from app.schemas import (
    RegisterRequest, RegisterResponse, TemplateRequest,
    CampaignRequest, CampaignStatus,
)
from app.email_sender import run_campaign, load_contacts

from dotenv import load_dotenv
from app.routers.ai_routes import router as ai_router
load_dotenv()  # loads OPENROUTEAIKEY / CHAT_API_KEY from .env


app = FastAPI(title="Bulk Email Sender API & AI Portfolio API", version="3.0 (production)")

app.include_router(ai_router, prefix="/api/v1", tags=["AGentic Ai Api "])


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your actual frontend domain(s) in production
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    db.init_db()


def user_dir(user_id: str) -> str:
    path = os.path.join(DATA_DIR, user_id)
    os.makedirs(path, exist_ok=True)
    return path


def resume_path(user_id: str) -> str:
    return os.path.join(user_dir(user_id), "resume.pdf")


def contacts_path(user_id: str) -> str:
    return os.path.join(user_dir(user_id), "contacts.csv")


def campaign_log_path(user_id: str, campaign_id: str) -> str:
    return os.path.join(user_dir(user_id), f"campaign_{campaign_id}.log")


# ---------------- Auth / onboarding ----------------
@app.post("/auth/register", response_model=RegisterResponse)
def register(req: RegisterRequest):
    """Any developer can self-register to get their own API key.
    Example:
        curl -X POST localhost:8000/auth/register -H "Content-Type: application/json" \\
             -d '{"email": "you@example.com"}'
    """
    import sqlite3
    try:
        user_id, api_key = db.create_user(req.email)
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Email already registered.")
    return RegisterResponse(user_id=user_id, api_key=api_key)


# ---------------- Dynamic assets: resume, template, contacts ----------------
@app.post("/resume")
async def upload_resume(file: UploadFile = File(...), user=Depends(require_user)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Resume must be a PDF.")
    with open(resume_path(user["id"]), "wb") as f:
        f.write(await file.read())
    return {"message": "Resume uploaded."}


@app.post("/template")
def set_template(req: TemplateRequest, user=Depends(require_user)):
    """Fully custom subject/body — no fixed HR copy baked into the app.
    Use placeholders: {hr_name} {company} {role} {your_name} {your_phone} {your_linkedin}
    """
    db.upsert_template(user["id"], req.subject, req.body)
    return {"message": "Template saved."}


@app.post("/contacts")
async def upload_contacts(file: UploadFile = File(...), user=Depends(require_user)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Contacts file must be CSV (columns: name,email,company).")
    path = contacts_path(user["id"])
    with open(path, "wb") as f:
        f.write(await file.read())
    count = len(load_contacts(path))
    return {"message": "Contacts uploaded.", "count": count}


# ---------------- Campaigns ----------------
@app.post("/campaigns", response_model=CampaignStatus)
def start_campaign(req: CampaignRequest, user=Depends(require_user)):
    """Starts a background send using THIS user's own resume, template,
    contacts, and SMTP credentials (any provider — Gmail, Outlook, custom
    relay). Credentials are never stored."""
    user_id = user["id"]

    if not os.path.exists(resume_path(user_id)):
        raise HTTPException(400, "Upload a resume first via POST /resume.")
    if not os.path.exists(contacts_path(user_id)):
        raise HTTPException(400, "Upload contacts first via POST /contacts.")
    template = db.get_template(user_id)
    if not template:
        raise HTTPException(400, "Set a template first via POST /template.")

    campaign_id = str(uuid.uuid4())
    total = len(load_contacts(contacts_path(user_id)))
    db.create_campaign(campaign_id, user_id, total)

    thread = threading.Thread(
        target=run_campaign,
        args=(campaign_id, user_id, req, resume_path(user_id), contacts_path(user_id),
              template["subject"], template["body"], campaign_log_path(user_id, campaign_id)),
        daemon=True,
    )
    thread.start()

    row = db.get_campaign(campaign_id, user_id)
    return CampaignStatus(**dict(row))


@app.get("/campaigns/{campaign_id}", response_model=CampaignStatus)
def get_campaign(campaign_id: str, user=Depends(require_user)):
    row = db.get_campaign(campaign_id, user["id"])
    if not row:
        raise HTTPException(404, "Campaign not found.")
    return CampaignStatus(**dict(row))


@app.get("/campaigns", response_model=list[CampaignStatus])
def list_campaigns(user=Depends(require_user)):
    rows = db.list_campaigns(user["id"])
    return [CampaignStatus(**dict(r)) for r in rows]


@app.get("/")
def root():
    return {"status": "Api is Success for Agentic Ai ok"}
