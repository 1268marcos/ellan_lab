// 01_source/frontend/src/pages/public/PublicCatalogPage.jsx
// Catálogo ONLINE usando gateway + runtime, sem backend_sp/backend_pt e sem lockers hardcoded

import React, { useEffect, useMemo, useState, useCallback } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

const GATEWAY_BASE =
  import.meta.env.VITE_GATEWAY_BASE_URL || "http://localhost:8000";

const RUNTIME_BASE =
  import.meta.env.VITE_RUNTIME_BASE_URL || "http://localhost:8200";

const SORT_TYPES = {
  SLOT: "slot",
  NAME: "name",
  PRICE_ASC: "price_asc",
  PRICE_DESC: "price_desc",
};

const SORT_LABELS = {
  [SORT_TYPES.SLOT]: "🔢 Ordem de Gaveta",
  [SORT_TYPES.NAME]: "🍽️ Ordem de Sabor",
  [SORT_TYPES.PRICE_ASC]: "💰 Menor Preço",
  [SORT_TYPES.PRICE_DESC]: "💰 Maior Preço",
};

function formatCatalogSnapshot(iso) {
  if (!iso) return null;
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return null;
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);
}

function formatMoney(cents, currency, locale = undefined) {
  const value = Number(cents);
  if (!Number.isFinite(value)) return "-";

  const amount = value / 100;
  const safeCurrency = String(currency || "").trim().toUpperCase();

  try {
    if (safeCurrency) {
      return new Intl.NumberFormat(locale || undefined, {
        style: "currency",
        currency: safeCurrency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(amount);
    }

    return new Intl.NumberFormat(locale || undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    return safeCurrency
      ? `${amount.toFixed(2)} ${safeCurrency}`.trim()
      : amount.toFixed(2);
  }
}

function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);

  return debouncedValue;
}

function parseLockersResponse(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.items)) return data.items;
  return [];
}

function isLegacyLockerId(value) {
  return /^CACIFO-[A-Z]{2}-\d{3}$/i.test(String(value || "").trim());
}

function isCanonicalLockerId(value) {
  return /^[A-Z]{2}-[A-Z0-9]+(?:-[A-Z0-9]+)*-LK-\d{3}$/i.test(
    String(value || "").trim()
  );
}

function normalizeLockerId(locker) {
  const raw = String(
    locker?.locker_id || locker?.id || locker?.machine_id || ""
  ).trim();

  if (!raw) return "";

  if (isLegacyLockerId(raw)) {
    return "";
  }

  return raw.toUpperCase();
}

function normalizeLockerItem(locker) {
  const address =
    locker?.address && typeof locker.address === "object"
      ? locker.address
      : {
          address: locker?.address || "",
          number: locker?.number ?? "",
          additional_information: locker?.additional_information || "",
          locality: locker?.locality || "",
          city: locker?.city || "",
          federative_unit: locker?.federative_unit || "",
          postal_code: locker?.postal_code || "",
          country: locker?.country || "",
        };

  const normalizedLockerId = normalizeLockerId(locker);

  return {
    locker_id: normalizedLockerId,
    label:
      locker?.display_name ||
      locker?.locker_id ||
      locker?.id ||
      locker?.machine_id ||
      "",
    address:
      [
        [address.address, address.number].filter(Boolean).join(", "),
        address.additional_information || "",
        address.locality || "",
        [address.city, address.federative_unit].filter(Boolean).join(" / "),
        address.postal_code || "",
        address.country || "",
      ]
        .map((item) => String(item || "").trim())
        .filter(Boolean)
        .join(" • ") || "-",
    region: String(locker?.region || "").trim().toUpperCase(),
    active: Boolean(locker?.active),
  };
}

function parseError(data) {
  if (typeof data?.detail === "string") return data.detail;
  if (typeof data?.detail === "object" && data?.detail) {
    return JSON.stringify(data.detail);
  }
  if (typeof data?.message === "string") return data.message;
  return JSON.stringify(data);
}

function resolveRegion(raw) {
  return String(raw || "").trim().toUpperCase();
}

