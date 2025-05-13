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
    """Отправляет письмо со ссылкой для сброса пароля пользователя.

    Args:
        email (EmailStr): Адрес электронной почты пользователя.
        reset_url (str): URL для сброса пароля.
    """
    msg = MIMEText(f"""Нажмите на ссылку, чтобы сбросить ваш пароль: {reset_url}

    Эта ссылка истечет через 15 минут.""")

    msg["Subject"] = "Запрос на сброс пароля"
    msg["From"] = MAIL
    msg["To"] = email

    with smtplib.SMTP_SSL(SMTP_SERVER, 465) as server:
        server.login(MAIL.split("@")[0], MAIL_PASSWORD)
        server.sendmail(MAIL, [str(email)], msg.as_string())

def send_confirmation_email(email: EmailStr, token_url: str):
    """Отправляет письмо со ссылкой для подтверждения электронной почты пользователя.

    Args:
        email (EmailStr): Адрес электронной почты пользователя.
        token_url (str): URL для подтверждения электронной почты.
    """
    msg = MIMEText(f"Нажмите на ссылку, чтобы подтвердить вашу электронную почту: {token_url}")
    msg["Subject"] = "Подтвердите вашу электронную почту"
    msg["From"] = MAIL
    msg["To"] = email

    with smtplib.SMTP_SSL(SMTP_SERVER, 465) as server:
        server.login(MAIL.split("@")[0], MAIL_PASSWORD)
        server.sendmail(MAIL, [str(email)], msg.as_string())
