from metrics import inventory_metrics


def test_counters_and_gauge():
    inventory_metrics.inc_reservation("pending")
    inventory_metrics.inc_stream("payment.confirmed")
    inventory_metrics.inc_stream_error()
    inventory_metrics.set_divergences(2)
