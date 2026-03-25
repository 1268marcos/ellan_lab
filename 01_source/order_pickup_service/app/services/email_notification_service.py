# 01_source/order_pickup_service/app/services/email_notification_service.py
from __future__ import annotations

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings


class EmailNotificationError(Exception):
    pass


def _build_receipt_email_html(*, receipt_code: str, order_id: str) -> str:
    return f"""
    <div style="font-family: Arial, sans-serif;">
        <h2>Comprovante fiscal</h2>
        <p>Seu comprovante foi gerado com sucesso.</p>
        <p><strong>Pedido:</strong> {order_id}</p>
        <p><strong>Código:</strong> {receipt_code}</p>
        <p>Guarde este código para consulta posterior do comprovante.</p>
        <hr/>
        <small>ELLAN LAB LOCKER</small>
    </div>
    """


def send_email(*, to_email: str, subject: str, html: str) -> None:
    host = settings.email_host
    port = settings.email_port
    user = settings.email_username
    password = settings.email_password
    secure = settings.email_secure
    sender = settings.email_sender
    email_from_name = settings.email_from_name

    if not settings.email_enabled:
        raise EmailNotificationError("EMAIL_ENABLED=false")

    if not host:
        raise EmailNotificationError("EMAIL_HOST not configured")

    if not sender:
        raise EmailNotificationError("EMAIL_SENDER not configured")

    if not user:
        raise EmailNotificationError("EMAIL_USERNAME not configured")

    if not password:
        raise EmailNotificationError("EMAIL_PASSWORD not configured")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{email_from_name} <{sender}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        if secure:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, context=context, timeout=15) as server:
                server.login(user, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=15) as server:
                server.ehlo()
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
                server.login(user, password)
                server.send_message(msg)

    except smtplib.SMTPAuthenticationError as exc:
        raise EmailNotificationError(
            "Autenticação SMTP falhou. Verifique EMAIL_USERNAME, EMAIL_PASSWORD e EMAIL_SENDER."
        ) from exc
    except smtplib.SMTPRecipientsRefused as exc:
        raise EmailNotificationError(
            f"Destinatário recusado pelo servidor SMTP: {to_email}"
        ) from exc
    except smtplib.SMTPConnectError as exc:
        raise EmailNotificationError(
            "Falha ao conectar no servidor SMTP. Verifique EMAIL_HOST, EMAIL_PORT e EMAIL_SECURE."
        ) from exc
    except TimeoutError as exc:
        raise EmailNotificationError("Tempo de conexão com SMTP esgotado.") from exc
    except Exception as exc:
        raise EmailNotificationError(
            f"Falha ao enviar email: {exc.__class__.__name__}: {exc}"
        ) from exc


def send_receipt_email(*, to_email: str, receipt_code: str, order_id: str) -> None:
    html = _build_receipt_email_html(
        receipt_code=receipt_code,
        order_id=order_id,
    )
    send_email(
        to_email=to_email,
        subject="Seu comprovante fiscal",
        html=html,
    )