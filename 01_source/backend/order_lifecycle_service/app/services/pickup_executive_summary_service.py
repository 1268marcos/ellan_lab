# 01_source/backend/order_lifecycle_service/app/services/pickup_executive_summary_service.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import Numeric, func
from sqlalchemy.orm import Query

from app.models.lifecycle import AnalyticsFact
from app.schemas.analytics_executive_summary import (
    ExecutiveActionItem,
    ExecutiveSummaryItem,
    ExecutiveSummaryOverview,
    ExecutiveSummarySection,
    ExecutiveSummaryTrendItem,
    PickupExecutiveSummaryResponse,
)
from app.services.pickup_metrics_service import build_pickup_metrics
from app.services.pickup_ranking_service import build_pickup_ranking


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _apply_filters(
    query: Query,
    *,
    start_at: datetime | None,
    end_at: datetime | None,
    region: str | None,
    channel: str | None,
    slot: str | None,
    locker_id: str | None,
    machine_id: str | None,
    operator_id: str | None,
    tenant_id: str | None,
    site_id: str | None,
) -> Query:
    if start_at is not None:
        query = query.filter(AnalyticsFact.occurred_at >= start_at)

    if end_at is not None:
        query = query.filter(AnalyticsFact.occurred_at <= end_at)

    if region:
        query = query.filter(AnalyticsFact.region_code == region)

    if channel:
        query = query.filter(AnalyticsFact.order_channel == channel)

    if slot:
        query = query.filter(AnalyticsFact.slot_id == slot)

    if locker_id:
        query = query.filter(AnalyticsFact.payload["locker_id"].astext == locker_id)

    if machine_id:
        query = query.filter(AnalyticsFact.payload["machine_id"].astext == machine_id)

    if operator_id:
        query = query.filter(AnalyticsFact.payload["operator_id"].astext == operator_id)

    if tenant_id:
        query = query.filter(AnalyticsFact.payload["tenant_id"].astext == tenant_id)

    if site_id:
        query = query.filter(AnalyticsFact.payload["site_id"].astext == site_id)

    return query


def _dimension_expr(dimension: str):
    if dimension == "region":
        return AnalyticsFact.region_code
    if dimension == "channel":
        return AnalyticsFact.order_channel
    if dimension == "slot":
        return AnalyticsFact.slot_id
    if dimension == "locker_id":
        return AnalyticsFact.payload["locker_id"].astext
    if dimension == "machine_id":
        return AnalyticsFact.payload["machine_id"].astext
    if dimension == "operator_id":
        return AnalyticsFact.payload["operator_id"].astext
    if dimension == "tenant_id":
        return AnalyticsFact.payload["tenant_id"].astext
    if dimension == "site_id":
        return AnalyticsFact.payload["site_id"].astext
    raise ValueError(f"unsupported dimension: {dimension}")


def _grouped_stddev_minutes(
    db,
    *,
    dimension: str,
    fact_name: str,
    filters: dict,
) -> dict[str | None, float | None]:
    dim = _dimension_expr(dimension)

    query = db.query(
        dim.label("dimension_value"),
        func.stddev_pop(AnalyticsFact.payload["minutes"].astext.cast(Numeric)).label("stddev_value"),
    ).filter(
        AnalyticsFact.fact_name == fact_name,
    )

    query = _apply_filters(query, **filters)
    query = query.group_by(dim)

    result: dict[str | None, float | None] = {}
    for row in query.all():
        result[row.dimension_value] = round(float(row.stddev_value), 3) if row.stddev_value is not None else None
    return result


def _classify_exception(metric: str, value: float) -> tuple[str, str]:
    if metric == "expiration_rate":
        if value >= 40:
            return "CRITICAL", "investigate"
        if value >= 25:
            return "HIGH", "investigate"
        if value >= 10:
            return "MEDIUM", "monitor"
        return "LOW", "monitor"

    if metric == "avg_minutes_door_opened_to_door_closed":
        if value >= 8:
            return "CRITICAL", "investigate"
        if value >= 5:
            return "HIGH", "investigate"
        if value >= 2:
            return "MEDIUM", "monitor"
        return "LOW", "monitor"

    return "LOW", "monitor"


