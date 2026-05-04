def render_whatsapp(body: str, order_id: str) -> str:
    return body.replace("{{order_id}}", order_id)


def send_whatsapp(to: str, body: str) -> bool:
    _ = to
    return len(body) > 0
