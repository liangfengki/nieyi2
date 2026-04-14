from __future__ import annotations

import asyncio
import smtplib
import ssl
from email.message import EmailMessage

import httpx
from fastapi import HTTPException

from app.core.config import (
    APP_BRAND_NAME,
    BREVO_API_BASE_URL,
    BREVO_API_KEY,
    BREVO_SENDER_EMAIL,
    BREVO_SENDER_NAME,
    EMAIL_LOGIN_CODE_TTL_MINUTES,
    EMAIL_LOGIN_DEBUG,
    SMTP_FROM_EMAIL,
    SMTP_FROM_NAME,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USE_SSL,
    SMTP_USE_TLS,
    SMTP_USERNAME,
)



def brevo_delivery_configured() -> bool:
    return bool(BREVO_API_KEY and BREVO_SENDER_EMAIL)



def smtp_delivery_configured() -> bool:
    return bool(SMTP_HOST and SMTP_FROM_EMAIL)



def email_delivery_configured() -> bool:
    return brevo_delivery_configured() or smtp_delivery_configured()



def email_login_available() -> bool:
    return EMAIL_LOGIN_DEBUG or email_delivery_configured()



def _build_login_code_content(code: str) -> tuple[str, str, str]:
    subject = f"{APP_BRAND_NAME} 登录验证码"
    plain_text = (
        f"您好，\n\n"
        f"您本次登录 {APP_BRAND_NAME} 的验证码是：{code}\n"
        f"验证码 {EMAIL_LOGIN_CODE_TTL_MINUTES} 分钟内有效，仅可使用一次。\n"
        f"如果这不是您本人的操作，请忽略这封邮件。\n"
    )
    html = f"""
    <div style=\"font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #111827; line-height: 1.7;\">
      <h2 style=\"margin-bottom: 12px;\">{APP_BRAND_NAME} 登录验证码</h2>
      <p>您好，您本次登录验证码如下：</p>
      <div style=\"margin: 20px 0; padding: 16px 20px; font-size: 30px; font-weight: 700; letter-spacing: 8px; background: #f3f4f6; border-radius: 12px; display: inline-block;\">{code}</div>
      <p>验证码 <strong>{EMAIL_LOGIN_CODE_TTL_MINUTES} 分钟内有效</strong>，且仅可使用一次。</p>
      <p style=\"color: #6b7280; font-size: 13px;\">如果这不是您本人的操作，请忽略这封邮件。</p>
    </div>
    """
    return subject, plain_text, html



def _build_login_code_message(recipient_email: str, subject: str, plain_text: str, html: str) -> EmailMessage:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>" if SMTP_FROM_NAME else SMTP_FROM_EMAIL
    message["To"] = recipient_email
    message.set_content(plain_text)
    message.add_alternative(html, subtype="html")
    return message



def _send_message_sync(message: EmailMessage) -> None:
    if SMTP_USE_SSL:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15, context=context) as server:
            if SMTP_USERNAME:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(message)
        return

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
        if SMTP_USE_TLS:
            context = ssl.create_default_context()
            server.starttls(context=context)
        if SMTP_USERNAME:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(message)


async def _send_via_brevo(recipient_email: str, subject: str, plain_text: str, html: str) -> None:
    payload = {
        "sender": {
            "name": BREVO_SENDER_NAME,
            "email": BREVO_SENDER_EMAIL,
        },
        "to": [{"email": recipient_email}],
        "subject": subject,
        "htmlContent": html,
        "textContent": plain_text,
    }

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(f"{BREVO_API_BASE_URL}/smtp/email", json=payload, headers=headers)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Brevo 邮件发送失败，请稍后重试（{exc.__class__.__name__}）") from exc

    if response.status_code not in (200, 201, 202):
        detail = response.text
        try:
            data = response.json()
            detail = data.get("message") or data.get("code") or detail
        except Exception:
            pass
        raise HTTPException(status_code=502, detail=f"Brevo 邮件发送失败：{detail}")


async def send_login_code_email(recipient_email: str, code: str) -> None:
    if EMAIL_LOGIN_DEBUG and not email_delivery_configured():
        return

    if not email_delivery_configured():
        raise HTTPException(status_code=503, detail="邮箱登录暂未配置发信服务，请先设置 Brevo API 或 SMTP 环境变量")

    subject, plain_text, html = _build_login_code_content(code)

    if brevo_delivery_configured():
        await _send_via_brevo(recipient_email, subject, plain_text, html)
        return

    message = _build_login_code_message(recipient_email, subject, plain_text, html)
    try:
        await asyncio.to_thread(_send_message_sync, message)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"验证码邮件发送失败，请稍后重试（{exc.__class__.__name__}）") from exc
