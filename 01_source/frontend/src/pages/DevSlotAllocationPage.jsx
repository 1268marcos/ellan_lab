import React, { useEffect, useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";

const GATEWAY_BASE =
  import.meta.env.VITE_GATEWAY_BASE_URL || "http://localhost:8000";
const RUNTIME_BASE =
  import.meta.env.VITE_RUNTIME_BASE_URL || "http://localhost:8200";
const INTERNAL_TOKEN = import.meta.env.VITE_INTERNAL_TOKEN || "";

function isDevBypassEnabled() {
  return String(import.meta.env.VITE_DEV_BYPASS_AUTH || "").toLowerCase() === "true";
}

function getAllowedRoleSet() {
  const raw =
    String(import.meta.env.VITE_SLOT_ALLOCATION_ALLOWED_ROLES || "").trim() ||
    "LOCKER_SLOT_MANAGER,ADMIN";
  return new Set(
    raw
      .split(",")
      .map((item) => item.trim().toUpperCase())
      .filter(Boolean)
  );
}

function userRolesFromProfile(user) {
  if (!user) return [];

  if (Array.isArray(user.roles)) return user.roles.map((item) => String(item));
  if (typeof user.role === "string") return [user.role];
  if (typeof user.category === "string") return [user.category];
  if (Array.isArray(user.categories)) return user.categories.map((item) => String(item));
  return [];
}

function parseLockersResponse(data) {
  if (Array.isArray(data?.items)) return data.items;
  if (Array.isArray(data?.lockers)) return data.lockers;
  if (Array.isArray(data)) return data;
  return [];
}

function normalizeLocker(locker) {
  return {
    locker_id: String(locker?.locker_id || locker?.id || "").trim(),
    display_name:
      locker?.display_name ||
      locker?.locker_id ||
      locker?.id ||
      "Locker sem nome",
    active: Boolean(locker?.active),
  };
}

export default function DevSlotAllocationPage() {
  const { user } = useAuth();

  const [region, setRegion] = useState("SP");
  const [lockers, setLockers] = useState([]);
  const [selectedLockerId, setSelectedLockerId] = useState("");

  const [loadingLockers, setLoadingLockers] = useState(false);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [savingBatch, setSavingBatch] = useState(false);
  const [savingSlot, setSavingSlot] = useState(null);

  const [slots, setSlots] = useState([]);
  const [skuOptions, setSkuOptions] = useState([]);
  const [slotDraftMap, setSlotDraftMap] = useState({});

  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const allowedRoles = useMemo(() => getAllowedRoleSet(), []);
  const currentRoles = useMemo(() => userRolesFromProfile(user), [user]);

  const canAccess = useMemo(() => {
    if (isDevBypassEnabled()) return true;
    const normalized = currentRoles.map((item) => item.trim().toUpperCase());
    return normalized.some((role) => allowedRoles.has(role));
  }, [allowedRoles, currentRoles]);

  async function fetchLockers() {
    setLoadingLockers(true);
    setError("");
    setMessage("");

    try {
      const res = await fetch(
        `${GATEWAY_BASE}/lockers?region=${encodeURIComponent(region)}&active_only=true`
      );
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data?.detail ? JSON.stringify(data.detail) : JSON.stringify(data));
      }

      const items = parseLockersResponse(data)
        .map(normalizeLocker)
        .filter((item) => item.active && item.locker_id);

      setLockers(items);
      setSelectedLockerId((prev) => {
        if (prev && items.some((item) => item.locker_id === prev)) return prev;
        return items[0]?.locker_id || "";
      });
    } catch (e) {
      setLockers([]);
      setSelectedLockerId("");
      setError(String(e?.message || e));
    } finally {
      setLoadingLockers(false);
    }
  }

  async function fetchSlotsAndCatalog() {
    if (!selectedLockerId) {
      setSlots([]);
      setSkuOptions([]);
      setSlotDraftMap({});
      return;
    }

    setLoadingSlots(true);
    setError("");
    setMessage("");

    try {
      const res = await fetch(`${RUNTIME_BASE}/dev/catalog/slots`, {
        headers: {
          "X-Locker-Id": selectedLockerId,
          "X-Internal-Token": INTERNAL_TOKEN,
        },
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data?.message || data?.detail || JSON.stringify(data));
      }

      const nextSlots = Array.isArray(data?.slots) ? data.slots : [];
      const nextSkus = Array.isArray(data?.skus) ? data.skus : [];
      const nextDraft = {};

      for (const slot of nextSlots) {
        nextDraft[String(slot.slot)] = String(slot.sku_id || "");
      }

      setSlots(nextSlots);
      setSkuOptions(nextSkus);
      setSlotDraftMap(nextDraft);
    } catch (e) {
      setSlots([]);
      setSkuOptions([]);
      setSlotDraftMap({});
      setError(String(e?.message || e));
    } finally {
      setLoadingSlots(false);
    }
  }

  useEffect(() => {
    fetchLockers();
  }, [region]);

  useEffect(() => {
    fetchSlotsAndCatalog();
  }, [selectedLockerId]);

  const dirtySlots = useMemo(() => {
    const items = [];
    for (const slot of slots) {
      const key = String(slot.slot);
      const currentSku = String(slot.sku_id || "");
      const draftSku = String(slotDraftMap[key] || "");
      if (currentSku !== draftSku) {
        items.push({ slot: Number(slot.slot), sku_id: draftSku });
      }
    }
    return items;
  }, [slots, slotDraftMap]);

  async function saveSingleSlot(slotNumber) {
    const draftSku = String(slotDraftMap[String(slotNumber)] || "");
    if (!draftSku) {
      setError("Selecione um SKU antes de salvar o slot.");
      return;
    }

    setSavingSlot(slotNumber);
    setError("");
    setMessage("");

    try {
      const res = await fetch(`${RUNTIME_BASE}/dev/catalog/slots/${slotNumber}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Locker-Id": selectedLockerId,
          "X-Internal-Token": INTERNAL_TOKEN,
        },
        body: JSON.stringify({ slot: Number(slotNumber), sku_id: draftSku }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data?.message || data?.detail || JSON.stringify(data));
      }

      setMessage(`Slot ${slotNumber} atualizado para ${draftSku}.`);
      await fetchSlotsAndCatalog();
    } catch (e) {
      setError(String(e?.message || e));
    } finally {
      setSavingSlot(null);
    }
  }

  async function saveAllChanges() {
    if (!dirtySlots.length) {
      setMessage("Nenhuma alteração pendente.");
      return;
    }

    const invalid = dirtySlots.find((item) => !item.sku_id);
    if (invalid) {
      setError(`O slot ${invalid.slot} está sem SKU. Defina um SKU válido.`);
      return;
    }

    setSavingBatch(true);
    setError("");
    setMessage("");

    try {
      const res = await fetch(`${RUNTIME_BASE}/dev/catalog/slot-overrides/batch`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Locker-Id": selectedLockerId,
          "X-Internal-Token": INTERNAL_TOKEN,
        },
        body: JSON.stringify({ allocations: dirtySlots }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data?.message || data?.detail || JSON.stringify(data));
      }

      setMessage(`Alocação em lote concluída (${data?.updated_count || dirtySlots.length} slots).`);
      await fetchSlotsAndCatalog();
    } catch (e) {
      setError(String(e?.message || e));
    } finally {
      setSavingBatch(false);
    }
  }

  if (!canAccess) {
    return (
      <div style={pageStyle}>
        <section style={cardStyle}>
          <h1 style={{ marginTop: 0 }}>Ops — Alocação de Produtos por Slot</h1>
          <div style={warningStyle}>
            Esta interface exige categoria/perfil autorizado. Defina um papel permitido em
            <b> VITE_SLOT_ALLOCATION_ALLOWED_ROLES</b> ou use ambiente de desenvolvimento com
            <b> VITE_DEV_BYPASS_AUTH=true</b>.
          </div>
          <div style={summaryStyle}>
            <div><b>Perfis atuais:</b> {currentRoles.join(", ") || "-"}</div>
            <div><b>Perfis exigidos:</b> {Array.from(allowedRoles).join(", ")}</div>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <h1 style={{ marginTop: 0 }}>Ops — Alocação de Produtos por Slot</h1>
        <div style={warningStyle}>
          Ferramenta operacional para mapear SKU em gaveta/slot do locker. O catálogo público
          passa a refletir esta alocação. Esta tela é exclusivamente para ambiente de desenvolvimento 
          controlado com VITE_DEV_BYPASS_AUTH=true. Veja 02_docker/.env
        </div>

        <div style={gridStyle}>
          <label style={labelStyle}>
            Região
            <select value={region} onChange={(e) => setRegion(e.target.value)} style={inputStyle}>
              <option value="SP">SP</option>
              <option value="PT">PT</option>
            </select>
          </label>

          <label style={labelStyle}>
            Locker
            <select
              value={selectedLockerId}
              onChange={(e) => setSelectedLockerId(e.target.value)}
              style={inputStyle}
              disabled={loadingLockers || !lockers.length}
            >
              {!lockers.length ? (
                <option value="">Nenhum locker disponível</option>
              ) : (
                lockers.map((locker) => (
                  <option key={locker.locker_id} value={locker.locker_id}>
                    {locker.display_name}
                  </option>
                ))
              )}
            </select>
          </label>
        </div>

        <div style={toolbarStyle}>
          <button onClick={fetchLockers} style={buttonSecondaryStyle} disabled={loadingLockers}>
            {loadingLockers ? "Atualizando..." : "Atualizar lockers"}
          </button>
          <button onClick={fetchSlotsAndCatalog} style={buttonSecondaryStyle} disabled={loadingSlots}>
            {loadingSlots ? "Atualizando slots..." : "Atualizar slots"}
          </button>
          <button
            onClick={saveAllChanges}
            style={buttonPrimaryStyle}
            disabled={savingBatch || !dirtySlots.length}
          >
            {savingBatch ? "Salvando lote..." : `Salvar alterações (${dirtySlots.length})`}
          </button>
        </div>

        {message ? <div style={okStyle}>{message}</div> : null}
        {error ? <pre style={errorStyle}>{error}</pre> : null}
      </section>

      <section style={cardStyle}>
        <h2 style={{ marginTop: 0 }}>Slots</h2>
        {!selectedLockerId ? (
          <div style={summaryStyle}>Selecione um locker para editar a alocação.</div>
        ) : loadingSlots ? (
          <div style={summaryStyle}>Carregando slots...</div>
        ) : !slots.length ? (
          <div style={summaryStyle}>Nenhum slot retornado para este locker.</div>
        ) : (
          <div style={tableWrapperStyle}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>Slot</th>
                  <th style={thStyle}>SKU atual</th>
                  <th style={thStyle}>Novo SKU</th>
                  <th style={thStyle}>Ação</th>
                </tr>
              </thead>
              <tbody>
                {slots.map((slot) => {
                  const slotKey = String(slot.slot);
                  const draftSku = String(slotDraftMap[slotKey] || "");
                  const currentSku = String(slot.sku_id || "");
                  const isDirty = draftSku !== currentSku;
                  const isSavingRow = savingSlot === Number(slot.slot);

                  return (
                    <tr key={slotKey}>
                      <td style={tdStyle}>{slot.slot}</td>
                      <td style={tdStyle}>{currentSku || "-"}</td>
                      <td style={tdStyle}>
                        <select
                          value={draftSku}
                          onChange={(e) =>
                            setSlotDraftMap((prev) => ({ ...prev, [slotKey]: e.target.value }))
                          }
                          style={inputStyle}
                        >
                          <option value="">Selecione um SKU</option>
                          {skuOptions.map((sku) => (
                            <option key={sku.sku_id} value={sku.sku_id}>
                              {sku.sku_id} - {sku.name}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td style={tdStyle}>
                        <button
                          onClick={() => saveSingleSlot(Number(slot.slot))}
                          style={isDirty ? buttonPrimaryStyle : buttonSecondaryStyle}
                          disabled={!isDirty || isSavingRow}
                        >
                          {isSavingRow ? "Salvando..." : "Salvar"}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

const pageStyle = {
  width: "100%",
  maxWidth: "none",
  padding: 24,
  boxSizing: "border-box",
  color: "#f5f7fa",
  fontFamily: "system-ui, sans-serif",
  display: "grid",
  gap: 16,
};

const cardStyle = {
  background: "#11161c",
  border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: 16,
  padding: 16,
  boxSizing: "border-box",
};

const warningStyle = {
  padding: 10,
  borderRadius: 10,
  background: "rgba(199,146,0,0.14)",
  border: "1px solid rgba(199,146,0,0.30)",
  fontSize: 14,
};

const summaryStyle = {
  marginTop: 12,
  padding: 10,
  borderRadius: 10,
  background: "rgba(255,255,255,0.05)",
  border: "1px solid rgba(255,255,255,0.08)",
};

const gridStyle = {
  marginTop: 12,
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
  gap: 12,
};

const labelStyle = {
  display: "grid",
  gap: 6,
  fontSize: 14,
};

const inputStyle = {
  padding: "10px 12px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#0b0f14",
  color: "#f5f7fa",
};

const toolbarStyle = {
  marginTop: 12,
  display: "flex",
  gap: 8,
  flexWrap: "wrap",
};

const buttonSecondaryStyle = {
  padding: "10px 14px",
  cursor: "pointer",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#1b5883",
  color: "white",
  fontWeight: 600,
};

const buttonPrimaryStyle = {
  padding: "10px 14px",
  cursor: "pointer",
  borderRadius: 10,
  border: "1px solid rgba(31,122,63,0.40)",
  background: "#1f7a3f",
  color: "white",
  fontWeight: 700,
};

const okStyle = {
  marginTop: 10,
  padding: 10,
  borderRadius: 10,
  background: "rgba(31,122,63,0.15)",
  border: "1px solid rgba(31,122,63,0.35)",
};

const errorStyle = {
  marginTop: 10,
  background: "#2b1d1d",
  color: "#ffb4b4",
  padding: 12,
  borderRadius: 12,
  overflow: "auto",
  whiteSpace: "pre-wrap",
};

const tableWrapperStyle = {
  overflowX: "auto",
};

const tableStyle = {
  width: "100%",
  borderCollapse: "collapse",
};

const thStyle = {
  textAlign: "left",
  borderBottom: "1px solid rgba(255,255,255,0.18)",
  padding: "10px 8px",
  fontSize: 13,
};

const tdStyle = {
  borderBottom: "1px solid rgba(255,255,255,0.08)",
  padding: "10px 8px",
  verticalAlign: "top",
};
