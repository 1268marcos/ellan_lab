from __future__ import annotations

import ssl
from pathlib import Path

import httpx


def build_ssl_context(ca_file: str, cert_file: str, key_file: str) -> ssl.SSLContext:
    ctx = ssl.create_default_context(cafile=ca_file)
    ctx.load_cert_chain(certfile=cert_file, keyfile=key_file)
    return ctx


def mtls_client(base_url: str, ca_file: str, cert_file: str, key_file: str) -> httpx.Client:
    for p in (ca_file, cert_file, key_file):
        if not Path(p).is_file():
            raise FileNotFoundError(p)
    ctx = build_ssl_context(ca_file, cert_file, key_file)
    return httpx.Client(base_url=base_url, verify=ctx, timeout=10.0)
