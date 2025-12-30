"""
Email utilities (Brevo SMTP).
"""

from __future__ import annotations

import os
import smtplib
import ssl
from email.message import EmailMessage


def _smtp_settings() -> tuple[str, int, str | None, str | None]:
    host = os.environ.get("BREVO_SMTP_HOST", "smtp-relay.brevo.com").strip()
    port_raw = os.environ.get("BREVO_SMTP_PORT", "587").strip()
    try:
        port = int(port_raw)
    except Exception:
        port = 587

    user = os.environ.get("BREVO_SMTP_USER")
    password = os.environ.get("BREVO_SMTP_PASSWORD")
    return host, port, (user.strip() if user else None), (password.strip() if password else None)


def send_email(*, to_email: str, subject: str, html: str, text: str | None = None) -> None:
    host, port, user, password = _smtp_settings()

    from_email = os.environ.get("EMAIL_FROM", "noreply@habi.software").strip()
    from_name = os.environ.get("EMAIL_FROM_NAME", "Smart Travel").strip()
    from_header = f"{from_name} <{from_email}>" if from_name else from_email

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = from_header
    message["To"] = to_email

    if text:
        message.set_content(text)
        message.add_alternative(html, subtype="html")
    else:
        message.add_alternative(html, subtype="html")

    context = ssl.create_default_context()
    with smtplib.SMTP(host, port, timeout=20) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        if user and password:
            server.login(user, password)
        server.send_message(message)


def render_otp_email(*, code: str, ttl_minutes: int, title: str) -> tuple[str, str]:
    subject = f"{title} - Mã xác thực OTP"
    text = f"Mã OTP của bạn là: {code}\nMã có hiệu lực trong {ttl_minutes} phút."

    html = f"""\
<!doctype html>
<html lang="vi">
  <body style="margin:0;padding:0;background:#f7f7fb;font-family:Arial,Helvetica,sans-serif;">
    <div style="max-width:560px;margin:0 auto;padding:24px;">
      <div style="background:#ffffff;border-radius:16px;padding:24px;border:1px solid #eee;">
        <div style="font-size:20px;font-weight:700;color:#d81b60;margin-bottom:12px;">
          {title}
        </div>
        <div style="color:#444;line-height:1.6;margin-bottom:18px;">
          Xin chào,<br/>
          Bạn vừa yêu cầu mã xác thực OTP. Vui lòng nhập mã dưới đây để tiếp tục.
        </div>

        <div style="text-align:center;margin:20px 0;">
          <div style="display:inline-block;padding:14px 18px;border-radius:12px;background:#fff0f6;border:1px solid #ffd6e7;">
            <span style="font-size:28px;letter-spacing:6px;font-weight:800;color:#d81b60;">{code}</span>
          </div>
        </div>

        <div style="color:#666;line-height:1.6;">
          Mã có hiệu lực trong <b>{ttl_minutes} phút</b>.<br/>
          Nếu bạn không thực hiện yêu cầu này, vui lòng bỏ qua email.
        </div>

        <div style="margin-top:22px;padding-top:16px;border-top:1px solid #eee;color:#999;font-size:12px;line-height:1.5;">
          Email được gửi tự động, vui lòng không trả lời email này.
        </div>
      </div>
    </div>
  </body>
</html>
"""

    return subject, text + "\n", html

