import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch

from infra.mtls.client import mtls_client


def test_mtls_client_calls_httpx(tmp_path: Path):
    if shutil.which("openssl") is None:
        return
    key = tmp_path / "k.pem"
    cert = tmp_path / "c.pem"
    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-keyout",
            str(key),
            "-out",
            str(cert),
            "-subj",
            "/CN=test",
            "-days",
            "1",
        ],
        check=True,
        capture_output=True,
    )
    with patch("infra.mtls.client.httpx.Client") as m:
        mtls_client("https://example.test", str(cert), str(cert), str(key))
        m.assert_called_once()
