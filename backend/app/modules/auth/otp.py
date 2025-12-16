from __future__ import annotations

import hmac
import hashlib
import secrets
import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import settings
from app.modules.auth.models import OtpPurpose


def generate_otp_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(email: str, purpose: OtpPurpose, otp_code: str) -> str:
    key = (settings.SECRET_KEY or "change-me").encode("utf-8")
    msg = f"{email.lower()}:{purpose.value}:{otp_code}".encode("utf-8")
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


def verify_otp(email: str, purpose: OtpPurpose, otp_code: str, expected_hash: str) -> bool:
    computed = hash_otp(email=email, purpose=purpose, otp_code=otp_code)
    return hmac.compare_digest(computed, expected_hash or "")


def _build_subject(purpose: OtpPurpose) -> str:
    if purpose == OtpPurpose.RESET_PASSWORD:
        return "Smart Travel - OTP đặt lại mật khẩu"
    return "Smart Travel - Mã xác thực OTP"


def _build_html(otp_code: str, purpose: OtpPurpose, ttl_min: int) -> str:
    title = "Xác thực tài khoản" if purpose == OtpPurpose.REGISTER else "Đặt lại mật khẩu"
    subtitle = (
        "Dùng mã OTP bên dưới để hoàn tất đăng ký."
        if purpose == OtpPurpose.REGISTER
        else "Dùng mã OTP bên dưới để đặt lại mật khẩu."
    )
    return f"""\
<!doctype html>
<html lang="vi">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title}</title>
  </head>
  <body style="margin:0;background:#f6f7fb;font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Arial;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="padding:28px 12px;">
      <tr>
        <td align="center">
          <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border-radius:18px;overflow:hidden;box-shadow:0 12px 40px rgba(17,24,39,.10);">
            <tr>
              <td style="padding:22px 24px;background:linear-gradient(135deg,#ff4fa3 0%,#a855f7 60%,#60a5fa 100%);color:#fff;">
                <div style="font-size:18px;font-weight:700;letter-spacing:.2px;">Smart Travel</div>
                <div style="opacity:.95;margin-top:4px;font-size:13px;">{title}</div>
              </td>
            </tr>
            <tr>
              <td style="padding:26px 24px 8px;color:#111827;">
                <div style="font-size:15px;line-height:1.55;">{subtitle}</div>
              </td>
            </tr>
            <tr>
              <td style="padding:10px 24px 4px;">
                <div style="display:inline-block;padding:16px 22px;border-radius:14px;background:#fff1f7;border:1px solid #ffd0e6;">
                  <div style="font-size:28px;font-weight:800;letter-spacing:6px;color:#b42318;text-align:center;">{otp_code}</div>
                </div>
              </td>
            </tr>
            <tr>
              <td style="padding:10px 24px 18px;color:#374151;">
                <div style="font-size:13px;line-height:1.6;">
                  Mã có hiệu lực trong <b>{ttl_min}</b> phút. Không chia sẻ mã này với bất kỳ ai.
                </div>
              </td>
            </tr>
            <tr>
              <td style="padding:18px 24px 24px;color:#6b7280;font-size:12px;line-height:1.6;border-top:1px solid #eef2f7;">
                Nếu bạn không yêu cầu thao tác này, vui lòng bỏ qua email.
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""


def send_otp_email(to_email: str, otp_code: str, purpose: OtpPurpose) -> None:
    host = settings.BREVO_SMTP_HOST
    port = settings.BREVO_SMTP_PORT
    username = settings.BREVO_SMTP_USER
    password = settings.BREVO_SMTP_PASSWORD

    if not host or not username or not password or not settings.EMAIL_FROM:
        raise RuntimeError("SMTP is not configured (missing Brevo SMTP credentials or EMAIL_FROM).")

    ttl_min = int(getattr(settings, "OTP_TTL_MIN", 10) or 10)

    msg = EmailMessage()
    msg["Subject"] = _build_subject(purpose)
    from_name = settings.EMAIL_FROM_NAME or "Smart Travel"
    msg["From"] = f"{from_name} <{settings.EMAIL_FROM}>"
    msg["To"] = to_email

    text = (
        f"OTP của bạn là: {otp_code}\n"
        f"Mã có hiệu lực trong {ttl_min} phút.\n"
        "Nếu bạn không yêu cầu thao tác này, vui lòng bỏ qua email."
    )
    msg.set_content(text)
    msg.add_alternative(_build_html(otp_code=otp_code, purpose=purpose, ttl_min=ttl_min), subtype="html")

    context = ssl.create_default_context()
    with smtplib.SMTP(host, port, timeout=20) as smtp:
        smtp.ehlo()
        smtp.starttls(context=context)
        smtp.ehlo()
        smtp.login(username, password)
        smtp.send_message(msg)

