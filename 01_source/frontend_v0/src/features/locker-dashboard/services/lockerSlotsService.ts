
type UnknownRecord = Record<string, unknown>;

export async function fetchLockerSlots({
  backendBase,
  lockerId,
  signal,
}: {
  backendBase: string;
  lockerId: string;
  signal?: AbortSignal;
}) {
  const res = await fetch(`${backendBase}/locker/slots`, {
    signal,
    headers: { "X-Locker-Id": lockerId },
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }

  return res.json() as Promise<unknown>;
}

export async function fetchCatalogSlots({
  backendBase,
  lockerId,
  signal,
}: {
  backendBase: string;
  lockerId: string;
  signal?: AbortSignal;
}) {
  const res = await fetch(`${backendBase}/catalog/slots`, {
    signal,
    headers: { "X-Locker-Id": lockerId },
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }

  return res.json() as Promise<unknown>;
}

export async function setLockerSlotState({
  backendBase,
  lockerId,
  slot,
  payload,
}: {
  backendBase: string;
  lockerId: string;
  slot: number | string;
  payload: UnknownRecord;
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

  return text ? (JSON.parse(text) as UnknownRecord) : { ok: true as const };
}

