import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email(*, to_email: str, subject: str, html: str) -> None:
    host = os.getenv("EMAIL_HOST", "smtp.hostinger.com")
    port = int(os.getenv("EMAIL_PORT", "465"))
    user = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    secure = os.getenv("EMAIL_SECURE", "true").lower() == "true"
    email_from_name = os.getenv("EMAIL_FROM_NAME", "ELLAN LAB")

    msg = MIMEMultipart()
    msg["From"] = f'"{email_from_name}" <{user}>'
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html, "html"))

    if secure:
        server = smtplib.SMTP_SSL(host, port)
    else:
        server = smtplib.SMTP(host, port)
        server.starttls()

    server.login(user, password)
    server.send_message(msg)
    server.quit()