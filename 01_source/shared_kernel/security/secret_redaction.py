SENSITIVE_KEYS = {
    "authorization",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "api_key",
    "signature",
    "webhook_signature",
}


def redact_dict(data: dict) -> dict:
    sanitized = {}
    for key, value in data.items():
        if key.lower() in SENSITIVE_KEYS:
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = redact_dict(value)
        else:
            sanitized[key] = value
    return sanitized
