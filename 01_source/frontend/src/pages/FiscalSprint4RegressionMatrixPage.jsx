import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { strToU8, zipSync } from "fflate";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import {
  SPRINT4_GO_NO_GO_MITIGATION_TOPICS_LIBRARY,
  SPRINT4_GO_NO_GO_RESIDUAL_RISKS_CATALOG,
  SPRINT4_MATRIX_PAGE_VERSION,
  SPRINT4_MATRIX_STORAGE_KEY,
  SPRINT4_MATRIX_VERSION,
  SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST,
  appendSprint4PilotRun,
  buildSprint4GoNoGoRegisterSummaryPayload,
  buildSprint4LastPilotRunPayload,
  buildSprint4PilotHistoryPayload,
  buildSprint4KioskTouchUatModelsPayload,
  buildSprint4PersonaFunctionalChecklistPayload,
  buildSprint4RegressionMatrixPayload,
  computeSprint4CombinedFunctionalPct,
  computeSprint4GoNoGoReadinessDocumentationPct,
  computeSprint4KioskUatProgress,
  computeSprint4MatrixProgress,
  computeSprint4PersonaRollup,
  normalizeSprint4GoNoGoState,
  loadSprint4MatrixStateRaw,
  loadSprint4PilotRunsRaw,
  mergeSprint4KioskUatRows,
  mergeSprint4MatrixRows,
  saveSprint4PilotRuns,
} from "../utils/fiscalSprint4RegressionMatrix";

const PAGE_VERSION = SPRINT4_MATRIX_PAGE_VERSION;
const DAILY_AUDIT_PREFIX = "ELLAN_FISCAL_DAILY";

function downloadJsonFile(filename, payload) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  window.URL.revokeObjectURL(url);
}

