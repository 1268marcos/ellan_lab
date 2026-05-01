import React, { useEffect, useMemo, useState, type CSSProperties } from "react";
import { Link } from "react-router-dom";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";

type ModelId = "A" | "B" | "C" | "D";

const MODEL_IDS: ModelId[] = ["A", "B", "C", "D"];

/** Sobrescreve textos/rotas dos modelos; merge por id com canónicos quando a chave não existir ou o JSON for inválido. */
const MODEL_DEFINITIONS_LS_KEY = "ops_kiosk_touch_models_definitions_v1";

const USABILITY_LS_KEY = "ops_kiosk_touch_models_usability_n8_v1";

const USABILITY_CHECKLIST: ReadonlyArray<{ id: string; label: string }> = [
  { id: "n1", label: "CTA principal do modelo ativo visível sem scroll nesta página." },
  { id: "n2", label: "Áreas de toque ≥44px nos CTAs principais (cards e link primário)." },
  { id: "n3", label: "Contraste legível no cartão selecionado vs. cartões inativos." },
  { id: "n4", label: "Estados explícitos: seleção de modelo + painel de detalhe coerente." },
  { id: "n5", label: "Rotas secundárias (kiosk PT/SP, locker `/ops/00`) acessíveis a partir do detalhe." },
  { id: "n6", label: "Microcopy em PT consistente nesta rota (títulos, bullets, rodapé)." },
  { id: "n7", label: "Ligações a fluxos reais do lab revistas na sessão (≥1 fluxo aberto para smoke)." },
  { id: "n8", label: "Evidência exportável: checklist + pontuação em JSON (botão abaixo)." },
];

function defaultUsabilityChecks(): Record<string, boolean> {
  return Object.fromEntries(USABILITY_CHECKLIST.map((row) => [row.id, false]));
}

function readUsabilityChecksFromLs(): Record<string, boolean> {
  const base = defaultUsabilityChecks();
  if (typeof window === "undefined") return base;
  try {
    const raw = window.localStorage.getItem(USABILITY_LS_KEY);
    if (!raw) return base;
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    const merged: Record<string, boolean> = { ...base };
    for (const row of USABILITY_CHECKLIST) {
      if (typeof parsed[row.id] === "boolean") merged[row.id] = parsed[row.id] as boolean;
    }
    return merged;
  } catch {
    return base;
  }
}

function downloadJsonFile(filename: string, payload: unknown) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

type TouchModelRow = {
  id: ModelId;
  title: string;
  subtitle: string;
  bullets: string[];
  primaryTo: string;
  primaryLabel: string;
};

const CANONICAL_TOUCH_MODELS: TouchModelRow[] = [
  {
    id: "A",
    title: "Modelo A — Quick Buy",
    subtitle: "Compra rápida e recorrente; CTA principal sempre visível.",
    bullets: [
      "Poucos passos até confirmação.",
      "Ideal para SKU memorizado ou favorito.",
      "Alvo touch mínimo 44px nos CTAs.",
    ],
    primaryTo: "/comprar",
    primaryLabel: "Abrir catálogo (fluxo compra)",
  },
  {
    id: "B",
    title: "Modelo B — Guided Buy",
    subtitle: "Fluxo assistido para carrinho mais complexo ou primeiro uso.",
    bullets: [
      "Validações progressivas.",
      "Linguagem simples e estados explícitos.",
      "Recuperação de erro antes do pagamento.",
    ],
    primaryTo: "/checkout",
    primaryLabel: "Abrir checkout (laboratório)",
  },
  {
    id: "C",
    title: "Modelo C — Pickup Fast Lane",
    subtitle: "Retirada por QR, código ou manual no totem.",
    bullets: [
      "Entrada única para identificação do pedido.",
      "Confirmação rápida e feedback imediato.",
      "Integra com painel locker / kiosk OPS.",
    ],
    primaryTo: "/ops/pt/kiosk",
    primaryLabel: "Abrir kiosk OPS (PT)",
  },
  {
    id: "D",
    title: "Modelo D — Partner Allocation",
    subtitle: "Alocação de itens de parceiros com rastreabilidade de slot/lote.",
    bullets: [
      "Clareza de slot, lote e status.",
      "Confirmação auditável.",
      "Dev: alocação por slot no lab.",
    ],
    primaryTo: "/ops/dev/slots",
    primaryLabel: "Abrir alocação por slot (dev)",
  },
];

