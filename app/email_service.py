"""
email_service.py
----------------
Sends transactional emails using SMTP (works with Gmail, SendGrid, Mailtrap etc.)

Set these in .env:
  SMTP_HOST     = smtp.gmail.com
  SMTP_PORT     = 587
  SMTP_USER     = you@gmail.com
  SMTP_PASSWORD = your-app-password
  SMTP_FROM     = you@gmail.com
  BASE_URL      = http://localhost:8000
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", 587))
SMTP_USER     = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM     = os.getenv("SMTP_FROM", SMTP_USER)
BASE_URL      = os.getenv("BASE_URL", "http://localhost:8000")


def _send(to: str, subject: str, html: str):
    """Send an HTML email. Silently skips if SMTP is not configured."""
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"[EMAIL] SMTP not configured — would send '{subject}' to {to}")
        return
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = SMTP_FROM
    msg["To"]      = to
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM, to, msg.as_string())


def send_verification_email(to: str, token: str):
    link = f"{BASE_URL}/verify-email?token={token}"
    _send(to, "Verify your SecureShare email", f"""
    <div style="font-family:sans-serif;max-width:480px;margin:auto;padding:2rem">
      <h2 style="color:#7c6af7">SecureShare</h2>
      <p>Thanks for signing up! Click the button below to verify your email.</p>
      <a href="{link}" style="display:inline-block;padding:12px 24px;background:#7c6af7;color:#fff;border-radius:8px;text-decoration:none;font-weight:bold;margin:1rem 0">Verify Email</a>
      <p style="color:#888;font-size:12px">Or copy this link: {link}</p>
      <p style="color:#888;font-size:12px">This link expires in 24 hours.</p>
    </div>
    """)


def send_password_reset_email(to: str, token: str):
    link = f"{BASE_URL}/reset-password?token={token}"
    _send(to, "Reset your SecureShare password", f"""
    <div style="font-family:sans-serif;max-width:480px;margin:auto;padding:2rem">
      <h2 style="color:#7c6af7">SecureShare</h2>
      <p>You requested a password reset. Click below to set a new password.</p>
      <a href="{link}" style="display:inline-block;padding:12px 24px;background:#7c6af7;color:#fff;border-radius:8px;text-decoration:none;font-weight:bold;margin:1rem 0">Reset Password</a>
      <p style="color:#888;font-size:12px">Or copy this link: {link}</p>
      <p style="color:#888;font-size:12px">This link expires in 1 hour. If you didn't request this, ignore this email.</p>
    </div>
    """)
