# 01_source/order_pickup_service/app/services/email_notification_service.py
from __future__ import annotations

import base64
import io
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from zoneinfo import ZoneInfo

from app.core.config import settings


class EmailNotificationError(Exception):
    pass


# =========================================================
# Helpers
# =========================================================

def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _format_pickup_expiration(*, expires_at: str | None, region: str | None) -> str:
    dt = _parse_iso_datetime(expires_at)
    if not dt:
        return expires_at or "ver aplicativo"

    region_norm = str(region or "").strip().upper()
    tz = ZoneInfo("Europe/Lisbon") if region_norm == "PT" else ZoneInfo("America/Sao_Paulo")

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))

    local_dt = dt.astimezone(tz)

    return local_dt.strftime("%d/%m/%Y às %H:%M")


def _build_pickup_link(order_id: str) -> str:
    base = settings.frontend_base_url.rstrip("/")
    return f"{base}/meus-pedidos/{order_id}"


def _build_qr_data_uri(value: str) -> str | None:
    """
    Gera imagem PNG em base64 para embutir no email.
    Se a lib qrcode não estiver instalada, retorna None e o email segue sem imagem.
    """
    try:
        import qrcode
    except Exception:
        return None

    try:
        qr = qrcode.QRCode(
            version=None,
            box_size=8,
            border=2,
        )
        qr.add_data(value)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_bytes = buffer.getvalue()
        encoded = base64.b64encode(img_bytes).decode("ascii")
        return f"data:image/png;base64,{encoded}"
    except Exception:
        return None


# =========================================================
# RECEIPT EMAIL (KIOSK)
# =========================================================

def _build_receipt_email_html(*, receipt_code: str, order_id: str) -> str:
    return f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.5; color: #111;">
        <h2>Comprovante fiscal</h2>
        <p>Seu comprovante foi gerado com sucesso.</p>
        <p><strong>Pedido:</strong> {order_id}</p>
        <p><strong>Código:</strong> {receipt_code}</p>
        <p>Guarde este código para consulta posterior.</p>
        <hr/>
        <small>ELLAN LAB LOCKER</small>
    </div>
    """


# =========================================================
# PICKUP EMAIL (ONLINE)
# =========================================================

def _build_pickup_email_html(
    *,
    order_id: str,
    qr_value: str,
    manual_code: str,
    expires_at: str | None,
    region: str | None,
    locker_id: str | None,
    slot: str | None,
) -> str:
    pickup_link = _build_pickup_link(order_id)
    formatted_expiration = _format_pickup_expiration(
        expires_at=expires_at,
        region=region,
    )
    qr_data_uri = _build_qr_data_uri(qr_value)

    location_lines = []
    if region:
        location_lines.append(f"<p><strong>Região:</strong> {region}</p>")
    if locker_id:
        location_lines.append(f"<p><strong>Locker / Cacifo:</strong> {locker_id}</p>")
    if slot:
        location_lines.append(f"<p><strong>Gaveta / Slot:</strong> {slot}</p>")

    location_html = "".join(location_lines)

    qr_image_html = (
        f"""
        <div style="margin: 16px 0; text-align: center;">
            <img
                src="{qr_data_uri}"
                alt="QR Code de retirada"
                style="max-width: 220px; width: 220px; height: 220px; border: 1px solid #ddd; padding: 8px; background: #fff;"
            />
        </div>
        """
        if qr_data_uri
        else
        """
        <p><strong>QR Code:</strong> seu cliente de email não conseguiu renderizar a imagem.
        Use o link do pedido ou o código manual abaixo.</p>
        """
    )

    return f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.55; color: #111;">
        <h2>Retirada disponível</h2>

        <p>Seu pedido está pronto para retirada.</p>

        <p><strong>Pedido:</strong> {order_id}</p>

        <p>Ficamos agradecidos por sua compra e saboreie nossas delícias.</p>

        <hr/>

        <h3>Local de retirada</h3>
        {location_html}

        <hr/>

        <h3>QR Code de retirada</h3>
        <p>Apresente este QR Code no locker/cacifo:</p>

        {qr_image_html}

        <hr/>

        <h3>Código manual (fallback)</h3>
        <p style="font-size: 20px; font-weight: bold; letter-spacing: 1px;">{manual_code}</p>

        <p>Use este código se não conseguir utilizar o QR Code.</p>

        <hr/>

        <p><strong>Validade:</strong> {formatted_expiration}</p>

        <hr/>

        <p>
            Você pode ver seu pedido em:
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
    region: str | None,
    locker_id: str | None,
    slot: str | None,
) -> None:
    html = _build_pickup_email_html(
        order_id=order_id,
        qr_value=qr_value,
        manual_code=manual_code,
        expires_at=expires_at,
        region=region,
        locker_id=locker_id,
        slot=slot,
    )

    send_email(
        to_email=to_email,
        subject="Seu código de retirada",
        html=html,
    )