async function computeSha256Hex(content) {
  if (!window?.crypto?.subtle) return "UNAVAILABLE";
  const bytes = new TextEncoder().encode(String(content || ""));
  const digest = await window.crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

async function buildSignedPayload(payload) {
  const payloadJson = JSON.stringify(payload, null, 2);
  return {
    integrity: {
      algorithm: "SHA-256",
      content_sha256: await computeSha256Hex(payloadJson),
    },
    payload,
  };
}

function toAuditDayStamp(isoString) {
  return String(isoString || "").slice(0, 10).replaceAll("-", "");
}

function downloadZipFile(filename, filesMap) {
  const zipped = zipSync(filesMap, { level: 6 });
  const blob = new Blob([zipped], { type: "application/zip" });
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  window.URL.revokeObjectURL(url);
}

export default function FiscalSprint4RegressionMatrixPage() {
  const [rows, setRows] = useState(() => mergeSprint4MatrixRows(loadSprint4MatrixStateRaw()?.rows || {}));
  const [kioskUatRows, setKioskUatRows] = useState(() =>
    mergeSprint4KioskUatRows(loadSprint4MatrixStateRaw()?.kiosk_uat?.models || {})
  );
  const [owner, setOwner] = useState(() => String(loadSprint4MatrixStateRaw()?.owner || ""));
  const [goNoGoDecision, setGoNoGoDecision] = useState(
    () => String(loadSprint4MatrixStateRaw()?.go_no_go?.decision || "PENDING_REVIEW")
  );
  const [goNoGoRisk, setGoNoGoRisk] = useState(
    () => String(loadSprint4MatrixStateRaw()?.go_no_go?.residual_risk || "MEDIUM")
  );
  const [goNoGoMitigation, setGoNoGoMitigation] = useState(
    () => String(loadSprint4MatrixStateRaw()?.go_no_go?.mitigation_plan || "")
  );
  const [goNoGoRiskIds, setGoNoGoRiskIds] = useState(() => {
    const o = loadSprint4MatrixStateRaw()?.go_no_go?.residual_risk_ids;
    return o && typeof o === "object" ? { ...o } : {};
  });
  const [goNoGoMitigationTopicIds, setGoNoGoMitigationTopicIds] = useState(() => {
    const o = loadSprint4MatrixStateRaw()?.go_no_go?.mitigation_topic_ids;
    return o && typeof o === "object" ? { ...o } : {};
  });
  const [statusMsg, setStatusMsg] = useState("");
  const [pilotLabel, setPilotLabel] = useState("");
  const [pilotEnv, setPilotEnv] = useState("HML");
  const [pilotOutcome, setPilotOutcome] = useState("PARTIAL");
  const [pilotNotes, setPilotNotes] = useState("");
  const [pilotRuns, setPilotRuns] = useState(() => loadSprint4PilotRunsRaw());

  useEffect(() => {
    const payload = {
      version: SPRINT4_MATRIX_VERSION,
      updated_at: new Date().toISOString(),
      owner,
      rows: Object.fromEntries(rows.map((r) => [r.id, { done: r.done, note: r.note, last_marked_at: r.last_marked_at }])),
      kiosk_uat: {
        models: Object.fromEntries(
          kioskUatRows.map((r) => [r.id, { pass: r.pass, note: r.note, marked_at: r.marked_at }])
        ),
      },
      go_no_go: {
        decision: goNoGoDecision,
        residual_risk: goNoGoRisk,
        mitigation_plan: goNoGoMitigation,
        owner: String(owner || "").trim() || "-",
        updated_at: new Date().toISOString(),
        residual_risk_ids: goNoGoRiskIds,
        mitigation_topic_ids: goNoGoMitigationTopicIds,
      },
    };
    window.localStorage.setItem(SPRINT4_MATRIX_STORAGE_KEY, JSON.stringify(payload));
  }, [rows, kioskUatRows, owner, goNoGoDecision, goNoGoRisk, goNoGoMitigation, goNoGoRiskIds, goNoGoMitigationTopicIds]);

  const progress = useMemo(() => computeSprint4MatrixProgress(rows), [rows]);
  const kioskUatProgress = useMemo(() => computeSprint4KioskUatProgress(kioskUatRows), [kioskUatRows]);
  const personaRollup = useMemo(() => computeSprint4PersonaRollup(rows), [rows]);
  const combinedFunctionalPct = useMemo(
    () => computeSprint4CombinedFunctionalPct(progress, kioskUatProgress),
    [progress, kioskUatProgress]
  );
  const goNoGoReadinessPct = useMemo(() => {
    const norm = normalizeSprint4GoNoGoState({
      decision: goNoGoDecision,
      residual_risk: goNoGoRisk,
      mitigation_plan: goNoGoMitigation,
      owner,
      updated_at: "",
      residual_risk_ids: goNoGoRiskIds,
      mitigation_topic_ids: goNoGoMitigationTopicIds,
    });
    return computeSprint4GoNoGoReadinessDocumentationPct(norm, progress, kioskUatProgress);
  }, [
    goNoGoDecision,
    goNoGoRisk,
    goNoGoMitigation,
    owner,
    goNoGoRiskIds,
    goNoGoMitigationTopicIds,
    progress,
    kioskUatProgress,
  ]);

  function setRow(id, patch) {
    setRows((prev) =>
      prev.map((row) => {
        if (row.id !== id) return row;
        const next = { ...row, ...patch };
        if (Object.prototype.hasOwnProperty.call(patch, "done")) {
          next.last_marked_at = new Date().toISOString();
        }
        return next;
      })
    );
  }

  function toggleGoNoGoRisk(id) {
    setGoNoGoRiskIds((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  function toggleGoNoGoMitigationTopic(id) {
    setGoNoGoMitigationTopicIds((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  function setKioskUatRow(id, patch) {
    setKioskUatRows((prev) =>
      prev.map((row) => {
        if (row.id !== id) return row;
        const next = { ...row, ...patch };
        if (Object.prototype.hasOwnProperty.call(patch, "pass")) {
          next.marked_at = new Date().toISOString();
        }
        return next;
      })
    );
  }

  async function exportSignedJson() {
    const nowIso = new Date().toISOString();
    const ts = nowIso.replace(/[:.]/g, "-");
    const stored = loadSprint4MatrixStateRaw();
    const syntheticState = {
      version: SPRINT4_MATRIX_VERSION,
      updated_at: nowIso,
      owner,
      rows: Object.fromEntries(
        rows.map((r) => [r.id, { done: r.done, note: r.note, last_marked_at: r.last_marked_at }])
      ),
      kiosk_uat: {
        models: Object.fromEntries(
          kioskUatRows.map((r) => [r.id, { pass: r.pass, note: r.note, marked_at: r.marked_at }])
        ),
      },
      go_no_go: {
        decision: goNoGoDecision,
        residual_risk: goNoGoRisk,
        mitigation_plan: goNoGoMitigation,
        owner: String(owner || "").trim() || "-",
        updated_at: nowIso,
        residual_risk_ids: goNoGoRiskIds,
        mitigation_topic_ids: goNoGoMitigationTopicIds,
      },
    };
    const payload = buildSprint4RegressionMatrixPayload(nowIso, stored || syntheticState);
    const signed = await buildSignedPayload(payload);
    downloadJsonFile(`${DAILY_AUDIT_PREFIX}_${toAuditDayStamp(nowIso)}_SPRINT4_REGRESSION_MATRIX_${ts}.json`, signed);
    setStatusMsg("Matriz exportada (JSON assinado por SHA-256 do conteúdo).");
    window.setTimeout(() => setStatusMsg(""), 2400);
  }

  async function exportGoNoGoSignedJson() {
    const nowIso = new Date().toISOString();
    const ts = nowIso.replace(/[:.]/g, "-");
    const syntheticState = {
      version: SPRINT4_MATRIX_VERSION,
      updated_at: nowIso,
      owner,
      rows: Object.fromEntries(
        rows.map((r) => [r.id, { done: r.done, note: r.note, last_marked_at: r.last_marked_at }])
      ),
      kiosk_uat: {
        models: Object.fromEntries(
          kioskUatRows.map((r) => [r.id, { pass: r.pass, note: r.note, marked_at: r.marked_at }])
        ),
      },
      go_no_go: {
        decision: goNoGoDecision,
        residual_risk: goNoGoRisk,
        mitigation_plan: goNoGoMitigation,
        owner: String(owner || "").trim() || "-",
        updated_at: nowIso,
        residual_risk_ids: goNoGoRiskIds,
        mitigation_topic_ids: goNoGoMitigationTopicIds,
      },
    };
    const payload = buildSprint4GoNoGoRegisterSummaryPayload(nowIso, syntheticState);
    const signed = await buildSignedPayload(payload);
    downloadJsonFile(`${DAILY_AUDIT_PREFIX}_${toAuditDayStamp(nowIso)}_SPRINT4_GO_NO_GO_REGISTER_${ts}.json`, signed);
    setStatusMsg("Go/No-Go exportado (scope SPRINT4_GO_NO_GO_REGISTER_SUMMARY, JSON assinado).");
    window.setTimeout(() => setStatusMsg(""), 2600);
  }

  async function exportAuditZip() {
    const nowIso = new Date().toISOString();
    const ts = nowIso.replace(/[:.]/g, "-");
    const day = toAuditDayStamp(nowIso);
    const syntheticState = {
      version: SPRINT4_MATRIX_VERSION,
      updated_at: nowIso,
      owner,
      rows: Object.fromEntries(
        rows.map((r) => [r.id, { done: r.done, note: r.note, last_marked_at: r.last_marked_at }])
      ),
      kiosk_uat: {
        models: Object.fromEntries(
          kioskUatRows.map((r) => [r.id, { pass: r.pass, note: r.note, marked_at: r.marked_at }])
        ),
      },
      go_no_go: {
        decision: goNoGoDecision,
        residual_risk: goNoGoRisk,
        mitigation_plan: goNoGoMitigation,
        owner: String(owner || "").trim() || "-",
        updated_at: nowIso,
        residual_risk_ids: goNoGoRiskIds,
        mitigation_topic_ids: goNoGoMitigationTopicIds,
      },
    };
    const matrixPayload = buildSprint4RegressionMatrixPayload(nowIso, syntheticState);
    const signedMatrix = await buildSignedPayload(matrixPayload);
    const signedGoNoGo = await buildSignedPayload(buildSprint4GoNoGoRegisterSummaryPayload(nowIso, syntheticState));
    const signedPersonaChecklist = await buildSignedPayload(
      buildSprint4PersonaFunctionalChecklistPayload(nowIso, syntheticState)
    );
    const signedKioskTouchUat = await buildSignedPayload(buildSprint4KioskTouchUatModelsPayload(nowIso, syntheticState));
    const runs = loadSprint4PilotRunsRaw();
    const pilotPayload = buildSprint4PilotHistoryPayload(nowIso, runs);
    const signedPilot = await buildSignedPayload(pilotPayload);
    downloadZipFile(`${DAILY_AUDIT_PREFIX}_${day}_SPRINT4_REGRESSION_PILOT_PACKAGE_${ts}.zip`, {
      [`${DAILY_AUDIT_PREFIX}_${day}_SPRINT4_REGRESSION_MATRIX_${ts}.json`]: strToU8(JSON.stringify(signedMatrix, null, 2)),
      [`${DAILY_AUDIT_PREFIX}_${day}_SPRINT4_GO_NO_GO_REGISTER_${ts}.json`]: strToU8(JSON.stringify(signedGoNoGo, null, 2)),
      [`${DAILY_AUDIT_PREFIX}_${day}_SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST_${ts}.json`]: strToU8(
        JSON.stringify(signedPersonaChecklist, null, 2)
      ),
      [`${DAILY_AUDIT_PREFIX}_${day}_SPRINT4_KIOSK_TOUCH_UAT_MODELS_A_D_${ts}.json`]: strToU8(
        JSON.stringify(signedKioskTouchUat, null, 2)
      ),
      [`${DAILY_AUDIT_PREFIX}_${day}_SPRINT4_PILOT_HISTORY_${ts}.json`]: strToU8(JSON.stringify(signedPilot, null, 2)),
    });
    setStatusMsg("Pacote ZIP: matriz + Go/No-Go + checklist + UAT KIOSK A–D + pilotos.");
    window.setTimeout(() => setStatusMsg(""), 2600);
  }

  async function copyLastPilotSignedJson() {
    const runs = loadSprint4PilotRunsRaw();
    if (!runs.length) {
      setStatusMsg("Não há rodadas piloto registradas para copiar.");
      window.setTimeout(() => setStatusMsg(""), 2600);
      return;
    }
    const last = runs[runs.length - 1];
    const nowIso = new Date().toISOString();
    const payload = buildSprint4LastPilotRunPayload(nowIso, last);
    const signed = await buildSignedPayload(payload);
    const text = JSON.stringify(signed, null, 2);
    try {
      await navigator.clipboard.writeText(text);
      setStatusMsg("JSON assinado da última rodada piloto copiado para a área de transferência.");
    } catch (err) {
      setStatusMsg(`Falha ao copiar: ${String(err?.message || err)}`);
    }
    window.setTimeout(() => setStatusMsg(""), 2800);
  }

  function registerPilotRun() {
    const nowIso = new Date().toISOString();
    const label = String(pilotLabel || "").trim() || `rodada-${nowIso.slice(0, 16)}`;
    const run = {
      id: `spr4_pilot_${Date.now()}`,
      recorded_at: nowIso,
      label,
      environment: String(pilotEnv || "HML").toUpperCase(),
      outcome: String(pilotOutcome || "PARTIAL").toUpperCase(),
      owner: String(owner || "").trim() || "-",
      notes: String(pilotNotes || "").trim(),
      matrix_progress: computeSprint4MatrixProgress(rows),
      persona_progress: computeSprint4PersonaRollup(rows),
    };
    const next = appendSprint4PilotRun(run);
    setPilotRuns(next);
    setStatusMsg(`Rodada piloto registrada (${run.id}).`);
    window.setTimeout(() => setStatusMsg(""), 2600);
  }

  function clearPilotHistory() {
    const ok = window.confirm("Remover histórico local de rodadas piloto? (localStorage)");
    if (!ok) return;
    saveSprint4PilotRuns([]);
    setPilotRuns([]);
    setStatusMsg("Histórico de pilotos limpo.");
    window.setTimeout(() => setStatusMsg(""), 2200);
  }

  function resetMatrix() {
    const ok = window.confirm("Limpar progresso local desta matriz? (localStorage)");
    if (!ok) return;
    window.localStorage.removeItem(SPRINT4_MATRIX_STORAGE_KEY);
    setOwner("");
    setRows(mergeSprint4MatrixRows({}));
    setKioskUatRows(mergeSprint4KioskUatRows({}));
    setGoNoGoDecision("PENDING_REVIEW");
    setGoNoGoRisk("MEDIUM");
    setGoNoGoMitigation("");
    setGoNoGoRiskIds({});
    setGoNoGoMitigationTopicIds({});
    setStatusMsg("Matriz reiniciada.");
    window.setTimeout(() => setStatusMsg(""), 2000);
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={shortcutRowStyle}>
          <Link to="/fiscal/slo-alerts" style={shortcutLinkStyle}>
            Voltar para fiscal/slo-alerts
          </Link>
          <Link to="/fiscal/incident-response" style={shortcutLinkStyle}>
            Abrir fiscal/incident-response
          </Link>
        </div>

        <OpsPageTitleHeader title="SPRINT 4 — Matriz mínima de regressão (por persona)" versionLabel={PAGE_VERSION} />

        <p style={mutedTextStyle}>
          Checklist operacional para avançar o Sprint 4 em paralelo (sem bloquear Sprint 3): marcar evidência mínima por persona, registrar rodadas piloto e exportar pacote auditável com prefixo <code>{DAILY_AUDIT_PREFIX}</code>. O pacote diário em <code>fiscal/management-daily</code> pode anexar automaticamente a matriz e o histórico de pilotos (com limite de tamanho; ver utilitário Sprint 4).
        </p>

        <div style={toolbarStyle}>
          <label style={labelStyle}>
            Owner (opcional)
            <input
              value={owner}
              onChange={(e) => setOwner(e.target.value)}
              placeholder="Nome do executor / turno"
              style={inputStyle}
            />
          </label>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "end" }}>
            <button type="button" style={buttonStyle} onClick={() => void exportSignedJson()}>
              Exportar JSON assinado
            </button>
            <button type="button" style={buttonStyle} onClick={() => void exportGoNoGoSignedJson()}>
              Exportar Go/No-Go (JSON)
            </button>
            <button type="button" style={buttonStyle} onClick={() => void exportAuditZip()}>
              Exportar ZIP (matriz + checklist + UAT KIOSK + pilotos)
            </button>
            <button type="button" style={buttonStyle} onClick={() => void copyLastPilotSignedJson()}>
              Copiar JSON da última rodada
            </button>
            <button type="button" style={buttonStyleSecondary} onClick={() => resetMatrix()}>
              Reiniciar matriz
            </button>
          </div>
        </div>

        <div style={kpiRowStyle}>
          <span style={chipStyle}>Progresso: {progress.done}/{progress.total}</span>
          <span style={chipStyle}>{progress.pct}%</span>
          <span style={chipStyle}>Combinado matriz+UAT: {combinedFunctionalPct}%</span>
        </div>
        {statusMsg ? <small style={mutedTextStyle}>{statusMsg}</small> : null}

        <section style={boxStyle}>
          <h3 style={boxTitleStyle}>UAT KIOSK touch (4 modelos A–D)</h3>
          <p style={mutedTextStyle}>
            Protocolo manual alinhado a <code>e2e/kiosk-touch-models.spec.ts</code>; o ZIP inclui JSON assinado{" "}
            <code>SPRINT4_KIOSK_TOUCH_UAT_MODELS_A_D</code> com passos + PASS/notas por modelo para anexar ao daily/executivo.
          </p>
          <div style={kpiRowStyle}>
            <span style={chipStyle}>
              Cobertura UAT: {kioskUatProgress.pass}/{kioskUatProgress.total} ({kioskUatProgress.pct}%)
            </span>
            <span style={chipStyle}>
              Status: {kioskUatProgress.all_pass ? "PRONTO PARA GO/NO-GO" : "PENDENTE"}
            </span>
          </div>
          <div style={{ marginTop: 10, overflowX: "auto" }}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>PASS</th>
                  <th style={thStyle}>Modelo / testes manuais</th>
                  <th style={thStyle}>Notas por modelo (evidência)</th>
                </tr>
              </thead>
              <tbody>
                {kioskUatRows.map((row) => (
                  <tr key={row.id}>
                    <td style={tdStyle}>
                      <input
                        type="checkbox"
                        checked={row.pass}
                        onChange={(e) => setKioskUatRow(row.id, { pass: e.target.checked })}
                        aria-label={`Marcar UAT ${row.id}`}
                      />
                    </td>
                    <td style={tdStyle}>
                      <strong>{row.label}</strong>
                      <div>
                        <small style={mutedTextStyle}>id: {row.id}</small>
                      </div>
                      {row.default_note_hint ? (
                        <div style={{ marginTop: 6 }}>
                          <small style={{ ...mutedTextStyle, fontWeight: 700 }}>Guia de nota:</small>
                          <div>
                            <small style={mutedTextStyle}>{row.default_note_hint}</small>
                          </div>
                        </div>
                      ) : null}
                      {Array.isArray(row.manual_steps) && row.manual_steps.length ? (
                        <ol style={{ margin: "8px 0 0", paddingLeft: 18, fontSize: 12, color: "var(--fiscal-text)" }}>
                          {row.manual_steps.map((step, idx) => (
                            <li key={`${row.id}-mstep-${idx}`} style={{ marginBottom: 4 }}>
                              {step}
                            </li>
                          ))}
                        </ol>
                      ) : null}
                      {Array.isArray(row.e2e_anchors) && row.e2e_anchors.length ? (
                        <div style={{ marginTop: 6 }}>
                          <small style={{ ...mutedTextStyle, fontWeight: 700 }}>Âncoras E2E:</small>
                          <ul style={{ margin: "4px 0 0", paddingLeft: 16 }}>
                            {row.e2e_anchors.map((a, i) => (
                              <li key={`${row.id}-e2e-${i}`}>
                                <small style={mutedTextStyle}>{a}</small>
                              </li>
                            ))}
                          </ul>
                        </div>
                      ) : null}
                    </td>
                    <td style={tdStyle}>
                      <textarea
                        value={row.note}
                        onChange={(e) => setKioskUatRow(row.id, { note: e.target.value })}
                        rows={4}
                        style={textareaStyle}
                        placeholder="ticket, vídeo, order_id, path, HAR, screenshot — exportado no ZIP com o protocolo"
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section style={boxStyle}>
          <h3 style={boxTitleStyle}>Registro Go/No-Go (mínimo)</h3>
          <div style={kpiRowStyle}>
            <span style={chipStyle}>Readiness documentação: {goNoGoReadinessPct}%</span>
            <span style={chipStyle}>Riscos catalogados marcados: {SPRINT4_GO_NO_GO_RESIDUAL_RISKS_CATALOG.filter((r) => goNoGoRiskIds[r.id]).length}/{SPRINT4_GO_NO_GO_RESIDUAL_RISKS_CATALOG.length}</span>
            <span style={chipStyle}>
              Tópicos mitigação: {SPRINT4_GO_NO_GO_MITIGATION_TOPICS_LIBRARY.filter((t) => goNoGoMitigationTopicIds[t.id]).length}/
              {SPRINT4_GO_NO_GO_MITIGATION_TOPICS_LIBRARY.length}
            </span>
          </div>
          <div style={pilotGridStyle}>
            <label style={labelStyle}>
              Decisão
              <select value={goNoGoDecision} onChange={(e) => setGoNoGoDecision(e.target.value)} style={inputStyle}>
                <option value="PENDING_REVIEW">PENDING_REVIEW</option>
                <option value="GO">GO</option>
                <option value="NO_GO">NO_GO</option>
              </select>
            </label>
            <label style={labelStyle}>
              Risco residual
              <select value={goNoGoRisk} onChange={(e) => setGoNoGoRisk(e.target.value)} style={inputStyle}>
                <option value="LOW">LOW</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="HIGH">HIGH</option>
              </select>
            </label>
          </div>
          <div style={{ marginTop: 12 }}>
            <div style={{ ...labelStyle, marginBottom: 6 }}>Riscos residuais documentados (marque os aplicáveis)</div>
            <div style={{ display: "grid", gap: 8, gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))" }}>
              {SPRINT4_GO_NO_GO_RESIDUAL_RISKS_CATALOG.map((r) => (
                <label key={r.id} style={{ display: "flex", gap: 8, alignItems: "flex-start", fontSize: 13, cursor: "pointer" }}>
                  <input type="checkbox" checked={Boolean(goNoGoRiskIds[r.id])} onChange={() => toggleGoNoGoRisk(r.id)} />
                  <span>
                    <strong style={{ color: "var(--fiscal-text)" }}>{r.id}</strong>
                    <div style={mutedTextStyle}>{r.title}</div>
                  </span>
                </label>
              ))}
            </div>
          </div>
          <div style={{ marginTop: 12 }}>
            <div style={{ ...labelStyle, marginBottom: 6 }}>Plano de mitigação — tópicos (marque e complemente no texto)</div>
            <div style={{ display: "grid", gap: 8, gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))" }}>
              {SPRINT4_GO_NO_GO_MITIGATION_TOPICS_LIBRARY.map((t) => (
                <label key={t.id} style={{ display: "flex", gap: 8, alignItems: "flex-start", fontSize: 13, cursor: "pointer" }}>
                  <input
                    type="checkbox"
                    checked={Boolean(goNoGoMitigationTopicIds[t.id])}
                    onChange={() => toggleGoNoGoMitigationTopic(t.id)}
                  />
                  <span style={{ color: "var(--fiscal-text)" }}>{t.label}</span>
                </label>
              ))}
            </div>
          </div>
          <label style={{ ...labelStyle, marginTop: 10 }}>
            Plano de mitigação (obrigatório para NO_GO)
            <textarea
              value={goNoGoMitigation}
              onChange={(e) => setGoNoGoMitigation(e.target.value)}
              rows={3}
              style={textareaStyle}
              placeholder="Ação, owner e ETA para risco residual."
            />
          </label>
          <small style={mutedTextStyle}>
            Dica operacional: mantenha GO somente quando UAT KIOSK estiver 4/4 e sem bloqueio crítico.
          </small>
        </section>

        <section style={boxStyle}>
          <h3 style={boxTitleStyle}>Resumo por persona (mínimo)</h3>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {personaRollup.map((p) => (
              <span key={p.persona} style={chipStyle}>
                {p.persona}: {p.done}/{p.total}
              </span>
            ))}
          </div>
        </section>

        <section style={boxStyle}>
          <h3 style={boxTitleStyle}>Checklist funcional por persona (referência Sprint 4)</h3>
          <p style={mutedTextStyle}>
            Texto fixo de cobertura mínima; o JSON assinado <code>SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST</code> replica este bloco com rollups atuais no ZIP e nos anexos diários quando a matriz existir em <code>localStorage</code>.
          </p>
          <ul style={{ margin: "8px 0 0", paddingLeft: 18, color: "var(--fiscal-text)", fontSize: 13 }}>
            {SPRINT4_PERSONA_FUNCTIONAL_CHECKLIST.map((block) => (
              <li key={block.persona} style={{ marginBottom: 10 }}>
                <strong>{block.persona}</strong>
                {Array.isArray(block.matrix_case_ids) && block.matrix_case_ids.length ? (
                  <div style={{ ...mutedTextStyle, marginTop: 4, fontSize: 12 }}>
                    IDs matriz: <code>{block.matrix_case_ids.join(", ")}</code>
                  </div>
                ) : null}
                <ul style={{ margin: "4px 0 0", paddingLeft: 16 }}>
                  {block.must_cover.map((line) => (
                    <li key={line}>{line}</li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        </section>

        <section style={boxStyle}>
          <h3 style={boxTitleStyle}>Rodada piloto registrada (paralelo seguro)</h3>
          <p style={mutedTextStyle}>
            Use para carimbar execução assistida: o registro grava progresso da matriz e rollup por persona no momento do clique.
          </p>
          <div style={pilotGridStyle}>
            <label style={labelStyle}>
              Título da rodada
              <input value={pilotLabel} onChange={(e) => setPilotLabel(e.target.value)} style={inputStyle} placeholder="Ex.: piloto-2026-04-30-turno-A" />
            </label>
            <label style={labelStyle}>
              Ambiente
              <select value={pilotEnv} onChange={(e) => setPilotEnv(e.target.value)} style={inputStyle}>
                <option value="DEV">DEV</option>
                <option value="HML">HML</option>
                <option value="PROD">PROD</option>
              </select>
            </label>
            <label style={labelStyle}>
              Resultado
              <select value={pilotOutcome} onChange={(e) => setPilotOutcome(e.target.value)} style={inputStyle}>
                <option value="PASS">PASS</option>
                <option value="PARTIAL">PARTIAL</option>
                <option value="FAIL">FAIL</option>
              </select>
            </label>
          </div>
          <label style={{ ...labelStyle, marginTop: 10 }}>
            Notas / evidência (livre)
            <textarea value={pilotNotes} onChange={(e) => setPilotNotes(e.target.value)} rows={3} style={textareaStyle} placeholder="IDs de teste, links, observações de falso positivo, etc." />
          </label>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 }}>
            <button type="button" style={buttonStyle} onClick={() => registerPilotRun()}>
              Registrar rodada piloto
            </button>
            <button type="button" style={buttonStyleSecondary} onClick={() => clearPilotHistory()}>
              Limpar histórico de pilotos
            </button>
          </div>
          {pilotRuns.length ? (
            <div style={{ marginTop: 12, overflowX: "auto" }}>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    <th style={thStyle}>Quando</th>
                    <th style={thStyle}>Título</th>
                    <th style={thStyle}>Ambiente</th>
                    <th style={thStyle}>Resultado</th>
                    <th style={thStyle}>Matriz</th>
                  </tr>
                </thead>
                <tbody>
                  {[...pilotRuns].reverse().slice(0, 8).map((r) => (
                    <tr key={r.id}>
                      <td style={tdStyle}>
                        <small style={mutedTextStyle}>{String(r.recorded_at || "-")}</small>
                      </td>
                      <td style={tdStyle}>{String(r.label || "-")}</td>
                      <td style={tdStyle}>{String(r.environment || "-")}</td>
                      <td style={tdStyle}>{String(r.outcome || "-")}</td>
                      <td style={tdStyle}>
                        {r.matrix_progress ? `${r.matrix_progress.done}/${r.matrix_progress.total}` : "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <small style={mutedTextStyle}>Nenhuma rodada piloto registrada ainda.</small>
          )}
        </section>

        <div style={{ marginTop: 12, overflowX: "auto" }}>
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>OK</th>
                <th style={thStyle}>Persona</th>
                <th style={thStyle}>Área</th>
                <th style={thStyle}>Caso</th>
                <th style={thStyle}>Notas / evidência</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id}>
                  <td style={tdStyle}>
                    <input
                      type="checkbox"
                      checked={row.done}
                      onChange={(e) => setRow(row.id, { done: e.target.checked })}
                      aria-label={`Marcar caso ${row.id}`}
                    />
                  </td>
                  <td style={tdStyle}>{row.persona}</td>
                  <td style={tdStyle}>{row.area}</td>
                  <td style={tdStyle}>
                    <div style={{ fontWeight: 800 }}>{row.case}</div>
                    <small style={mutedTextStyle}>id: {row.id}</small>
                  </td>
                  <td style={tdStyle}>
                    <textarea
                      value={row.note}
                      onChange={(e) => setRow(row.id, { note: e.target.value })}
                      rows={3}
                      style={textareaStyle}
                      placeholder="Link de PR, path de tela, order_id de teste, etc."
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "var(--fiscal-text)", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "var(--fiscal-card-bg)", border: "1px solid var(--fiscal-card-border)", borderRadius: 16, padding: 16 };
const shortcutRowStyle = { display: "flex", gap: 8, justifyContent: "flex-end", flexWrap: "wrap", marginBottom: 10 };
const shortcutLinkStyle = { padding: "8px 12px", borderRadius: 10, border: "1px solid var(--fiscal-link-border)", background: "var(--fiscal-link-bg)", color: "var(--fiscal-text)", textDecoration: "none", fontWeight: 700, fontSize: 13 };
const mutedTextStyle = { color: "var(--fiscal-soft-text)", marginTop: 8 };
const toolbarStyle = { display: "grid", gap: 10, gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", alignItems: "end", marginTop: 10 };
const labelStyle = { display: "grid", gap: 6, fontSize: 12, fontWeight: 700, color: "var(--fiscal-soft-text)" };
const inputStyle = { borderRadius: 8, border: "1px solid var(--fiscal-link-border)", background: "var(--fiscal-link-bg)", color: "var(--fiscal-text)", padding: "8px 10px", fontSize: 13 };
const textareaStyle = { ...inputStyle, width: "100%", resize: "vertical" };
const buttonStyle = { padding: "8px 12px", borderRadius: 10, border: "1px solid var(--fiscal-link-border)", background: "var(--fiscal-link-bg)", color: "var(--fiscal-text)", cursor: "pointer", fontWeight: 800 };
const buttonStyleSecondary = { ...buttonStyle, opacity: 0.9 };
const kpiRowStyle = { display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 };
const chipStyle = { display: "inline-flex", padding: "4px 10px", borderRadius: 999, border: "1px solid var(--fiscal-link-border)", background: "var(--fiscal-link-bg)", color: "var(--fiscal-text)", fontSize: 12, fontWeight: 800 };
const boxStyle = { marginTop: 12, border: "1px solid var(--fiscal-box-border)", borderRadius: 12, background: "var(--fiscal-box-bg)", padding: 12 };
const boxTitleStyle = { margin: "0 0 8px", fontSize: 14 };
const pilotGridStyle = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 10, marginTop: 8 };
const tableStyle = { width: "100%", borderCollapse: "collapse", minWidth: 720 };
const thStyle = { textAlign: "left", borderBottom: "1px solid var(--fiscal-box-border)", padding: "8px 8px", fontSize: 12, color: "var(--fiscal-soft-text)" };
const tdStyle = { borderTop: "1px solid rgba(148,163,184,0.18)", padding: "10px 8px", verticalAlign: "top", fontSize: 13 };
