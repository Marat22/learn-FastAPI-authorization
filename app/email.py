import os
import smtplib
from email.mime.text import MIMEText

from dotenv import load_dotenv
from pydantic import EmailStr

load_dotenv()
MAIL = os.getenv("MAIL")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER")

if not all((MAIL, MAIL_PASSWORD, SMTP_SERVER)):
    raise Exception(
        f"SET ALL .env variables: {MAIL=}, {MAIL_PASSWORD=}, {SMTP_SERVER=}"
    )


def send_update_password_email(email: EmailStr, reset_url: str):
    msg = MIMEText(f"""Click the link to reset your password: {reset_url}

    This link will expire in 15 minutes.""")

    msg["Subject"] = "Password Reset Request"
    msg["From"] = MAIL
    msg["To"] = email

    with smtplib.SMTP_SSL(SMTP_SERVER, 465) as server:
        server.login(MAIL.split("@")[0], MAIL_PASSWORD)
        server.sendmail(MAIL, [str(email)], msg.as_string())


def send_confirmation_email(email: EmailStr, token_url: str):
    msg = MIMEText(f"Click the link to confirm your email: {token_url}")
    msg["Subject"] = "Confirm your email"
    msg["From"] = MAIL
    msg["To"] = email

    with smtplib.SMTP_SSL(SMTP_SERVER, 465) as server:
        server.login(MAIL.split("@")[0], MAIL_PASSWORD)
        server.sendmail(MAIL, [str(email)], msg.as_string())
