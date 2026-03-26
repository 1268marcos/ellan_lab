# 01_source/order_pickup_service/app/services/email_notification_service.py
from __future__ import annotations

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings


class EmailNotificationError(Exception):
    pass


# =========================================================
# RECEIPT EMAIL (KIOSK)
# =========================================================

def _build_receipt_email_html(*, receipt_code: str, order_id: str) -> str:
    return f"""
    <div style="font-family: Arial, sans-serif;">
        <h2>Comprovante fiscal</h2>
        <p>Seu comprovante foi gerado com sucesso.</p>
        <p><strong>Pedido:</strong> {order_id}</p>
        <p><strong>Código:</strong> {receipt_code}</p>
        <p>Guarde este código para consulta posterior.</p>
        <hr/>
        <p>Se você não solicitou este código, pode ignorar com segurança este e-mail.</p>
        <p>Outra pessoa pode ter digitado seu endereço de e-mail por engano.</p>
        <hr/>
        <small>ELLAN LAB LOCKER</small>
    </div>
    """


# =========================================================
# PICKUP EMAIL (ONLINE) 🚀 NOVO
# =========================================================

def _build_pickup_email_html(
    *,
    order_id: str,
    qr_value: str,
    manual_code: str,
    expires_at: str | None,
    frontend_base_url: str,
) -> str:
    pickup_link = f"{frontend_base_url}/meus-pedidos/{order_id}"

    return f"""
    <div style="font-family: Arial, sans-serif;">
        <h2>Retirada disponível</h2>

        <p>Seu pedido está pronto para retirada.</p>

        <p><strong>Pedido:</strong> {order_id}</p>

        <p>Ficamos agradecidos por sua compra e saboreie nossas delícias.</p>
        
        <hr/>

        <h3>QR Code de retirada</h3>
        <p>Apresente este QR Code no locker:</p>

        <pre style="background:#eee;padding:10px;border-radius:6px;">
{qr_value}
        </pre>

        <hr/>

        <h3>Código manual (fallback)</h3>
        <p><strong>{manual_code}</strong></p>

        <p>Use este código se não conseguir utilizar o QR Code.</p>

        <hr/>

        <p><strong>Validade:</strong> {expires_at or "ver aplicativo"}</p>

        <hr/>

        <p>
            Você também pode acessar sua retirada em:
            <br/>
            <a href="{pickup_link}">{pickup_link}</a>
        </p>

        <hr/>

        <small>ELLAN LAB LOCKER</small>
    </div>
    """


# =========================================================
# CORE SMTP
# =========================================================

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

    except Exception as exc:
        raise EmailNotificationError(
            f"Falha ao enviar email: {exc.__class__.__name__}: {exc}"
        ) from exc


# =========================================================
# PUBLIC FUNCTIONS
# =========================================================

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


def send_pickup_email(
    *,
    to_email: str,
    order_id: str,
    qr_value: str,
    manual_code: str,
    expires_at: str | None,
) -> None:
    # frontend_base_url = settings.frontend_base_url or "http://localhost:5173"
    frontend_base_url = getattr(settings, "frontend_base_url", None) or getattr(settings, "FRONTEND_BASE_URL", None) or "http://localhost:5173"

    html = _build_pickup_email_html(
        order_id=order_id,
        qr_value=qr_value,
        manual_code=manual_code,
        expires_at=expires_at,
        frontend_base_url=frontend_base_url,
    )

    send_email(
        to_email=to_email,
        subject="Seu código de retirada",
        html=html,
    )