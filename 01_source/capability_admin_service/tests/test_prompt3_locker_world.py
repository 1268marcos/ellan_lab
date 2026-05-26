from __future__ import annotations

PREFIX = "/api/v1/capability-admin"

LOCKER_MUST = {
    "INPOST",
    "DHL",
    "DPD",
    "MAGALU",
    "MELI",
    "MERCADOLIVRE",
    "AMAZON",
    "CORREIOS",
    "CTT",
    "WORTEN",
    "EL_CORTE_INGLES",
}


def test_locker_world_presence(client):
    client.post(f"{PREFIX}/seed")
    presence = client.get(f"{PREFIX}/ecosystem/locker-presence")
    assert presence.status_code == 200
    assert presence.json()["total"] >= 20
    codes = {r["player_code"] for r in presence.json()["items"]}
    assert LOCKER_MUST.issubset(codes)

    inpost = client.get(f"{PREFIX}/ecosystem/locker-presence", params={"player_code": "INPOST"})
    assert inpost.json()["total"] >= 1
    assert inpost.json()["items"][0]["locker_role"] == "PARCEL_LOCKER_NETWORK"

    dhl = client.get(f"{PREFIX}/ecosystem/locker-presence", params={"player_code": "DHL"})
    assert dhl.json()["items"][0]["program_code"] == "DHL_PACKSTATION"

    pt_retail = client.get(
        f"{PREFIX}/ecosystem/locker-presence", params={"locker_role": "RETAIL_LOCKER_HUB"}
    )
    assert pt_retail.json()["total"] >= 3
    retail_codes = {r["player_code"] for r in pt_retail.json()["items"]}
    assert {"MAGALU", "WORTEN", "EL_CORTE_INGLES"}.issubset(retail_codes)


def test_locker_profile_bindings(client):
    client.post(f"{PREFIX}/seed")
    bindings = client.get(f"{PREFIX}/ecosystem/bindings").json()["items"]
    pairs = {(b["profile_code"], b["player_code"]) for b in bindings}
    assert ("PT:kiosk:purchase", "CTT") in pairs
    assert ("DE:carrier:dropoff", "DHL") in pairs
    assert ("SP:kiosk:pickup", "CORREIOS") in pairs
