from pathlib import Path

import json


def test_grafana_dashboards_parse():
    root = Path(__file__).resolve().parents[1]
    inv = json.loads((root / "metrics/grafana_dashboards/inventory_dashboard.json").read_text())
    assert inv["title"] == "Inventory Service"
    slo = json.loads((root / "metrics/grafana_dashboards/slos_dashboard.json").read_text())
    assert "SLOs" in slo["title"]


def test_alert_files_contain_rules():
    root = Path(__file__).resolve().parents[1]
    ia = (root / "alerts/inventory_alerts.yml").read_text()
    sa = (root / "alerts/slo_alerts.yml").read_text()
    assert "groups:" in ia and "InventoryStreamErrors" in ia
    assert "SLOErrorBudgetBurn" in sa