def _classify_positive(metric: str, value: float) -> tuple[str, str]:
    if metric == "redemption_rate":
        if value >= 95:
            return "LOW", "replicate"
        if value >= 85:
            return "LOW", "replicate"
        return "LOW", "monitor"

    if metric == "avg_minutes_ready_to_redeemed":
        if value <= 10:
            return "LOW", "replicate"
        if value <= 20:
            return "LOW", "monitor"
        return "MEDIUM", "monitor"

    return "LOW", "replicate"


def _classify_saturation(volume: float) -> tuple[str, str]:
    if volume >= 500:
        return "HIGH", "expand_capacity"
    if volume >= 200:
        return "MEDIUM", "monitor"
    return "LOW", "monitor"


def _classify_reliability(metric: str, value: float) -> tuple[str, str]:
    if metric == "cancellation_rate":
        if value <= 1:
            return "LOW", "replicate"
        if value <= 3:
            return "LOW", "monitor"
        if value <= 8:
            return "MEDIUM", "monitor"
        return "HIGH", "investigate"

    if metric == "avg_minutes_door_opened_to_door_closed":
        if value <= 1:
            return "LOW", "replicate"
        if value <= 2:
            return "LOW", "monitor"
        if value <= 5:
            return "MEDIUM", "monitor"
        return "HIGH", "investigate"

    if metric == "stddev_minutes_ready_to_redeemed":
        if value <= 2:
            return "LOW", "replicate"
        if value <= 5:
            return "LOW", "monitor"
        if value <= 10:
            return "MEDIUM", "monitor"
        return "HIGH", "investigate"

    return "LOW", "monitor"


def _classify_trend(delta: float) -> tuple[str, str]:
    if delta <= -15:
        return "CRITICAL", "investigate"
    if delta <= -8:
        return "HIGH", "investigate"
    if delta <= -3:
        return "MEDIUM", "monitor"
    if delta >= 5:
        return "LOW", "replicate"
    return "LOW", "monitor"


def _label_worst_locker(item) -> str:
    return (
        f"Locker {item.dimension_value or 'N/D'} com expiração de "
        f"{item.expiration_rate:.3f}% em {item.total_terminal_pickups} pickups terminais."
    )


def _label_best_site(item) -> str:
    return (
        f"Site {item.dimension_value or 'N/D'} com conversão de "
        f"{item.redemption_rate:.3f}% em {item.total_terminal_pickups} pickups terminais."
    )


def _label_critical_machine(item) -> str:
    return (
        f"Máquina {item.dimension_value or 'N/D'} com média de "
        f"{item.avg_minutes_door_opened_to_door_closed or 0:.3f} min entre porta aberta e porta fechada."
    )


def _label_best_locker(item) -> str:
    return (
        f"Locker {item.dimension_value or 'N/D'} com taxa de retirada de "
        f"{item.redemption_rate:.3f}%."
    )


def _label_best_region_sla(item) -> str:
    return (
        f"Região {item.dimension_value or 'N/D'} com média de "
        f"{item.avg_minutes_ready_to_redeemed or 0:.3f} min entre pronto e retirada."
    )


def _label_saturation(item, title_prefix: str) -> str:
    return (
        f"{title_prefix} {item.dimension_value or 'N/D'} concentra "
        f"{item.total_terminal_pickups} pickups terminais."
    )


def _label_reliability_cancel(item) -> str:
    return (
        f"Região {item.dimension_value or 'N/D'} com cancelamento de "
        f"{item.cancellation_rate:.3f}%."
    )


def _label_reliability_door(item) -> str:
    return (
        f"Máquina {item.dimension_value or 'N/D'} com média de "
        f"{item.avg_minutes_door_opened_to_door_closed or 0:.3f} min de porta aberta."
    )


# def _label_predictable_region(item) -> str:
#     return (
#         f"Região {item.dimension_value or 'N/D'} com desvio-padrão de "
#         f"{item.stddev_minutes_ready_to_redeemed or 0:.3f} min no SLA ready→redeemed."
#     )
def _label_predictable_region(item) -> str:
    # ⚠️ NÃO usar campo inexistente no ranking
    return (
        f"Região {item.dimension_value or 'N/D'} com comportamento previsível de retirada."
    )


