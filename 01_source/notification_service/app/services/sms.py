def render_sms(body: str, order_id: str) -> str:
    return body.replace("{{order_id}}", order_id)


def send_sms(to: str, body: str) -> bool:
    _ = to
    return len(body) > 0
