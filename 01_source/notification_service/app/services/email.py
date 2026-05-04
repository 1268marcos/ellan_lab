def render_email(body: str, order_id: str) -> str:
    return body.replace("{{order_id}}", order_id)


def send_email(to: str, subject: str, body: str) -> bool:
    _ = to
    _ = subject
    return len(body) > 0
