import uuid
from fastapi import APIRouter
from app.core.event_log import log_event
from app.core.event_types import EventType, Severity

router = APIRouter(prefix="/debug", tags=["debug"])

MACHINE_ID = "CACIFO-SP-001"


# @router.post("/log_sample")
@router.api_route("/log_sample", methods=["GET", "POST"])
def log_sample():

    correlation_id = str(uuid.uuid4())
    sale_id = f"S-{uuid.uuid4().hex[:8]}"
    command_id = f"CMD-{uuid.uuid4().hex[:8]}"
    door_id = 17

    events = []

    events.append(
        log_event(
            machine_id=MACHINE_ID,
            event_type=EventType.SALE_STARTED,
            severity=Severity.INFO,
            correlation_id=correlation_id,
            door_id=door_id,
            sale_id=sale_id,
            payload={"message": "Sale initiated"},
        )
    )

    events.append(
        log_event(
            machine_id=MACHINE_ID,
            event_type=EventType.PAYMENT_APPROVED,
            severity=Severity.INFO,
            correlation_id=correlation_id,
            door_id=door_id,
            sale_id=sale_id,
            payload={"amount": 31.2, "currency": "BRL"},
        )
    )

    events.append(
        log_event(
            machine_id=MACHINE_ID,
            event_type=EventType.HW_OPEN_CMD_SENT,
            severity=Severity.INFO,
            correlation_id=correlation_id,
            door_id=door_id,
            sale_id=sale_id,
            command_id=command_id,
            payload={"timeout_seconds": 3},
        )
    )

    events.append(
        log_event(
            machine_id=MACHINE_ID,
            event_type=EventType.STATE_CHANGE,
            severity=Severity.INFO,
            correlation_id=correlation_id,
            door_id=door_id,
            old_state="AVAILABLE",
            new_state="PAID_PENDING_OPEN",
            payload={"fsm": "door_state"},
        )
    )

    events.append(
        log_event(
            machine_id=MACHINE_ID,
            event_type=EventType.DOOR_OPENED,
            severity=Severity.INFO,
            correlation_id=correlation_id,
            door_id=door_id,
            sale_id=sale_id,
            payload={"sensor": "reed_switch"},
        )
    )

    events.append(
        log_event(
            machine_id=MACHINE_ID,
            event_type=EventType.DOOR_CLOSED,
            severity=Severity.INFO,
            correlation_id=correlation_id,
            door_id=door_id,
            sale_id=sale_id,
            payload={"sensor": "reed_switch"},
        )
    )

    events.append(
        log_event(
            machine_id=MACHINE_ID,
            event_type=EventType.STATE_CHANGE,
            severity=Severity.INFO,
            correlation_id=correlation_id,
            door_id=door_id,
            old_state="PAID_PENDING_OPEN",
            new_state="COMPLETED",
            payload={"fsm": "door_state"},
        )
    )

    return {
        "status": "sample_events_created",
        "events_created": len(events),
        "correlation_id": correlation_id,
        "sale_id": sale_id,
    }