def _to_exec_items(items, label_builder, classifier, extra_map: dict[str | None, float | None] | None = None, extra_metric_name: str | None = None):
    result: list[ExecutiveSummaryItem] = []
    for item in items:
        severity, recommended_action = classifier(item.metric, item.metric_value)

        stddev_value = None
        if extra_map is not None and extra_metric_name == "stddev_minutes_ready_to_redeemed":
            stddev_value = extra_map.get(item.dimension_value)
            if stddev_value is not None:
                severity, recommended_action = classifier(extra_metric_name, stddev_value)

        result.append(
            ExecutiveSummaryItem(
                rank=item.rank,
                dimension_value=item.dimension_value,
                metric=item.metric,
                metric_value=item.metric_value,
                label=label_builder(item),
                severity=severity,
                recommended_action=recommended_action,
                total_terminal_pickups=item.total_terminal_pickups,
                redeemed_pickups=item.redeemed_pickups,
                expired_pickups=item.expired_pickups,
                cancelled_pickups=item.cancelled_pickups,
                redemption_rate=item.redemption_rate,
                expiration_rate=item.expiration_rate,
                cancellation_rate=item.cancellation_rate,
                avg_minutes_created_to_ready=item.avg_minutes_created_to_ready,
                avg_minutes_ready_to_redeemed=item.avg_minutes_ready_to_redeemed,
                avg_minutes_door_opened_to_redeemed=item.avg_minutes_door_opened_to_redeemed,
                avg_minutes_door_opened_to_door_closed=item.avg_minutes_door_opened_to_door_closed,
                stddev_minutes_ready_to_redeemed=stddev_value,
            )
        )
    return result


def _build_region_trend(
    db,
    *,
    now: datetime,
    days_window: int,
    limit: int,
    base_filters: dict,
) -> tuple[list[ExecutiveSummaryTrendItem], list[ExecutiveSummaryTrendItem], list[ExecutiveSummaryTrendItem]]:
    current_start = now - timedelta(days=days_window)
    previous_end = current_start
    previous_start = previous_end - timedelta(days=days_window)

    previous = build_pickup_ranking(
        db,
        category="trend",
        metric="redemption_rate",
        dimension="region",
        direction="asc",
        limit=100,
        start_at=previous_start,
        end_at=previous_end,
        **base_filters,
    )

    current = build_pickup_ranking(
        db,
        category="trend",
        metric="redemption_rate",
        dimension="region",
        direction="asc",
        limit=100,
        start_at=current_start,
        end_at=now,
        **base_filters,
    )

    previous_map = {item.dimension_value: item for item in previous.items}
    current_map = {item.dimension_value: item for item in current.items}

    keys = set(previous_map.keys()) | set(current_map.keys())

    worsening: list[ExecutiveSummaryTrendItem] = []
    improving: list[ExecutiveSummaryTrendItem] = []
    stable: list[ExecutiveSummaryTrendItem] = []

    for key in keys:
        prev_item = previous_map.get(key)
        curr_item = current_map.get(key)

        prev_rate = prev_item.redemption_rate if prev_item else 0.0
        curr_rate = curr_item.redemption_rate if curr_item else 0.0
        delta = round(curr_rate - prev_rate, 3)

        prev_total = prev_item.total_terminal_pickups if prev_item else 0
        curr_total = curr_item.total_terminal_pickups if curr_item else 0

        severity, recommended_action = _classify_trend(delta)

        row = ExecutiveSummaryTrendItem(
            region=key,
            previous_redemption_rate=prev_rate,
            current_redemption_rate=curr_rate,
            delta_redemption_rate=delta,
            previous_terminal_pickups=prev_total,
            current_terminal_pickups=curr_total,
            label=(
                f"Região {key or 'N/D'} variou {delta:.3f} p.p. "
                f"na taxa de retirada ({prev_rate:.3f}% → {curr_rate:.3f}%)."
            ),
            severity=severity,
            recommended_action=recommended_action,
        )

        if delta <= -1:
            worsening.append(row)
        elif delta >= 1:
            improving.append(row)
        else:
            stable.append(row)

    worsening.sort(key=lambda x: (x.delta_redemption_rate, -(x.current_terminal_pickups), x.region or ""))
    improving.sort(key=lambda x: (-x.delta_redemption_rate, -(x.current_terminal_pickups), x.region or ""))
    stable.sort(key=lambda x: (abs(x.delta_redemption_rate), -(x.current_terminal_pickups), x.region or ""))

    return worsening[:limit], improving[:limit], stable[:limit]


