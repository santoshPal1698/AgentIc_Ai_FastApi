from typing import List, Literal,Optional
from pydantic import BaseModel, EmailStr, field_validator
from app.config import MAX_DELAY_SECONDS, MAX_DAILY_LIMIT

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



class RegisterRequest(BaseModel):
    email: EmailStr

class RegisterResponse(BaseModel):
    user_id: str
    api_key: str
    note: str = "Save this API key now — it will not be shown again."


class TemplateRequest(BaseModel):
    """Fully dynamic — every developer writes their own subject/body.
    Supported placeholders: {hr_name} {company} {role} {your_name}
    {your_phone} {your_linkedin}
    """
    subject: str
    body: str


class SMTPConfig(BaseModel):
    """Works with any provider — Gmail, Outlook, Zoho, a company SMTP relay,
    etc. Credentials are used once to log in and are never persisted."""
    smtp_host: str
    smtp_port: int = 465
    use_ssl: bool = True
    smtp_user: str
    smtp_password: str


class CampaignRequest(BaseModel):
    smtp: SMTPConfig
    your_name: str
    your_role: str
    your_phone: str = ""
    your_linkedin: str = ""
    delay_seconds: int = 20
    daily_limit: int = 450

    @field_validator("delay_seconds")
    @classmethod
    def enforce_min_delay(cls, v):
        if v < MAX_DELAY_SECONDS:
            raise ValueError(f"delay_seconds must be >= {MAX_DELAY_SECONDS} to avoid provider spam blocks.")
        return v

    @field_validator("daily_limit")
    @classmethod
    def enforce_max_limit(cls, v):
        if v > MAX_DAILY_LIMIT:
            raise ValueError(f"daily_limit cannot exceed {MAX_DAILY_LIMIT}.")
        return v


class CampaignStatus(BaseModel):
    id: str
    status: str
    sent: int
    failed: int
    total: int
    last_error: Optional[str]
    created_at: str
    finished_at: Optional[str]