function resolveInitialLockerId(rawLockerId) {
  const raw = String(rawLockerId || "").trim().toUpperCase();

  if (!raw) return "";
  if (isLegacyLockerId(raw)) return "";
  if (isCanonicalLockerId(raw)) return raw;

  return raw;
}

function highlightSearchTerm(text, search) {
  if (!search) return text;

  const safeText = String(text || "");
  const safeSearch = String(search || "").trim();

  if (!safeSearch) return safeText;

  const escaped = safeSearch.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const parts = safeText.split(new RegExp(`(${escaped})`, "gi"));

  return parts.map((part, index) =>
    part.toLowerCase() === safeSearch.toLowerCase() ? (
      <mark
        key={`${part}-${index}`}
        style={{
          background: "#fef3c7",
          color: "#92400e",
          padding: "0 2px",
          borderRadius: "var(--radius-sm)",
        }}
      >
        {part}
      </mark>
    ) : (
      part
    )
  );
}

export default function PublicCatalogPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const initialRegion = resolveRegion(searchParams.get("region")) || "SP";
  const initialLockerId = resolveInitialLockerId(searchParams.get("locker_id"));

  const [region, setRegion] = useState(initialRegion);
  const [lockerId, setLockerId] = useState(initialLockerId);
  const [lockers, setLockers] = useState([]);
  const [items, setItems] = useState([]);

  const [loadingLockers, setLoadingLockers] = useState(false);
  const [loadingCatalog, setLoadingCatalog] = useState(false);
  const [submittingSlot, setSubmittingSlot] = useState(null);

  const [error, setError] = useState("");
  const [selectedLockerDetails, setSelectedLockerDetails] = useState(null);
  const [expandedCards, setExpandedCards] = useState(new Set());
  const [sortType, setSortType] = useState(SORT_TYPES.SLOT);
  const [searchTerm, setSearchTerm] = useState("");
  /** Quando o runtime não manda updated_at, ainda exibimos o horário do último GET do catálogo. */
  const [catalogFetchedAt, setCatalogFetchedAt] = useState(null);

  const debouncedSearchTerm = useDebounce(searchTerm, 300);

  useEffect(() => {
    const params = new URLSearchParams(searchParams);
    params.set("region", region || "SP");

    if (lockerId) {
      params.set("locker_id", lockerId);
    } else {
      params.delete("locker_id");
    }

    setSearchParams(params, { replace: true });
  }, [region, lockerId, searchParams, setSearchParams]);

  useEffect(() => {
    async function loadLockers() {
      setLoadingLockers(true);
      setError("");

      try {
        const res = await fetch(
          `${GATEWAY_BASE}/lockers?region=${encodeURIComponent(region)}&active_only=true`
        );
        const data = await res.json().catch(() => ({}));

        if (!res.ok) {
          throw new Error(parseError(data));
        }

        const normalized = parseLockersResponse(data)
          .map(normalizeLockerItem)
          .filter((item) => item.active && item.locker_id)
          .sort((a, b) =>
            a.label.localeCompare(b.label, undefined, { sensitivity: "base" })
          );

        if (!normalized.length) {
          throw new Error(
            `Nenhum locker canônico ativo encontrado para a região ${region}.`
          );
        }

        setLockers(normalized);

        setLockerId((prev) => {
          const safePrev = resolveInitialLockerId(prev);

          if (
            safePrev &&
            normalized.some((item) => item.locker_id === safePrev)
          ) {
            return safePrev;
          }

          return normalized[0].locker_id;
        });
      } catch (e) {
        setLockers([]);
        setLockerId("");
        setItems([]);
        setSelectedLockerDetails(null);
        setError(String(e?.message || e));
      } finally {
        setLoadingLockers(false);
      }
    }

    loadLockers();
  }, [region]);

  useEffect(() => {
    const locker = lockers.find((item) => item.locker_id === lockerId) || null;
    setSelectedLockerDetails(locker);
  }, [lockers, lockerId]);

  useEffect(() => {
    async function loadCatalog() {
      if (!lockerId) {
        setItems([]);
        setExpandedCards(new Set());
        setCatalogFetchedAt(null);
        return;
      }

      setLoadingCatalog(true);
      setError("");
      setCatalogFetchedAt(null);

      try {
        const headers = { "X-Locker-Id": lockerId };

        const [catalogRes, lockerStateRes] = await Promise.all([
          fetch(`${RUNTIME_BASE}/catalog/slots`, { headers }),
          fetch(`${RUNTIME_BASE}/locker/slots`, { headers }),
        ]);

        const catalogData = await catalogRes.json().catch(() => []);
        const lockerStateData = await lockerStateRes.json().catch(() => []);

        if (!catalogRes.ok) {
          throw new Error(parseError(catalogData));
        }

        if (!lockerStateRes.ok) {
          throw new Error(parseError(lockerStateData));
        }

        const lockerStateMap = {};
        for (const row of Array.isArray(lockerStateData) ? lockerStateData : []) {
          const stateSlot = Number(row.slot);
          if (!Number.isFinite(stateSlot) || stateSlot <= 0) continue;

          lockerStateMap[stateSlot] = {
            state: row.state || "AVAILABLE",
            product_id: row.product_id ?? null,
            updated_at: row.updated_at ?? null,
          };
        }

        const normalized = (Array.isArray(catalogData) ? catalogData : [])
          .map((item) => {
            const slotNumber = Number(item.slot);

            if (!Number.isFinite(slotNumber) || slotNumber <= 0) {
              return null;
            }

            const runtimeState = lockerStateMap[slotNumber]?.state || "AVAILABLE";
            const isOperationallyAvailable = runtimeState === "AVAILABLE";

            return {
              locker_id: item.locker_id || lockerId,
              slot: slotNumber,
              sku_id: item.sku_id || null,
              name: item.name || "Produto sem nome",
              description: item.description || "",
              amount_cents: Number(item.amount_cents || 0),
              currency: String(item.currency || "").trim().toUpperCase() || "",
              imageURL: item.imageURL || "",
              is_active: Boolean(item.is_active),
              locker_state: runtimeState,
              is_operationally_available: isOperationallyAvailable,
              updated_at:
                item.updated_at || lockerStateMap[slotNumber]?.updated_at || null,
            };
          })
          .filter(Boolean)
          .filter((item) => item.is_active && item.sku_id)
          .sort((a, b) => a.slot - b.slot);

        setItems(normalized);
        setExpandedCards(new Set());
        setCatalogFetchedAt(new Date());
      } catch (e) {
        setError(String(e?.message || e));
        setItems([]);
        setCatalogFetchedAt(null);
      } finally {
        setLoadingCatalog(false);
      }
    }

    loadCatalog();
  }, [lockerId]);

  const filteredBySearch = useMemo(() => {
    if (!debouncedSearchTerm.trim()) return items;

    const searchLower = debouncedSearchTerm.toLowerCase().trim();
    return items.filter(
      (item) =>
        item.name.toLowerCase().includes(searchLower) ||
        (item.description && item.description.toLowerCase().includes(searchLower))
    );
  }, [items, debouncedSearchTerm]);

  const sortedItems = useMemo(() => {
    if (!filteredBySearch.length) return [];

    const itemsCopy = [...filteredBySearch];

    switch (sortType) {
      case SORT_TYPES.SLOT:
        return itemsCopy.sort((a, b) => a.slot - b.slot);
      case SORT_TYPES.NAME:
        return itemsCopy.sort((a, b) =>
          a.name.localeCompare(b.name, undefined, { sensitivity: "base" })
        );
      case SORT_TYPES.PRICE_ASC:
        return itemsCopy.sort((a, b) => a.amount_cents - b.amount_cents);
      case SORT_TYPES.PRICE_DESC:
        return itemsCopy.sort((a, b) => b.amount_cents - a.amount_cents);
      default:
        return itemsCopy;
    }
  }, [filteredBySearch, sortType]);

  /** Gavetas com estado operacional AVAILABLE (compra liberada). */
  const availableForPurchaseCount = useMemo(
    () => filteredBySearch.filter((i) => i.is_operationally_available).length,
    [filteredBySearch]
  );

  /** Maior updated_at conhecido entre catálogo e estados do locker (referência de frescor). */
  const catalogStateSnapshotAt = useMemo(() => {
    let maxMs = null;
    for (const row of items) {
      if (!row?.updated_at) continue;
      const ms = new Date(row.updated_at).getTime();
      if (Number.isNaN(ms)) continue;
      if (maxMs == null || ms > maxMs) maxMs = ms;
    }
    return maxMs != null ? new Date(maxMs) : null;
  }, [items]);

  const displaySnapshotAt = catalogStateSnapshotAt || catalogFetchedAt;

  const catalogSnapshotLabel = displaySnapshotAt
    ? formatCatalogSnapshot(displaySnapshotAt.toISOString())
    : null;

  const showCatalogMetrics = !loadingCatalog && !loadingLockers && Boolean(lockerId);

  const clearSearch = useCallback(() => {
    setSearchTerm("");
  }, []);

  async function handleReserve(item) {
    if (!item?.sku_id || !item?.slot || !lockerId) return;

    setSubmittingSlot(item.slot);
    setError("");

    try {
      navigate(
        `/checkout?region=${encodeURIComponent(region)}&locker_id=${encodeURIComponent(
          lockerId
        )}&sku_id=${encodeURIComponent(item.sku_id)}&slot=${encodeURIComponent(item.slot)}`
      );
    } finally {
      setSubmittingSlot(null);
    }
  }

  const toggleExpand = (slotId) => {
    setExpandedCards((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(slotId)) {
        newSet.delete(slotId);
      } else {
        newSet.add(slotId);
      }
      return newSet;
    });
  };

  const SkeletonCard = () => (
    <article
      className="card skeleton-card"
      aria-label="Carregando produto"
      style={{ animation: "pulse 1.5s ease-in-out infinite" }}
    >
      <div style={{ display: "flex", gap: "var(--spacing-4)", alignItems: "center" }}>
        <div
          style={{
            width: 60,
            height: 60,
            background: "#e5e7eb",
            borderRadius: "var(--radius-lg)",
          }}
        />
        <div style={{ flex: 1 }}>
          <div
            style={{
              width: "60%",
              height: 20,
              background: "#e5e7eb",
              borderRadius: "var(--radius-md)",
              marginBottom: "var(--spacing-2)",
            }}
          />
          <div
            style={{
              width: "40%",
              height: 16,
              background: "#e5e7eb",
              borderRadius: "var(--radius-md)",
            }}
          />
        </div>
      </div>
    </article>
  );

  return (
    <main
      className="catalog-page"
      style={{
        minHeight: "100vh",
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        padding: "var(--spacing-4)",
      }}
    >
      <div className="container" style={{ maxWidth: "1200px", margin: "0 auto" }}>
        <section
          className="card card--hero"
          aria-labelledby="catalog-title"
          style={{
            borderRadius: "var(--radius-2xl)",
            padding: "var(--spacing-6)",
            marginBottom: "var(--spacing-6)",
            background: "rgba(255,255,255,0.95)",
            boxShadow: "var(--shadow-xl)",
          }}
        >
          <span
            className="eyebrow"
            style={{
              display: "inline-block",
              marginBottom: "var(--spacing-2)",
              fontSize: "var(--font-size-xs)",
              fontWeight: 600,
              letterSpacing: "0.05em",
              textTransform: "uppercase",
              color: "var(--color-primary)",
            }}
          >
            📦 Catálogo Público
          </span>

          <h1
            id="catalog-title"
            style={{
              margin: 0,
              fontSize: "var(--font-size-3xl)",
              fontWeight: 800,
              lineHeight: 1.2,
              background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
            }}
          >
            Escolha seu produto
          </h1>

          <p
            style={{
              marginTop: "var(--spacing-3)",
              marginBottom: 0,
              fontSize: "var(--font-size-base)",
              lineHeight: 1.6,
              color: "var(--color-text-muted)",
              maxWidth: "600px",
            }}
          >
            Cada gaveta contém um produto único com preço já definido.
          </p>

          <div
            className="filters-toolbar"
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
              gap: "var(--spacing-3)",
              marginTop: "var(--spacing-5)",
            }}
            role="group"
            aria-label="Filtros de catálogo"
          >
            <div className="form-group">
              <label htmlFor="region-select" className="form-label">
                🌎 Região
              </label>
              <select
                id="region-select"
                value={region}
                onChange={(e) => setRegion(resolveRegion(e.target.value) || "SP")}
                className="form-input"
                aria-describedby="region-help"
              >
                <option value="SP">🇧🇷 São Paulo</option>
                <option value="PT">🇵🇹 Portugal</option>
              </select>
              <span id="region-help" className="form-help">
                Selecione sua região
              </span>
            </div>

            <div className="form-group">
              <label htmlFor="locker-select" className="form-label">
                📍 Ponto de retirada
              </label>
              <select
                id="locker-select"
                value={lockerId}
                onChange={(e) => setLockerId(e.target.value)}
                className="form-input"
                aria-describedby="locker-help"
                disabled={loadingLockers || !lockers.length}
              >
                {!lockers.length ? (
                  <option value="">Nenhum locker disponível</option>
                ) : (
                  lockers.map((item) => (
                    <option key={item.locker_id} value={item.locker_id}>
                      {item.label}
                    </option>
                  ))
                )}
              </select>
              {selectedLockerDetails ? (
                <span id="locker-help" className="form-help">
                  📮 {selectedLockerDetails.address}
                </span>
              ) : (
                <span id="locker-help" className="form-help">
                  {loadingLockers
                    ? "Carregando pontos de retirada..."
                    : "Selecione um ponto de retirada"}
                </span>
              )}
            </div>
          </div>

          <div
            className="search-bar"
            style={{
              marginTop: "var(--spacing-5)",
              marginBottom: "var(--spacing-3)",
            }}
          >
            <div style={{ position: "relative", width: "100%" }}>
              <div
                style={{
                  position: "absolute",
                  left: "var(--spacing-3)",
                  top: "50%",
                  transform: "translateY(-50%)",
                  fontSize: "var(--font-size-lg)",
                  pointerEvents: "none",
                  color: "#64748b",
                }}
              >
                🔍
              </div>
              <input
                type="text"
                id="search-product"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Buscar por sabor ou descrição..."
                style={{
                  width: "100%",
                  padding:
                    "var(--spacing-3) var(--spacing-3) var(--spacing-3) calc(var(--spacing-3) + 32px)",
                  fontSize: "var(--font-size-base)",
                  borderRadius: "var(--radius-lg)",
                  border: "1px solid #e2e8f0",
                  background: "white",
                  transition: "all var(--transition-base)",
                  outline: "none",
                }}
                aria-label="Buscar produtos por nome ou descrição"
              />
              {searchTerm ? (
                <button
                  onClick={clearSearch}
                  style={{
                    position: "absolute",
                    right: "var(--spacing-3)",
                    top: "50%",
                    transform: "translateY(-50%)",
                    background: "none",
                    border: "none",
                    fontSize: "var(--font-size-lg)",
                    cursor: "pointer",
                    padding: "var(--spacing-1)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    borderRadius: "var(--radius-full)",
                  }}
                  aria-label="Limpar busca"
                >
                  ✕
                </button>
              ) : null}
            </div>
            {debouncedSearchTerm ? (
              <p
                style={{
                  marginTop: "var(--spacing-2)",
                  fontSize: "var(--font-size-xs)",
                  color: "#f8fafc",
                  textAlign: "right",
                }}
              >
                {filteredBySearch.length}{" "}
                {filteredBySearch.length === 1 ? "resultado" : "resultados"} encontrados
              </p>
            ) : null}
          </div>

          <div
            style={{
              display: "flex",
              gap: "var(--spacing-3)",
              marginTop: "var(--spacing-4)",
              paddingTop: "var(--spacing-4)",
              borderTop: "1px solid var(--color-border)",
              flexWrap: "wrap",
            }}
          >
            <Link to="/" className="btn btn--secondary">
              ← Voltar
            </Link>
            <Link to="/meus-pedidos" className="btn btn--secondary">
              📋 Meus Pedidos
            </Link>
          </div>
        </section>

        {error ? (
          <div
            className="error-banner"
            role="alert"
            style={{
              marginBottom: "var(--spacing-4)",
              padding: "var(--spacing-4)",
              borderRadius: "var(--radius-lg)",
              background: "#fef2f2",
              border: "1px solid #fecaca",
              display: "flex",
              alignItems: "center",
              gap: "var(--spacing-3)",
              flexWrap: "wrap",
            }}
          >
            <span style={{ fontSize: "20px" }}>⚠️</span>
            <div style={{ flex: 1, color: "#991b1b", fontSize: "var(--font-size-sm)" }}>
              <strong>Ops!</strong> {error}
            </div>
            <button
              onClick={() => window.location.reload()}
              className="btn btn--danger"
              style={{ padding: "var(--spacing-2) var(--spacing-4)", fontSize: "var(--font-size-sm)" }}
            >
              Tentar novamente
            </button>
          </div>
        ) : null}

        {loadingCatalog || loadingLockers ? (
          <div
            className="products-grid"
            style={{
              display: "grid",
              gap: "var(--spacing-3)",
              gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
            }}
          >
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : (
          <>
            <div
              className="results-header"
              style={{
                marginBottom: "var(--spacing-4)",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: "var(--spacing-3)",
                background: "rgba(255,255,255,0.1)",
                padding: "var(--spacing-3)",
                borderRadius: "var(--radius-lg)",
                backdropFilter: "blur(10px)",
              }}
            >
              <div>
                <h2
                  style={{
                    fontSize: "var(--font-size-xl)",
                    fontWeight: 700,
                    color: "white",
                    margin: 0,
                  }}
                >
                  Produtos disponíveis
                  {showCatalogMetrics ? (
                    <span
                      style={{
                        fontSize: "var(--font-size-base)",
                        fontWeight: 500,
                        color: "#f8fafc",
                        marginLeft: "var(--spacing-2)",
                      }}
                    >
                      ({availableForPurchaseCount})
                    </span>
                  ) : null}
                </h2>
                {showCatalogMetrics ? (
                  <p
                    style={{
                      margin: "var(--spacing-2) 0 0 0",
                      fontSize: "var(--font-size-sm)",
                      fontWeight: 500,
                      color: "rgba(248, 250, 252, 0.92)",
                      maxWidth: 560,
                      lineHeight: 1.45,
                    }}
                  >
                    {catalogSnapshotLabel && displaySnapshotAt ? (
                      catalogStateSnapshotAt ? (
                        <>
                          Última leitura dos estados das gavetas:{" "}
                          <time dateTime={displaySnapshotAt.toISOString()}>
                            {catalogSnapshotLabel}
                          </time>
                          .
                        </>
                      ) : (
                        <>
                          Catálogo carregado em{" "}
                          <time dateTime={displaySnapshotAt.toISOString()}>
                            {catalogSnapshotLabel}
                          </time>{" "}
                          (sem horário por gaveta no servidor).
                        </>
                      )
                    ) : (
                      <>Horário da última leitura dos estados indisponível.</>
                    )}
                    {sortedItems.length > 0 ? (
                      <>
                        {" "}
                        Listando {sortedItems.length}{" "}
                        {sortedItems.length === 1 ? "posição" : "posições"} do catálogo
                        {debouncedSearchTerm.trim() ? " (filtro da busca)" : ""}.
                      </>
                    ) : null}
                  </p>
                ) : null}
              </div>

              <div
                className="sort-selector"
                style={{
                  display: "flex",
                  gap: "var(--spacing-2)",
                  flexWrap: "wrap",
                  alignItems: "center",
                }}
              >
                <label
                  htmlFor="sort-select"
                  style={{
                    fontSize: "var(--font-size-sm)",
                    fontWeight: 600,
                    color: "white",
                    marginRight: "var(--spacing-1)",
                  }}
                >
                  Ordenar por:
                </label>
                <select
                  id="sort-select"
                  value={sortType}
                  onChange={(e) => setSortType(e.target.value)}
                  style={{
                    padding: "var(--spacing-2) var(--spacing-3)",
                    borderRadius: "var(--radius-md)",
                    border: "1px solid rgba(255,255,255,0.3)",
                    background: "rgba(255,255,255,0.95)",
                    fontSize: "var(--font-size-sm)",
                    fontWeight: 500,
                    cursor: "pointer",
                    outline: "none",
                  }}
                  aria-label="Ordenar produtos"
                >
                  <option value={SORT_TYPES.SLOT}>{SORT_LABELS[SORT_TYPES.SLOT]}</option>
                  <option value={SORT_TYPES.NAME}>{SORT_LABELS[SORT_TYPES.NAME]}</option>
                  <option value={SORT_TYPES.PRICE_ASC}>{SORT_LABELS[SORT_TYPES.PRICE_ASC]}</option>
                  <option value={SORT_TYPES.PRICE_DESC}>{SORT_LABELS[SORT_TYPES.PRICE_DESC]}</option>
                </select>
              </div>
            </div>

            <div
              className="products-grid"
              style={{
                display: "grid",
                gap: "var(--spacing-3)",
                gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
              }}
              aria-label="Lista completa do catálogo por gaveta, incluindo indisponíveis para compra"
            >
              {sortedItems.length === 0 ? (
                <article
                  className="card empty-state"
                  style={{
                    gridColumn: "1 / -1",
                    textAlign: "center",
                    padding: "var(--spacing-10)",
                    background: "white",
                  }}
                >
                  <div style={{ fontSize: "48px", marginBottom: "var(--spacing-4)" }}>
                    {debouncedSearchTerm ? "🔍" : "📭"}
                  </div>
                  <h3
                    style={{
                      fontSize: "var(--font-size-xl)",
                      fontWeight: 600,
                      color: "var(--color-text)",
                      marginBottom: "var(--spacing-3)",
                    }}
                  >
                    {debouncedSearchTerm
                      ? `Nenhum produto encontrado para "${debouncedSearchTerm}"`
                      : "Nenhum produto disponível"}
                  </h3>
                  <p
                    style={{
                      fontSize: "var(--font-size-sm)",
                      color: "var(--color-text-muted)",
                      marginBottom: "var(--spacing-4)",
                    }}
                  >
                    {debouncedSearchTerm
                      ? "Tente buscar por outro sabor ou verifique a ortografia."
                      : "Não encontramos produtos ativos para este locker."}
                  </p>
                  {debouncedSearchTerm ? (
                    <button
                      onClick={clearSearch}
                      className="btn btn--primary"
                      style={{ padding: "var(--spacing-2) var(--spacing-6)" }}
                    >
                      Limpar busca
                    </button>
                  ) : null}
                </article>
              ) : (
                sortedItems.map((item) => {
                  const isExpanded = expandedCards.has(item.slot);
                  const isNameHighlighted = sortType === SORT_TYPES.NAME;
                  const isPriceHighlighted =
                    sortType === SORT_TYPES.PRICE_ASC || sortType === SORT_TYPES.PRICE_DESC;

                  return (
                    <article
                      key={`${item.locker_id}-${item.slot}`}
                      className="card product-card"
                      style={{
                        background: "white",
                        borderRadius: "var(--radius-xl)",
                        padding: "var(--spacing-4)",
                        boxShadow: "var(--shadow-md)",
                        transition: "all var(--transition-base)",
                        border:
                          sortType === SORT_TYPES.NAME && isExpanded
                            ? "2px solid #667eea"
                            : "none",
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          gap: "var(--spacing-3)",
                        }}
                      >
                        <div
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "var(--spacing-3)",
                            flex: 1,
                          }}
                        >
                          <div
                            style={{
                              width: 50,
                              height: 50,
                              background: isNameHighlighted
                                ? "#e5e7eb"
                                : "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                              borderRadius: "var(--radius-lg)",
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              fontSize: "var(--font-size-xl)",
                              fontWeight: 800,
                              color: isNameHighlighted ? "#4a5568" : "white",
                              flexShrink: 0,
                            }}
                          >
                            {item.slot}
                          </div>

                          <div style={{ flex: 1 }}>
                            <div
                              style={{
                                fontSize: isNameHighlighted
                                  ? "var(--font-size-lg)"
                                  : "var(--font-size-base)",
                                fontWeight: isNameHighlighted ? 800 : 700,
                                color: isNameHighlighted ? "#667eea" : "var(--color-text)",
                                marginBottom: "var(--spacing-1)",
                                lineHeight: 1.3,
                              }}
                            >
                              {debouncedSearchTerm
                                ? highlightSearchTerm(item.name, debouncedSearchTerm)
                                : item.name}
                            </div>

                            <div
                              style={{
                                fontSize: isPriceHighlighted
                                  ? "var(--font-size-xl)"
                                  : "var(--font-size-lg)",
                                fontWeight: isPriceHighlighted ? 900 : 800,
                                color: isPriceHighlighted ? "#92400e" : "#1e3a8a",
                              }}
                            >
                              {formatMoney(item.amount_cents, item.currency)}
                            </div>

                            <div
                              style={{
                                marginTop: 6,
                                fontSize: 12,
                                color:
                                  item.locker_state === "AVAILABLE" ? "#047857" : "#b91c1c",
                                fontWeight: 700,
                              }}
                            >
                              Estado: {item.locker_state || "-"}
                            </div>
                          </div>
                        </div>

                        <div style={{ display: "flex", gap: "var(--spacing-2)", alignItems: "center" }}>
                          <button
                            onClick={() => handleReserve(item)}
                            disabled={
                              submittingSlot === item.slot || !item.is_operationally_available
                            }
                            className="btn btn--primary"
                            style={{
                              width: 50,
                              height: 50,
                              borderRadius: "var(--radius-lg)",
                              padding: 0,
                              fontSize: "20px",
                            }}
                            aria-label={`Reservar ${item.name} - Gaveta ${item.slot}`}
                          >
                            {submittingSlot === item.slot ? "⏳" : "🛒"}
                          </button>

                          <button
                            onClick={() => toggleExpand(item.slot)}
                            className="btn btn--secondary"
                            style={{
                              width: 40,
                              height: 40,
                              borderRadius: "var(--radius-md)",
                              padding: 0,
                              fontSize: "var(--font-size-sm)",
                            }}
                            aria-label={isExpanded ? "Recolher detalhes" : "Expandir detalhes"}
                            aria-expanded={isExpanded}
                          >
                            {isExpanded ? "▲" : "▼"}
                          </button>
                        </div>
                      </div>

                      {isExpanded ? (
                        <div
                          style={{
                            marginTop: "var(--spacing-4)",
                            paddingTop: "var(--spacing-4)",
                            borderTop: "1px solid var(--color-border)",
                          }}
                        >
                          <div
                            style={{
                              display: "grid",
                              gap: "var(--spacing-2)",
                              fontSize: "var(--font-size-sm)",
                            }}
                          >
                            <div style={{ display: "flex", justifyContent: "space-between" }}>
                              <span style={{ fontWeight: 600, color: "var(--color-text-muted)" }}>
                                Gaveta:
                              </span>
                              <span style={{ fontWeight: 700 }}>{item.slot}</span>
                            </div>
                            <div style={{ display: "flex", justifyContent: "space-between" }}>
                              <span style={{ fontWeight: 600, color: "var(--color-text-muted)" }}>
                                SKU:
                              </span>
                              <span>{item.sku_id}</span>
                            </div>
                            <div style={{ display: "flex", justifyContent: "space-between" }}>
                              <span style={{ fontWeight: 600, color: "var(--color-text-muted)" }}>
                                Moeda:
                              </span>
                              <span>{item.currency || "-"}</span>
                            </div>
                            <div style={{ display: "flex", justifyContent: "space-between" }}>
                              <span style={{ fontWeight: 600, color: "var(--color-text-muted)" }}>
                                Estado operacional:
                              </span>
                              <span>{item.locker_state}</span>
                            </div>
                            <div style={{ display: "flex", justifyContent: "space-between" }}>
                              <span style={{ fontWeight: 600, color: "var(--color-text-muted)" }}>
                                Atualizado:
                              </span>
                              <span>
                                {item.updated_at
                                  ? new Date(item.updated_at).toLocaleDateString(undefined, {
                                      day: "2-digit",
                                      month: "short",
                                      year: "numeric",
                                    })
                                  : "-"}
                              </span>
                            </div>
                          </div>
                        </div>
                      ) : null}
                    </article>
                  );
                })
              )}
            </div>
          </>
        )}
      </div>
    </main>
  );
}