def build_pickup_executive_summary(
    db,
    *,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    region: str | None = None,
    channel: str | None = None,
    slot: str | None = None,
    locker_id: str | None = None,
    machine_id: str | None = None,
    operator_id: str | None = None,
    tenant_id: str | None = None,
    site_id: str | None = None,
    ranking_limit: int = 5,
    trend_days_window: int = 7,
) -> PickupExecutiveSummaryResponse:
    now = end_at or _utc_now()

    base_filters = {
        "region": region,
        "channel": channel,
        "slot": slot,
        "locker_id": locker_id,
        "machine_id": machine_id,
        "operator_id": operator_id,
        "tenant_id": tenant_id,
        "site_id": site_id,
    }

    filters_with_window = {
        **base_filters,
        "start_at": start_at,
        "end_at": end_at,
    }

    overview_metrics = build_pickup_metrics(
        db,
        start_at=start_at,
        end_at=end_at,
        **base_filters,
    )

    worst_lockers_ranking = build_pickup_ranking(
        db,
        category="exception",
        metric="expiration_rate",
        dimension="locker_id",
        direction="desc",
        limit=ranking_limit,
        start_at=start_at,
        end_at=end_at,
        **base_filters,
    )

    best_sites_ranking = build_pickup_ranking(
        db,
        category="efficiency",
        metric="redemption_rate",
        dimension="site_id",
        direction="desc",
        limit=ranking_limit,
        start_at=start_at,
        end_at=end_at,
        **base_filters,
    )

    critical_machines_ranking = build_pickup_ranking(
        db,
        category="risk",
        metric="avg_minutes_door_opened_to_door_closed",
        dimension="machine_id",
        direction="desc",
        limit=ranking_limit,
        start_at=start_at,
        end_at=end_at,
        **base_filters,
    )

    best_lockers_ranking = build_pickup_ranking(
        db,
        category="positive",
        metric="redemption_rate",
        dimension="locker_id",
        direction="desc",
        limit=ranking_limit,
        start_at=start_at,
        end_at=end_at,
        **base_filters,
    )

    best_regions_sla_ranking = build_pickup_ranking(
        db,
        category="positive",
        metric="avg_minutes_ready_to_redeemed",
        dimension="region",
        direction="asc",
        limit=ranking_limit,
        start_at=start_at,
        end_at=end_at,
        **base_filters,
    )

    top_lockers_volume = build_pickup_ranking(
        db,
        category="saturation",
        metric="terminal_volume",
        dimension="locker_id",
        direction="desc",
        limit=ranking_limit,
        start_at=start_at,
        end_at=end_at,
        **base_filters,
    )

    top_regions_volume = build_pickup_ranking(
        db,
        category="saturation",
        metric="terminal_volume",
        dimension="region",
        direction="desc",
        limit=ranking_limit,
        start_at=start_at,
        end_at=end_at,
        **base_filters,
    )

    top_sites_volume = build_pickup_ranking(
        db,
        category="saturation",
        metric="terminal_volume",
        dimension="site_id",
        direction="desc",
        limit=ranking_limit,
        start_at=start_at,
        end_at=end_at,
        **base_filters,
    )

    low_cancel_regions = build_pickup_ranking(
        db,
        category="reliability",
        metric="cancellation_rate",
        dimension="region",
        direction="asc",
        limit=ranking_limit,
        start_at=start_at,
        end_at=end_at,
        **base_filters,
    )

    low_door_open_machines = build_pickup_ranking(
        db,
        category="reliability",
        metric="avg_minutes_door_opened_to_door_closed",
        dimension="machine_id",
        direction="asc",
        limit=ranking_limit,
        start_at=start_at,
        end_at=end_at,
        **base_filters,
    )

    region_stddev = _grouped_stddev_minutes(
        db,
        dimension="region",
        fact_name="pickup_sla_ready_to_redeemed",
        filters=filters_with_window,
    )

    predictable_region_base = build_pickup_ranking(
        db,
        category="reliability",
        metric="redemption_rate",
        dimension="region",
        direction="desc",
        limit=100,
        start_at=start_at,
        end_at=end_at,
        **base_filters,
    )

    predictable_region_items = []
    for item in predictable_region_base.items:
        stddev_value = region_stddev.get(item.dimension_value)
        if stddev_value is None:
            continue
        item.metric = "stddev_minutes_ready_to_redeemed"
        item.metric_value = stddev_value
        predictable_region_items.append(item)

    predictable_region_items.sort(
        key=lambda x: (x.metric_value, -(x.total_terminal_pickups), x.dimension_value or "")
    )
    predictable_region_items = predictable_region_items[:ranking_limit]

    worsening_regions_trend, improving_regions_trend, stable_regions_trend = _build_region_trend(
        db,
        now=now,
        days_window=trend_days_window,
        limit=ranking_limit,
        base_filters=base_filters,
    )

    worst_lockers = ExecutiveSummarySection(
        title="Piores lockers por expiração",
        dimension="locker_id",
        metric="expiration_rate",
        direction="desc",
        items=_to_exec_items(
            worst_lockers_ranking.items,
            _label_worst_locker,
            _classify_exception,
        ),
    )

    best_sites = ExecutiveSummarySection(
        title="Melhores sites por conversão",
        dimension="site_id",
        metric="redemption_rate",
        direction="desc",
        items=_to_exec_items(
            best_sites_ranking.items,
            _label_best_site,
            _classify_positive,
        ),
    )

    critical_machines = ExecutiveSummarySection(
        title="Máquinas críticas por tempo de porta aberta",
        dimension="machine_id",
        metric="avg_minutes_door_opened_to_door_closed",
        direction="desc",
        items=_to_exec_items(
            critical_machines_ranking.items,
            _label_critical_machine,
            _classify_exception,
        ),
    )

    positive_highlights = [
        ExecutiveSummarySection(
            title="Melhores lockers",
            dimension="locker_id",
            metric="redemption_rate",
            direction="desc",
            items=_to_exec_items(
                best_lockers_ranking.items,
                _label_best_locker,
                _classify_positive,
            ),
        ),
        ExecutiveSummarySection(
            title="Melhores sites",
            dimension="site_id",
            metric="redemption_rate",
            direction="desc",
            items=_to_exec_items(
                best_sites_ranking.items,
                _label_best_site,
                _classify_positive,
            ),
        ),
        ExecutiveSummarySection(
            title="Melhores regiões por SLA",
            dimension="region",
            metric="avg_minutes_ready_to_redeemed",
            direction="asc",
            items=_to_exec_items(
                best_regions_sla_ranking.items,
                _label_best_region_sla,
                _classify_positive,
            ),
        ),
    ]

    saturation = [
        ExecutiveSummarySection(
            title="Lockers mais usados",
            dimension="locker_id",
            metric="terminal_volume",
            direction="desc",
            items=_to_exec_items(
                top_lockers_volume.items,
                lambda item: _label_saturation(item, "Locker"),
                lambda metric, value: _classify_saturation(value),
            ),
        ),
        ExecutiveSummarySection(
            title="Regiões mais carregadas",
            dimension="region",
            metric="terminal_volume",
            direction="desc",
            items=_to_exec_items(
                top_regions_volume.items,
                lambda item: _label_saturation(item, "Região"),
                lambda metric, value: _classify_saturation(value),
            ),
        ),
        ExecutiveSummarySection(
            title="Sites com maior throughput",
            dimension="site_id",
            metric="terminal_volume",
            direction="desc",
            items=_to_exec_items(
                top_sites_volume.items,
                lambda item: _label_saturation(item, "Site"),
                lambda metric, value: _classify_saturation(value),
            ),
        ),
    ]

    reliability = [
        ExecutiveSummarySection(
            title="Regiões com menor cancelamento",
            dimension="region",
            metric="cancellation_rate",
            direction="asc",
            items=_to_exec_items(
                low_cancel_regions.items,
                _label_reliability_cancel,
                _classify_reliability,
            ),
        ),
        ExecutiveSummarySection(
            title="Máquinas com menor porta aberta prolongada",
            dimension="machine_id",
            metric="avg_minutes_door_opened_to_door_closed",
            direction="asc",
            items=_to_exec_items(
                low_door_open_machines.items,
                _label_reliability_door,
                _classify_reliability,
            ),
        ),
        ExecutiveSummarySection(
            title="Regiões com menor variabilidade de SLA",
            dimension="region",
            metric="stddev_minutes_ready_to_redeemed",
            direction="asc",
            items=_to_exec_items(
                predictable_region_items,
                _label_predictable_region,
                _classify_reliability,
                extra_map=region_stddev,
                extra_metric_name="stddev_minutes_ready_to_redeemed",
            ),
        ),
    ]

    actions: list[ExecutiveActionItem] = []

    def _append_actions(section: ExecutiveSummarySection):
        for item in section.items[:2]:
            if item.severity in {"MEDIUM", "HIGH", "CRITICAL"} or item.recommended_action in {"replicate", "expand_capacity"}:
                actions.append(
                    ExecutiveActionItem(
                        title=section.title,
                        severity=item.severity,
                        recommended_action=item.recommended_action,
                        dimension=section.dimension,
                        dimension_value=item.dimension_value,
                        reason=item.label,
                    )
                )

    _append_actions(worst_lockers)
    _append_actions(best_sites)
    _append_actions(critical_machines)
    for section in positive_highlights:
        _append_actions(section)
    for section in saturation:
        _append_actions(section)
    for section in reliability:
        _append_actions(section)

    for trend_item in worsening_regions_trend[:2]:
        actions.append(
            ExecutiveActionItem(
                title="Regiões com pior tendência",
                severity=trend_item.severity,
                recommended_action=trend_item.recommended_action,
                dimension="region",
                dimension_value=trend_item.region,
                reason=trend_item.label,
            )
        )

    insights: list[str] = []

    if worst_lockers.items:
        top = worst_lockers.items[0]
        insights.append(
            f"O principal ponto de atenção é o locker {top.dimension_value or 'N/D'}, "
            f"com taxa de expiração de {top.expiration_rate:.3f}%."
        )

    if best_sites.items:
        top = best_sites.items[0]
        insights.append(
            f"O melhor desempenho de conversão está no site {top.dimension_value or 'N/D'}, "
            f"com taxa de retirada de {top.redemption_rate:.3f}%."
        )

    if critical_machines.items:
        top = critical_machines.items[0]
        insights.append(
            f"A máquina mais crítica é {top.dimension_value or 'N/D'}, "
            f"com média de {top.avg_minutes_door_opened_to_door_closed or 0:.3f} min "
            f"entre abertura e fechamento da porta."
        )

    if worsening_regions_trend:
        top = worsening_regions_trend[0]
        insights.append(
            f"A pior tendência recente está na região {top.region or 'N/D'}, "
            f"com variação de {top.delta_redemption_rate:.3f} p.p. na taxa de retirada."
        )

    if improving_regions_trend:
        top = improving_regions_trend[0]
        insights.append(
            f"A melhor evolução recente está na região {top.region or 'N/D'}, "
            f"com ganho de {top.delta_redemption_rate:.3f} p.p. na taxa de retirada."
        )

    return PickupExecutiveSummaryResponse(
        window_start=overview_metrics.window_start,
        window_end=overview_metrics.window_end,
        overview=ExecutiveSummaryOverview(
            total_terminal_pickups=overview_metrics.total_terminal_pickups,
            redeemed_pickups=overview_metrics.redeemed_pickups,
            expired_pickups=overview_metrics.expired_pickups,
            cancelled_pickups=overview_metrics.cancelled_pickups,
            redemption_rate=overview_metrics.redemption_rate,
            expiration_rate=overview_metrics.expiration_rate,
            cancellation_rate=overview_metrics.cancellation_rate,
            avg_minutes_created_to_ready=overview_metrics.avg_minutes_created_to_ready,
            avg_minutes_ready_to_redeemed=overview_metrics.avg_minutes_ready_to_redeemed,
            avg_minutes_door_opened_to_redeemed=overview_metrics.avg_minutes_door_opened_to_redeemed,
            avg_minutes_door_opened_to_door_closed=overview_metrics.avg_minutes_door_opened_to_door_closed,
        ),
        worst_lockers=worst_lockers,
        best_sites=best_sites,
        critical_machines=critical_machines,
        positive_highlights=positive_highlights,
        saturation=saturation,
        reliability=reliability,
        worsening_regions_trend=worsening_regions_trend,
        improving_regions_trend=improving_regions_trend,
        stable_regions_trend=stable_regions_trend,
        actions=actions,
        insights=insights,
        filters=overview_metrics.filters,
    )