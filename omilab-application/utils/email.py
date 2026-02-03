# utils/email.py
import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from dotenv import load_dotenv

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_USERNAME"),
    MAIL_PORT=2525,
    MAIL_SERVER="smtp-relay.brevo.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

async def send_confirmation_code(email: EmailStr, code: str):
    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
        <div style="max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; text-align: center;">
            <h2 style="color: #333;">OmiLab ID</h2>
            <p style="color: #666;">Ваш код подтверждения:</p>
            <h1 style="color: #ff3b30; font-size: 32px; letter-spacing: 5px;">{code}</h1>
            <p style="font-size: 12px; color: #999;">Никому не сообщайте этот код.</p>
        </div>
    </div>
    """

    message = MessageSchema(
        subject="OmiLab: Код подтверждения",
        recipients=[email],
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)