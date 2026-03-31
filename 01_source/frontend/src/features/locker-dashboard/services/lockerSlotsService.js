// 01_source/frontend/src/features/locker-dashboard/services/lockerSlotsService.js

export async function fetchLockerSlots({
  backendBase,
  lockerId,
  signal,
}) {
  const res = await fetch(`${backendBase}/locker/slots`, {
    signal,
    headers: { "X-Locker-Id": lockerId },
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }

  return res.json();
}

export async function setLockerSlotState({
  backendBase,
  lockerId,
  slot,
  payload,
}) {
  const res = await fetch(`${backendBase}/locker/slots/${slot}/set-state`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Locker-Id": lockerId,
    },
    body: JSON.stringify(payload),
  });

  const text = await res.text();

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${text}`);
  }

  return text ? JSON.parse(text) : { ok: true };
}