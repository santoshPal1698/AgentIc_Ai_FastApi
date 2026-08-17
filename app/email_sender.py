import csv
import time
import smtplib
import logging
from email.message import EmailMessage

from app import database as db
from app.schemas import CampaignRequest


def load_contacts(path: str):
    contacts = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("email"):
                contacts.append(row)
    return contacts


def render(template: str, hr_name, company, cfg: CampaignRequest) -> str:
    return template.format(
        hr_name=hr_name or "there",
        company=company or "your company",
        role=cfg.your_role,
        your_name=cfg.your_name,
        your_phone=cfg.your_phone,
        your_linkedin=cfg.your_linkedin,
    )


def build_message(cfg: CampaignRequest, subject_tmpl: str, body_tmpl: str,
                   resume_path: str, hr_email: str, hr_name: str, company: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = render(subject_tmpl, hr_name, company, cfg)
    msg["From"] = cfg.smtp.smtp_user
    msg["To"] = hr_email
    msg.set_content(render(body_tmpl, hr_name, company, cfg))

    with open(resume_path, "rb") as f:
        data = f.read()
    msg.add_attachment(data, maintype="application", subtype="pdf",
                        filename=resume_path.split("/")[-1])
    return msg


def run_campaign(campaign_id: str, user_id: str, cfg: CampaignRequest,
                  resume_path: str, contacts_path: str, subject_tmpl: str, body_tmpl: str,
                  log_file: str):
    """Runs in a background thread. `cfg` (which holds the SMTP password)
    goes out of scope and is garbage-collected once this function returns —
    it is never written to the database."""
    logger = logging.getLogger(campaign_id)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_file)
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    logger.addHandler(handler)

    contacts = load_contacts(contacts_path)
    sent, failed = 0, 0

    smtp_cls = smtplib.SMTP_SSL if cfg.smtp.use_ssl else smtplib.SMTP

    try:
        with smtp_cls(cfg.smtp.smtp_host, cfg.smtp.smtp_port) as server:
            if not cfg.smtp.use_ssl:
                server.starttls()
            server.login(cfg.smtp.smtp_user, cfg.smtp.smtp_password)

            for contact in contacts:
                if sent >= cfg.daily_limit:
                    break
                hr_email = contact["email"].strip()
                hr_name = contact.get("name", "").strip()
                company = contact.get("company", "").strip()
                try:
                    msg = build_message(cfg, subject_tmpl, body_tmpl, resume_path,
                                         hr_email, hr_name, company)
                    server.send_message(msg)
                    sent += 1
                    logger.info(f"SENT to {hr_email} ({company})")
                except Exception as e:
                    failed += 1
                    logger.error(f"FAILED to {hr_email}: {e}")
                db.update_campaign_progress(campaign_id, sent=sent, failed=failed)
                time.sleep(cfg.delay_seconds)

        db.update_campaign_progress(campaign_id, status="completed", finished=True)

    except smtplib.SMTPAuthenticationError:
        db.update_campaign_progress(
            campaign_id, status="failed",
            last_error="SMTP login failed — check host/port/username/password (use an App Password for Gmail/Outlook).",
            finished=True,
        )
    except Exception as e:
        logger.error(f"CAMPAIGN ERROR: {e}")
        db.update_campaign_progress(campaign_id, status="failed", last_error=str(e), finished=True)
