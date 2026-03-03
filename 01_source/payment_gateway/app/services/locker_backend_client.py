# 01_source/payment_gateway/app/services/locker_backend_client.py
import requests

class LockerBackendClient:
    def __init__(self, base_url: str, timeout_sec: int = 5):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout_sec

    def set_state(self, porta: int, state: str, product_id: str | None = None):
        payload = {"state": state, "product_id": product_id}
        r = requests.post(f"{self.base_url}/locker/slots/{porta}/set-state", json=payload, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def light_on(self, porta: int):
        r = requests.post(f"{self.base_url}/locker/slots/{porta}/light/on", json={}, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def open(self, porta: int):
        r = requests.post(f"{self.base_url}/locker/slots/{porta}/open", json={}, timeout=self.timeout)
        r.raise_for_status()
        return r.json()