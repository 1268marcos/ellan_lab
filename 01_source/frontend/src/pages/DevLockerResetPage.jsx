// 01_source/frontend/src/pages/DevLockerResetPage.jsx
import React, { useEffect, useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";

const ORDER_PICKUP_BASE =
  import.meta.env.VITE_ORDER_PICKUP_BASE_URL || "http://localhost:8003";

function normalizeLockerItem(locker) {
  return {
    locker_id: String(locker?.locker_id || "").trim(),
    region: String(locker?.region || "").trim().toUpperCase(),
    country_code: String(locker?.country_code || "").trim().toUpperCase(),
    province_code: String(locker?.province_code || "").trim().toUpperCase(),
    display_name: locker?.display_name || locker?.locker_id || "",
    slots: Number(locker?.slots || 24),
    active: Boolean(locker?.active),
  };
}

export default function DevLockerResetPage() {
  const { token } = useAuth();
  const [region, setRegion] = useState("SP");
  const [countryCode, setCountryCode] = useState("");
  const [provinceCode, setProvinceCode] = useState("");
  const [lockers, setLockers] = useState([]);
  const [countryOptions, setCountryOptions] = useState([]);
  const [provinceOptions, setProvinceOptions] = useState([]);
  const [selectedLockerId, setSelectedLockerId] = useState("");
  const [loadingLockers, setLoadingLockers] = useState(false);
  const [loadingReset, setLoadingReset] = useState(false);
  const [loadingRelease, setLoadingRelease] = useState(false);
  const [purgeLocalData, setPurgeLocalData] = useState(true);
  const [releaseKnownAllocationsFirst, setReleaseKnownAllocationsFirst] = useState(true);
  const [allocationIdsText, setAllocationIdsText] = useState("");
  const [result, setResult] = useState(null);
  const [releaseResult, setReleaseResult] = useState(null);
  const [err, setErr] = useState("");
  const authHeaders = useMemo(() => {
    return token ? { Authorization: `Bearer ${token}` } : {};
  }, [token]);

  const selectedLocker = useMemo(
    () => lockers.find((item) => item.locker_id === selectedLockerId) || null,
    [lockers, selectedLockerId]
  );

  async function fetchLockers() {
    setLoadingLockers(true);
    setErr("");

    try {
      const params = new URLSearchParams();
      params.set("active_only", "true");
      if (countryCode) params.set("country_code", countryCode);
      if (provinceCode) params.set("province_code", provinceCode);
      else params.set("q", region);

      const res = await fetch(`${ORDER_PICKUP_BASE}/dev-admin/base/lockers?${params.toString()}`, {
        headers: authHeaders,
      });
      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        throw new Error(data?.detail ? JSON.stringify(data.detail) : JSON.stringify(data));
      }

      const items = Array.isArray(data?.items) ? data.items.map(normalizeLockerItem) : [];
      setLockers(items);

      if (items.length > 0) {
        setSelectedLockerId(items[0].locker_id);
      } else {
        setSelectedLockerId("");
      }
    } catch (e) {
      setErr(String(e?.message || e));
      setLockers([]);
      setSelectedLockerId("");
    } finally {
      setLoadingLockers(false);
    }
  }

  async function fetchCountryProvinceOptions() {
    try {
      const [countriesRes, provincesRes] = await Promise.all([
        fetch(`${ORDER_PICKUP_BASE}/dev-admin/base/countries?active_only=true&limit=500`, {
          headers: authHeaders,
        }),
        fetch(`${ORDER_PICKUP_BASE}/dev-admin/base/provinces?active_only=true&limit=5000`, {
          headers: authHeaders,
        }),
      ]);
      const [countriesData, provincesData] = await Promise.all([
        countriesRes.json().catch(() => ({})),
        provincesRes.json().catch(() => ({})),
      ]);
      if (countriesRes.ok) {
        setCountryOptions(Array.isArray(countriesData?.items) ? countriesData.items : []);
      }
      if (provincesRes.ok) {
        setProvinceOptions(Array.isArray(provincesData?.items) ? provincesData.items : []);
      }
    } catch (_e) {
      // no-op
    }
  }

  useEffect(() => {
    fetchLockers();
  }, [region, countryCode, provinceCode, authHeaders]);

  useEffect(() => {
    fetchCountryProvinceOptions();
  }, [authHeaders]);

  function parseAllocationIds(text) {
    return String(text || "")
      .split(/\r?\n|,|;|\s+/)
      .map((item) => item.trim())
      .filter(Boolean);
  }

  async function handleResetLocker() {
    if (!selectedLockerId) {
      setErr("Selecione um locker antes de executar o reset DEV.");
      return;
    }

    const confirmed = window.confirm(
      `ATENÇÃO: isso vai forçar todas as gavetas do locker ${selectedLockerId} para AVAILABLE e apagar dados locais do order_pickup_service. Deseja continuar?`
    );
    if (!confirmed) return;

    setLoadingReset(true);
    setErr("");
    setResult(null);

    try {
      const res = await fetch(`${ORDER_PICKUP_BASE}/dev-admin/reset-locker`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: JSON.stringify({
          region,
          locker_id: selectedLockerId,
          purge_local_data: purgeLocalData,
          release_known_allocations_first: releaseKnownAllocationsFirst,
        }),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data?.detail ? JSON.stringify(data.detail) : JSON.stringify(data));
      }

      setResult(data);
    } catch (e) {
      setErr(String(e?.message || e));
    } finally {
      setLoadingReset(false);
    }
  }

  async function handleReleaseRegionalAllocations() {
    if (!selectedLockerId) {
      setErr("Selecione um locker antes de liberar allocations regionais.");
      return;
    }

    const allocationIds = parseAllocationIds(allocationIdsText);
    if (!allocationIds.length) {
      setErr("Informe ao menos um allocation_id órfão do backend regional.");
      return;
    }

    setLoadingRelease(true);
    setErr("");
    setReleaseResult(null);

    try {
      const res = await fetch(`${ORDER_PICKUP_BASE}/dev-admin/release-regional-allocations`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: JSON.stringify({
          region,
          locker_id: selectedLockerId,
          allocation_ids: allocationIds,
        }),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data?.detail ? JSON.stringify(data.detail) : JSON.stringify(data));
      }

      setReleaseResult(data);
    } catch (e) {
      setErr(String(e?.message || e));
    } finally {
      setLoadingRelease(false);
    }
  }

  return (
    <div style={pageStyle}>
      <section style={dangerCardStyle}>
        <h1 style={{ marginTop: 0 }}>DEV — Reset de locker</h1>
        <div style={warningStyle}>
          Esta tela é exclusivamente para ambiente de desenvolvimento controlado com
          <b> VITE_DEV_BYPASS_AUTH=true</b>. Veja 02_docker/.env 
        </div>

        <div style={gridStyle}>
          <label style={labelStyle}>
            Região (compat)
            <select value={region} onChange={(e) => setRegion(e.target.value)} style={inputStyle}>
              <option value="SP">SP</option>
              <option value="PT">PT</option>
            </select>
          </label>

          <label style={labelStyle}>
            Country code
            <select value={countryCode} onChange={(e) => setCountryCode(e.target.value)} style={inputStyle}>
              <option value="">Todos</option>
              {countryOptions.map((country) => (
                <option key={country.code} value={String(country.code).toUpperCase()}>
                  {country.code} - {country.name}
                </option>
              ))}
            </select>
          </label>

          <label style={labelStyle}>
            Province code
            <select value={provinceCode} onChange={(e) => setProvinceCode(e.target.value)} style={inputStyle}>
              <option value="">Todas</option>
              {provinceOptions
                .filter((province) => !countryCode || String(province.country_code || "").toUpperCase() === countryCode)
                .map((province) => (
                  <option key={province.code} value={String(province.code).toUpperCase()}>
                    {province.code} - {province.name}
                  </option>
                ))}
            </select>
          </label>

          <label style={labelStyle}>
            Locker
            <select
              value={selectedLockerId}
              onChange={(e) => setSelectedLockerId(e.target.value)}
              style={inputStyle}
              disabled={loadingLockers || lockers.length === 0}
            >
              {lockers.map((locker) => (
                <option key={locker.locker_id} value={locker.locker_id}>
                  {locker.display_name}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div style={toolbarStyle}>
          <button onClick={fetchLockers} disabled={loadingLockers} style={buttonSecondaryStyle}>
            {loadingLockers ? "Atualizando..." : "Atualizar lockers"}
          </button>
        </div>

        {selectedLocker ? (
          <div style={summaryBoxStyle}>
            <div><b>locker_id:</b> {selectedLocker.locker_id}</div>
            <div><b>region:</b> {selectedLocker.region}</div>
            <div><b>country_code:</b> {selectedLocker.country_code || "-"}</div>
            <div><b>province_code:</b> {selectedLocker.province_code || "-"}</div>
            <div><b>slots:</b> {selectedLocker.slots}</div>
          </div>
        ) : null}

        <div style={checkGridStyle}>
          <label style={checkboxLabelStyle}>
            <input
              type="checkbox"
              checked={releaseKnownAllocationsFirst}
              onChange={(e) => setReleaseKnownAllocationsFirst(e.target.checked)}
            />
            Tentar soltar allocations locais conhecidas antes
          </label>

          <label style={checkboxLabelStyle}>
            <input
              type="checkbox"
              checked={purgeLocalData}
              onChange={(e) => setPurgeLocalData(e.target.checked)}
            />
            Apagar dados locais do order_pickup_service
          </label>
        </div>

        <div style={toolbarStyle}>
          <button
            onClick={handleResetLocker}
            disabled={loadingReset || !selectedLockerId}
            style={buttonDangerStyle}
          >
            {loadingReset ? "Resetando..." : "Resetar locker inteiro"}
          </button>
        </div>
      </section>

      <section style={resultCardStyle}>
        <h2 style={{ marginTop: 0 }}>Liberação manual de allocations regionais órfãs</h2>

        <div style={warningStyle}>
          Use aqui os <b>allocation_id</b> que aparecem no <b>backend_detail</b> do erro
          <b> RESOURCE_ALLOCATION_CONFLICT</b>.
        </div>

        <label style={{ ...labelStyle, marginTop: 12 }}>
          Allocation IDs órfãos
          <textarea
            value={allocationIdsText}
            onChange={(e) => setAllocationIdsText(e.target.value)}
            placeholder={
              "Exemplo:\nal_e550701ec3ed4608a3386e51e7e8a427\nal_4ad9559bb28f46ec92194960df160794"
            }
            style={textAreaStyle}
          />
        </label>

        <div style={toolbarStyle}>
          <button
            onClick={handleReleaseRegionalAllocations}
            disabled={loadingRelease || !selectedLockerId}
            style={buttonPrimaryStyle}
          >
            {loadingRelease ? "Liberando..." : "Liberar allocations regionais"}
          </button>
        </div>

        {releaseResult ? (
          <>
            <div style={summaryBoxStyle}>
              <div><b>ok:</b> {String(releaseResult.ok)}</div>
              <div><b>released_count:</b> {releaseResult.released_count}</div>
              <div><b>failed_count:</b> {releaseResult.failed_count}</div>
            </div>

            <pre style={preStyle}>{JSON.stringify(releaseResult.results, null, 2)}</pre>
          </>
        ) : null}
      </section>

      {result ? (
        <section style={resultCardStyle}>
          <h2 style={{ marginTop: 0 }}>Resultado do reset</h2>
          <div style={summaryBoxStyle}>
            <div><b>ok:</b> {String(result.ok)}</div>
            <div><b>region:</b> {result.region}</div>
            <div><b>locker_id:</b> {result.locker_id}</div>
            <div><b>slots_total:</b> {result.slots_total}</div>
            <div><b>deleted_pickups:</b> {result.deleted_pickups}</div>
            <div><b>deleted_allocations:</b> {result.deleted_allocations}</div>
            <div><b>deleted_orders:</b> {result.deleted_orders}</div>
          </div>

          <h3>Allocations liberadas</h3>
          <pre style={preStyle}>{JSON.stringify(result.released_allocations, null, 2)}</pre>

          <h3>Reset dos slots</h3>
          <pre style={preStyle}>{JSON.stringify(result.slot_reset_results, null, 2)}</pre>

          <div style={okStyle}>{result.message}</div>
        </section>
      ) : null}

      {err ? <pre style={errorStyle}>{err}</pre> : null}
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
};

const dangerCardStyle = {
  width: "100%",
  background: "#211314",
  border: "1px solid rgba(179,38,30,0.45)",
  borderRadius: 16,
  padding: 16,
  boxSizing: "border-box",
};

const resultCardStyle = {
  width: "100%",
  marginTop: 16,
  background: "#11161c",
  border: "1px solid rgba(255,255,255,0.10)",
  borderRadius: 16,
  padding: 16,
  boxSizing: "border-box",
};

const gridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
  gap: 12,
  marginTop: 12,
};

const checkGridStyle = {
  display: "grid",
  gap: 10,
  marginTop: 14,
};

const toolbarStyle = {
  display: "flex",
  gap: 12,
  flexWrap: "wrap",
  marginTop: 16,
};

const labelStyle = {
  display: "grid",
  gap: 6,
  fontSize: 14,
};

const checkboxLabelStyle = {
  display: "flex",
  alignItems: "center",
  gap: 10,
  fontSize: 14,
};

const inputStyle = {
  padding: "10px 12px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#0b0f14",
  color: "#f5f7fa",
};

const textAreaStyle = {
  minHeight: 140,
  padding: "10px 12px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#0b0f14",
  color: "#f5f7fa",
  resize: "vertical",
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

const buttonDangerStyle = {
  padding: "10px 14px",
  cursor: "pointer",
  borderRadius: 10,
  border: "1px solid rgba(179,38,30,0.40)",
  background: "#8a2323",
  color: "white",
  fontWeight: 700,
};

const summaryBoxStyle = {
  marginTop: 14,
  display: "grid",
  gap: 6,
  padding: 12,
  borderRadius: 12,
  background: "rgba(255,255,255,0.05)",
  border: "1px solid rgba(255,255,255,0.08)",
};

const preStyle = {
  background: "#0b0f14",
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: 12,
  padding: 12,
  overflow: "auto",
};

const warningStyle = {
  padding: 10,
  borderRadius: 10,
  background: "rgba(199,146,0,0.14)",
  border: "1px solid rgba(199,146,0,0.30)",
  fontSize: 14,
};

const okStyle = {
  marginTop: 12,
  padding: 10,
  borderRadius: 10,
  background: "rgba(31,122,63,0.15)",
  border: "1px solid rgba(31,122,63,0.35)",
};

const errorStyle = {
  marginTop: 16,
  background: "#2b1d1d",
  color: "#ffb4b4",
  padding: 12,
  borderRadius: 12,
  overflow: "auto",
};