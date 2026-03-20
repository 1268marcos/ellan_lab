# 01_source/backend/order_lifecycle_service/app/services/pickup_executive_summary_service.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.schemas.analytics_executive_summary import (
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


def _to_exec_items(items, label_builder):
    result: list[ExecutiveSummaryItem] = []
    for item in items:
        result.append(
            ExecutiveSummaryItem(
                rank=item.rank,
                dimension_value=item.dimension_value,
                metric=item.metric,
                metric_value=item.metric_value,
                label=label_builder(item),
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
) -> list[ExecutiveSummaryTrendItem]:
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

    rows: list[ExecutiveSummaryTrendItem] = []
    for key in keys:
        prev_item = previous_map.get(key)
        curr_item = current_map.get(key)

        prev_rate = prev_item.redemption_rate if prev_item else 0.0
        curr_rate = curr_item.redemption_rate if curr_item else 0.0
        delta = round(curr_rate - prev_rate, 3)

        prev_total = prev_item.total_terminal_pickups if prev_item else 0
        curr_total = curr_item.total_terminal_pickups if curr_item else 0

        rows.append(
            ExecutiveSummaryTrendItem(
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
            )
        )

    rows.sort(
        key=lambda x: (
            x.delta_redemption_rate,
            x.current_terminal_pickups,
            x.region or "",
        )
    )

    return rows[:limit]


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

    worst_regions_trend = _build_region_trend(
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
        items=_to_exec_items(worst_lockers_ranking.items, _label_worst_locker),
    )

    best_sites = ExecutiveSummarySection(
        title="Melhores sites por conversão",
        dimension="site_id",
        metric="redemption_rate",
        direction="desc",
        items=_to_exec_items(best_sites_ranking.items, _label_best_site),
    )

    critical_machines = ExecutiveSummarySection(
        title="Máquinas críticas por tempo de porta aberta",
        dimension="machine_id",
        metric="avg_minutes_door_opened_to_door_closed",
        direction="desc",
        items=_to_exec_items(critical_machines_ranking.items, _label_critical_machine),
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

    if worst_regions_trend:
        top = worst_regions_trend[0]
        insights.append(
            f"A pior tendência recente está na região {top.region or 'N/D'}, "
            f"com variação de {top.delta_redemption_rate:.3f} p.p. na taxa de retirada."
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
        worst_regions_trend=worst_regions_trend,
        insights=insights,
        filters=overview_metrics.filters,
    )