function isModelId(v: unknown): v is ModelId {
  return v === "A" || v === "B" || v === "C" || v === "D";
}

function coerceTouchModel(row: unknown): TouchModelRow | null {
  if (typeof row !== "object" || row === null) return null;
  const r = row as Record<string, unknown>;
  if (!isModelId(r.id)) return null;
  if (typeof r.title !== "string" || !r.title.trim()) return null;
  if (typeof r.subtitle !== "string" || !r.subtitle.trim()) return null;
  if (!Array.isArray(r.bullets)) return null;
  const bullets = r.bullets
    .filter((b): b is string => typeof b === "string" && b.trim().length > 0)
    .map((b) => b.trim());
  if (bullets.length === 0) return null;
  if (typeof r.primaryTo !== "string" || !r.primaryTo.trim()) return null;
  if (typeof r.primaryLabel !== "string" || !r.primaryLabel.trim()) return null;
  return {
    id: r.id,
    title: r.title.trim(),
    subtitle: r.subtitle.trim(),
    bullets,
    primaryTo: r.primaryTo.trim(),
    primaryLabel: r.primaryLabel.trim(),
  };
}

function resolveTouchModels(): TouchModelRow[] {
  const fallback = (): TouchModelRow[] => CANONICAL_TOUCH_MODELS.map((m) => ({ ...m, bullets: [...m.bullets] }));
  if (typeof window === "undefined") return fallback();
  try {
    const raw = window.localStorage.getItem(MODEL_DEFINITIONS_LS_KEY);
    if (!raw) return fallback();
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return fallback();
    const byId = new Map<ModelId, TouchModelRow>(
      CANONICAL_TOUCH_MODELS.map((m) => [m.id, { ...m, bullets: [...m.bullets] }]),
    );
    for (const item of parsed) {
      const coerced = coerceTouchModel(item);
      if (coerced) byId.set(coerced.id, coerced);
    }
    return MODEL_IDS.map((id) => {
      const row = byId.get(id);
      return row ?? CANONICAL_TOUCH_MODELS.find((m) => m.id === id)!;
    });
  } catch {
    return fallback();
  }
}

const PAGE_VERSION = "ops/kiosk-touch-models v1.1.1-contrast-light";

