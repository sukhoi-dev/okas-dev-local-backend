import os
import boto3
from botocore.exceptions import ClientError

_AWS_REGION    = os.getenv("AWS_REGION", "ap-south-1")
_SES_FROM      = os.getenv("SES_FROM_EMAIL", "noreply@okas.ai")


def send_otp_email(to_email: str, otp_code: str) -> None:
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

    client = boto3.client("ses", region_name=_AWS_REGION)
    try:
        client.send_email(
            Source=_SES_FROM,
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": "Your OKAS Login OTP", "Charset": "UTF-8"},
                "Body": {
                    "Text": {"Data": text_body, "Charset": "UTF-8"},
                    "Html": {"Data": html_body, "Charset": "UTF-8"},
                },
            },
        )
    except ClientError as exc:
        raise RuntimeError(exc.response["Error"]["Message"]) from exc
