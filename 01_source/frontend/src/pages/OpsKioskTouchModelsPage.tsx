import React, { useEffect, useMemo, useState, type CSSProperties } from "react";
import { Link } from "react-router-dom";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";

type ModelId = "A" | "B" | "C" | "D";

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

const MODELS: Array<{
  id: ModelId;
  title: string;
  subtitle: string;
  bullets: string[];
  primaryTo: string;
  primaryLabel: string;
}> = [
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

const PAGE_VERSION = "ops/kiosk-touch-models v1.1.0-usability-n8";

export default function OpsKioskTouchModelsPage() {
  const [active, setActive] = useState<ModelId | null>("A");
  const [usabilityChecks, setUsabilityChecks] = useState<Record<string, boolean>>(() => readUsabilityChecksFromLs());

  const activeModel = useMemo(() => MODELS.find((m) => m.id === active) ?? MODELS[0], [active]);

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
    <div style={pageWrap}>
      <OpsPageTitleHeader
        title="KIOSK touch — modelos de tela v1"
        versionLabel={PAGE_VERSION}
        containerStyle={{ marginBottom: 12 }}
      />

      <p style={intro}>
        Protótipo navegável Sprint 1: quatro modelos do plano global (Quick Buy, Guided Buy, Pickup Fast Lane, Partner
        Allocation). Use os botões para pré-visualizar o foco de cada modelo e os links para abrir fluxos existentes no
        lab.
      </p>

      <div style={grid}>
        {MODELS.map((m) => {
          const isOn = active === m.id;
          return (
            <button
              key={m.id}
              type="button"
              onClick={() => setActive(m.id)}
              style={{
                ...card,
                borderColor: isOn ? "rgba(56,189,248,0.75)" : "rgba(255,255,255,0.14)",
                background: isOn ? "rgba(14,165,233,0.12)" : "rgba(255,255,255,0.04)",
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
  padding: "16px 18px 32px",
  maxWidth: 1100,
  margin: "0 auto",
  color: "#e2e8f0",
};

const intro: CSSProperties = {
  fontSize: 14,
  lineHeight: 1.5,
  opacity: 0.88,
  marginTop: 0,
  marginBottom: 16,
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
  border: "1px solid rgba(255,255,255,0.14)",
  textAlign: "left" as const,
  cursor: "pointer",
  color: "inherit",
  font: "inherit",
};

const cardTitle: CSSProperties = {
  fontSize: 15,
  fontWeight: 800,
  marginBottom: 6,
};

const cardSub: CSSProperties = {
  fontSize: 12,
  opacity: 0.82,
  lineHeight: 1.45,
};

const detailPanel: CSSProperties = {
  padding: 16,
  borderRadius: 16,
  border: "1px solid rgba(255,255,255,0.12)",
  background: "rgba(255,255,255,0.03)",
};

const h2: CSSProperties = {
  marginTop: 0,
  fontSize: 18,
  fontWeight: 800,
};

const ul: CSSProperties = {
  margin: "0 0 16px",
  paddingLeft: 20,
  fontSize: 13,
  lineHeight: 1.55,
  opacity: 0.9,
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
  background: "rgba(255,255,255,0.08)",
  border: "1px solid rgba(255,255,255,0.2)",
  color: "#e2e8f0",
};

const footerNote: CSSProperties = {
  marginTop: 20,
  fontSize: 12,
  opacity: 0.75,
  lineHeight: 1.5,
};

const checklistPanel: CSSProperties = {
  marginTop: 22,
  padding: 16,
  borderRadius: 16,
  border: "1px solid rgba(52,211,153,0.35)",
  background: "rgba(16,185,129,0.08)",
};

const checklistIntro: CSSProperties = {
  marginTop: 0,
  marginBottom: 12,
  fontSize: 13,
  lineHeight: 1.5,
  opacity: 0.9,
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
};

const checkInput: CSSProperties = { marginTop: 3, flexShrink: 0 };

const exportBtn: CSSProperties = {
  padding: "10px 16px",
  borderRadius: 12,
  border: "1px solid rgba(52,211,153,0.45)",
  background: "rgba(6,95,70,0.55)",
  color: "#ecfdf5",
  fontWeight: 700,
  fontSize: 13,
  cursor: "pointer",
};
