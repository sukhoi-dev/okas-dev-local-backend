import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def send_otp_email(to_email: str, otp_code: str) -> None:
    smtp_host     = os.getenv("SMTP_HOST", "")
    smtp_port     = int(os.getenv("SMTP_PORT", "587"))
    smtp_user     = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    smtp_from     = os.getenv("SMTP_FROM", smtp_user)

    # Dev mode: if SMTP is not configured, log the OTP and skip sending
    if not smtp_host or not smtp_user:
        logger.warning(
            "[DEV] SMTP not configured — OTP for %s is: %s", to_email, otp_code
        )
        return

    msg             = MIMEMultipart("alternative")
    msg["Subject"]  = "Your OKAS Login OTP"
    msg["From"]     = smtp_from
    msg["To"]       = to_email

    text_body = (
        f"Your OKAS login OTP is: {otp_code}\n\n"
        "This code expires in 10 minutes. Do not share it with anyone."
    )
    html_body = f"""
    <html><body style="font-family:sans-serif;padding:24px">
      <p>Your <strong>OKAS</strong> login OTP is:</p>
      <h2 style="letter-spacing:8px;font-size:36px">{otp_code}</h2>
      <p>This code expires in <strong>10 minutes</strong>.<br>Do not share it with anyone.</p>
    </body></html>
    """

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_from, to_email, msg.as_string())
