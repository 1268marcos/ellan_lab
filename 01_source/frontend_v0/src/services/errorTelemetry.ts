
export interface UiErrorTelemetryInput {
  domain: string;
  path: string;
  error: unknown;
  errorInfo?: unknown;
}

export interface UiErrorTelemetryEvent {
  eventId: string;
  domain: string;
  path: string;
  message: string;
  stack?: string;
  componentStack?: string;
  createdAt: string;
}

const STORAGE_KEY = "ellan_ui_error_events_v1";
const MAX_STORED_EVENTS = 50;
const ORDER_PICKUP_BASE =
  import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "/api/op";
const INTERNAL_TOKEN = String(import.meta.env.VITE_INTERNAL_TOKEN || "").trim();

function buildEventId() {
  return `uierr_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
}

function normalizeErrorMessage(error: unknown) {
  if (error instanceof Error) return error.message;
  return String(error || "Unknown UI error");
}

function normalizeErrorStack(error: unknown) {
  if (error instanceof Error) return error.stack;
  return undefined;
}

function readStoredEvents(): UiErrorTelemetryEvent[] {
  try {
    const raw = globalThis?.localStorage?.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function persistEvent(event: UiErrorTelemetryEvent) {
  try {
    const previous = readStoredEvents();
    const next = [event, ...previous].slice(0, MAX_STORED_EVENTS);
    globalThis?.localStorage?.setItem(STORAGE_KEY, JSON.stringify(next));
  } catch {
    // best effort only
  }
}

async function trySendToInternalIngest(event: UiErrorTelemetryEvent) {
  if (!INTERNAL_TOKEN) return;

  try {
    await fetch(`${ORDER_PICKUP_BASE}/internal/ui-errors`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Internal-Token": INTERNAL_TOKEN,
      },
      body: JSON.stringify(event),
      keepalive: true,
    });
  } catch {
    // best effort only
  }
}

function tryReportSentry(event: UiErrorTelemetryEvent, error: unknown) {
  try {
    const sentry = (globalThis as { Sentry?: { captureException?: Function; withScope?: Function } }).Sentry;
    if (!sentry?.captureException) return;
    const captureException = sentry.captureException;

    if (typeof sentry.withScope === "function") {
      sentry.withScope((scope: { setTag?: Function; setContext?: Function }) => {
        scope?.setTag?.("ui_error_domain", event.domain);
        scope?.setTag?.("ui_error_event_id", event.eventId);
        scope?.setContext?.("ui_error_event", event);
        captureException(error instanceof Error ? error : new Error(event.message));
      });
      return;
    }

    captureException(error instanceof Error ? error : new Error(event.message));
  } catch {
    // best effort only
  }
}

export function reportUiErrorTelemetry(input: UiErrorTelemetryInput): UiErrorTelemetryEvent {
  const event: UiErrorTelemetryEvent = {
    eventId: buildEventId(),
    domain: String(input.domain || "global"),
    path: String(input.path || ""),
    message: normalizeErrorMessage(input.error),
    stack: normalizeErrorStack(input.error),
    componentStack:
      typeof input.errorInfo === "object" && input.errorInfo !== null
        ? String((input.errorInfo as { componentStack?: string }).componentStack || "")
        : "",
    createdAt: new Date().toISOString(),
  };

  persistEvent(event);
  void trySendToInternalIngest(event);
  tryReportSentry(event, input.error);

  try {
    globalThis.dispatchEvent(new CustomEvent("ellan-ui-error", { detail: event }));
  } catch {
    // best effort only
  }

  console.error("[UI_TELEMETRY]", event);
  return event;
}

