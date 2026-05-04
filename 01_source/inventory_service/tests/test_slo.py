from slo import consistency, error_rate, latency


def test_error_rate_slo():
    assert error_rate.within_error_rate_slo(0, 1000)
    assert not error_rate.within_error_rate_slo(5, 1000, max_rate=0.001)


def test_latency_slo():
    assert latency.within_latency_slo(48.0, 40.0, 10.0)
    assert not latency.within_latency_slo(60.0, 40.0, 10.0)


def test_consistency_slo():
    assert consistency.within_consistency_slo(0, 10_000)
    assert not consistency.within_consistency_slo(2, 10_000, max_rate=0.0001)


def test_slos_zero_totals():
    assert error_rate.within_error_rate_slo(0, 0)
    assert consistency.within_consistency_slo(0, 0)