export default function OpsKioskTouchModelsPage() {
  const [active, setActive] = useState<ModelId | null>("A");
  const [usabilityChecks, setUsabilityChecks] = useState<Record<string, boolean>>(() => readUsabilityChecksFromLs());
  const [models, setModels] = useState<TouchModelRow[]>(() => resolveTouchModels());

  const activeModel = useMemo(() => models.find((m) => m.id === active) ?? models[0], [active, models]);

  function reloadModelDefinitions() {
    setModels(resolveTouchModels());
  }

  const usabilityDone = useMemo(
    () => USABILITY_CHECKLIST.filter((row) => usabilityChecks[row.id]).length,
    [usabilityChecks],
  );

  useEffect(() => {
    try {
      window.localStorage.setItem(USABILITY_LS_KEY, JSON.stringify(usabilityChecks));
    } catch {
      /* ignore quota / private mode */
    }
  }, [usabilityChecks]);

  function toggleUsability(id: string) {
    setUsabilityChecks((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  function exportUsabilityJson() {
    const ts = new Date().toISOString().replace(/[:.]/g, "-");
    downloadJsonFile(`SPRINT1_KIOSK_TOUCH_USABILITY_N8_${ts}.json`, {
      page: PAGE_VERSION,
      exportedAt: new Date().toISOString(),
      activeModelId: active,
      checklist: USABILITY_CHECKLIST.map((row) => ({
        id: row.id,
        label: row.label,
        done: Boolean(usabilityChecks[row.id]),
      })),
      score: usabilityDone,
      total: USABILITY_CHECKLIST.length,
    });
  }

  return (
    <div style={pageWrap} data-testid="ops-kiosk-touch-models-page">
      <OpsPageTitleHeader
        title="KIOSK touch — modelos de tela v1"
        versionLabel={PAGE_VERSION}
        containerStyle={{ marginBottom: 12 }}
        titleStyle={{ color: "#0f172a" }}
        versionBadgeStyle={{
          border: "1px solid #38bdf8",
          background: "#e0f2fe",
          color: "#0c4a6e",
        }}
      />

      <p style={intro}>
        Protótipo navegável Sprint 1: quatro modelos do plano global (Quick Buy, Guided Buy, Pickup Fast Lane, Partner
        Allocation). Use os botões para pré-visualizar o foco de cada modelo e os links para abrir fluxos existentes no
        lab.
      </p>

      <div style={definitionsToolbar}>
        <button type="button" onClick={reloadModelDefinitions} style={reloadDefinitionsBtn}>
          Recarregar definições
        </button>
        <span style={definitionsToolbarHint}>
          Relê <code style={definitionsToolbarCode}>{MODEL_DEFINITIONS_LS_KEY}</code> a partir do{" "}
          <code style={definitionsToolbarCode}>localStorage</code> sem refrescar a página.
        </span>
      </div>

      <div style={grid}>
        {models.map((m) => {
          const isOn = active === m.id;
          return (
            <button
              key={m.id}
              type="button"
              onClick={() => setActive(m.id)}
              style={{
                ...card,
                borderColor: isOn ? "#0284c7" : "#cbd5e1",
                background: isOn ? "#e0f2fe" : "#ffffff",
                boxShadow: isOn ? "0 0 0 2px rgba(2,132,199,0.25)" : "0 1px 2px rgba(15,23,42,0.06)",
              }}
            >
              <div style={cardTitle}>{m.title}</div>
              <div style={cardSub}>{m.subtitle}</div>
            </button>
          );
        })}
      </div>

      <section style={detailPanel} aria-live="polite">
        <h2 style={h2}>{activeModel.title}</h2>
        <ul style={ul}>
          {activeModel.bullets.map((line) => (
            <li key={line} style={li}>
              {line}
            </li>
          ))}
        </ul>
        <div style={row}>
          <Link to={activeModel.primaryTo} style={ctaLink}>
            {activeModel.primaryLabel}
          </Link>
          <Link to="/ops/sp/kiosk" style={secondaryLink}>
            Kiosk OPS (SP)
          </Link>
          <Link to="/ops/00" style={secondaryLink}>
            Locker protótipo `/ops/00`
          </Link>
        </div>
      </section>

      <section style={checklistPanel} aria-labelledby="kiosk-usability-n8-heading">
        <h2 id="kiosk-usability-n8-heading" style={h2}>
          Checklist usabilidade (n≥8) — Sprint 1
        </h2>
        <p style={checklistIntro}>
          Progresso: <strong>{usabilityDone}</strong> / {USABILITY_CHECKLIST.length}. Estado guardado em{" "}
          <code>localStorage</code> ({USABILITY_LS_KEY}) para sessões de revisão; exporte JSON para anexar ao daily.
        </p>
        <ul style={checklistUl}>
          {USABILITY_CHECKLIST.map((row) => (
            <li key={row.id} style={checklistLi}>
              <label style={checkLabel}>
                <input
                  type="checkbox"
                  checked={Boolean(usabilityChecks[row.id])}
                  onChange={() => toggleUsability(row.id)}
                  style={checkInput}
                />
                <span>{row.label}</span>
              </label>
            </li>
          ))}
        </ul>
        <button type="button" onClick={exportUsabilityJson} style={exportBtn}>
          Exportar checklist (JSON)
        </button>
      </section>

      <p style={footerNote}>
        Critério Sprint 1: modelo <strong>mínimo clicável</strong> + ligação a fluxo real ou OPS. Heurística n≥8
        acima cobre evidência leve até testes moderados com utilizadores; próximo: E2E KIOSK assistido ou estilos
        checkout conforme plano.
      </p>
    </div>
  );
}

const pageWrap: CSSProperties = {
  padding: "20px 20px 36px",
  maxWidth: 1100,
  margin: "0 auto",
  color: "#0f172a",
  background: "#f8fafc",
  borderRadius: 16,
  border: "1px solid #e2e8f0",
  boxSizing: "border-box",
};

const intro: CSSProperties = {
  fontSize: 14,
  lineHeight: 1.55,
  color: "#334155",
  marginTop: 0,
  marginBottom: 16,
};

const definitionsToolbar: CSSProperties = {
  display: "flex",
  flexWrap: "wrap",
  alignItems: "center",
  gap: 12,
  marginBottom: 16,
  padding: "12px 14px",
  borderRadius: 12,
  border: "1px solid #cbd5e1",
  background: "#ffffff",
};

const reloadDefinitionsBtn: CSSProperties = {
  padding: "10px 16px",
  borderRadius: 12,
  border: "1px solid #64748b",
  background: "#f1f5f9",
  color: "#0f172a",
  fontWeight: 700,
  fontSize: 13,
  cursor: "pointer",
  minHeight: 44,
};

const definitionsToolbarHint: CSSProperties = {
  fontSize: 12,
  lineHeight: 1.45,
  color: "#475569",
  flex: "1 1 200px",
};

const definitionsToolbarCode: CSSProperties = {
  fontSize: 11,
  padding: "1px 5px",
  borderRadius: 4,
  background: "#e2e8f0",
  color: "#0f172a",
};

const grid: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
  gap: 12,
  marginBottom: 20,
};

const card: CSSProperties = {
  minHeight: 96,
  padding: "14px 16px",
  borderRadius: 14,
  border: "1px solid #cbd5e1",
  textAlign: "left" as const,
  cursor: "pointer",
  color: "#0f172a",
  font: "inherit",
  background: "#ffffff",
};

const cardTitle: CSSProperties = {
  fontSize: 15,
  fontWeight: 800,
  marginBottom: 6,
  color: "#0f172a",
};

const cardSub: CSSProperties = {
  fontSize: 12,
  lineHeight: 1.45,
  color: "#475569",
};

const detailPanel: CSSProperties = {
  padding: 16,
  borderRadius: 16,
  border: "1px solid #e2e8f0",
  background: "#ffffff",
  boxShadow: "0 1px 3px rgba(15,23,42,0.08)",
};

const h2: CSSProperties = {
  marginTop: 0,
  fontSize: 18,
  fontWeight: 800,
  color: "#0f172a",
};

const ul: CSSProperties = {
  margin: "0 0 16px",
  paddingLeft: 20,
  fontSize: 13,
  lineHeight: 1.55,
  color: "#334155",
};

const li: CSSProperties = { marginBottom: 6 };

const row: CSSProperties = {
  display: "flex",
  flexWrap: "wrap",
  gap: 10,
  alignItems: "center",
};

const ctaLink: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  minHeight: 44,
  minWidth: 44,
  padding: "10px 18px",
  borderRadius: 12,
  background: "#1d4ed8",
  color: "#f8fafc",
  fontWeight: 700,
  fontSize: 14,
  textDecoration: "none",
};

const secondaryLink: CSSProperties = {
  ...ctaLink,
  background: "#f1f5f9",
  border: "1px solid #94a3b8",
  color: "#0f172a",
};

const footerNote: CSSProperties = {
  marginTop: 20,
  fontSize: 12,
  lineHeight: 1.55,
  color: "#64748b",
};

const checklistPanel: CSSProperties = {
  marginTop: 22,
  padding: 16,
  borderRadius: 16,
  border: "1px solid #6ee7b7",
  background: "#ecfdf5",
  boxShadow: "0 1px 3px rgba(6,78,59,0.08)",
};

const checklistIntro: CSSProperties = {
  marginTop: 0,
  marginBottom: 12,
  fontSize: 13,
  lineHeight: 1.55,
  color: "#14532d",
};

const checklistUl: CSSProperties = {
  margin: "0 0 14px",
  paddingLeft: 0,
  listStyle: "none",
  display: "grid",
  gap: 10,
};

const checklistLi: CSSProperties = { margin: 0 };

const checkLabel: CSSProperties = {
  display: "flex",
  gap: 10,
  alignItems: "flex-start",
  fontSize: 13,
  lineHeight: 1.45,
  cursor: "pointer",
  color: "#14532d",
};

const checkInput: CSSProperties = { marginTop: 3, flexShrink: 0 };

const exportBtn: CSSProperties = {
  padding: "10px 16px",
  borderRadius: 12,
  border: "1px solid #047857",
  background: "#059669",
  color: "#ffffff",
  fontWeight: 700,
  fontSize: 13,
  cursor: "pointer",
};
