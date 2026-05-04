def test_create_reservation_insufficient_stock(client):
    r = client.post("/api/v1/reservations", json={"order_id": "iso", "sku_id": "no-inv-sku", "quantity": 1})
    assert r.status_code == 409


def test_confirm_not_found(client):
    r = client.post("/api/v1/reservations/00000000-0000-0000-0000-000000000001/confirm?version=1")
    assert r.status_code == 404


def test_confirm_version_mismatch(client):
    client.post("/api/v1/inventory/movements", json={"sku_id": "e1", "delta": 5, "reason": "s"})
    cr = client.post("/api/v1/reservations", json={"order_id": "e1o", "sku_id": "e1", "quantity": 1})
    rid = cr.json()["id"]
    r = client.post(f"/api/v1/reservations/{rid}/confirm?version=99")
    assert r.status_code == 409


def test_confirm_invalid_state(client):
    client.post("/api/v1/inventory/movements", json={"sku_id": "e2", "delta": 5, "reason": "s"})
    cr = client.post("/api/v1/reservations", json={"order_id": "e2o", "sku_id": "e2", "quantity": 1})
    rid = cr.json()["id"]
    ver = cr.json()["version"]
    c1 = client.post(f"/api/v1/reservations/{rid}/confirm?version={ver}")
    assert c1.status_code == 200
    ver2 = c1.json()["version"]
    r = client.post(f"/api/v1/reservations/{rid}/confirm?version={ver2}")
    assert r.status_code == 409


def test_release_not_found(client):
    r = client.delete("/api/v1/reservations/00000000-0000-0000-0000-000000000002?version=1")
    assert r.status_code == 404


def test_release_version_mismatch(client):
    client.post("/api/v1/inventory/movements", json={"sku_id": "e3", "delta": 5, "reason": "s"})
    cr = client.post("/api/v1/reservations", json={"order_id": "e3o", "sku_id": "e3", "quantity": 1})
    rid = cr.json()["id"]
    r = client.delete(f"/api/v1/reservations/{rid}?version=99")
    assert r.status_code == 409
