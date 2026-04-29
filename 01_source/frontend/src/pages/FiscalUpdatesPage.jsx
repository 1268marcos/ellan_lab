import React, { useState } from "react";
import { Link } from "react-router-dom";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";

const FISCAL_UPDATES_PAGE_VERSION = "fiscal/updates v1.0.0";
const TIMELINE_TEMPLATE_JSON = `{
  "date": "YYYY-MM-DD",
  "scope": "L-3 D4",
  "title": "Resumo curto da entrega",
  "description": "Descrição breve do valor operacional entregue.",
  "uiRoutesNew": [
    "/ops/nova-rota-ui"
  ],
  "apiRoutesNew": [
    "GET /alguma/rota-nova"
  ],
  "routes": [
    "GET /alguma/rota",
    "POST /alguma/rota"
  ],
  "directLink": "/ops/alguma-pagina",
  "directLinkLabel": "Abrir página operacional"
}`;

const UPDATES = [
  {
    dateTime: "2026-04-29T17:14:00-03:00",
    scope: "FG-1 Stub Global - fase 2 (catálogo conectado)",
    title: "fiscal/global integrado com stub-adapters e fixtures-matrix",
    description:
      "A página fiscal/global passou a consumir e exibir as novas APIs FG-1 no próprio catálogo técnico, consolidando visão de países, cenário canônico, adapters stub e matriz de fixtures em uma única tela operacional.",
    uiRoutesNew: ["/fiscal"],
    apiRoutesNew: [
      "GET /admin/fiscal/global/fg1/stub-adapters",
      "GET /admin/fiscal/global/fg1/fixtures-matrix",
    ],
    routes: ["Frontend: 01_source/frontend/src/pages/FiscalGlobalPage.jsx", "UI /fiscal/updates"],
    directLink: "/fiscal",
    directLinkLabel: "Abrir fiscal/global com visão FG-1 conectada",
  },
  {
    dateTime: "2026-04-29T17:08:00-03:00",
    scope: "FG-1 Stub Global - execução técnica",
    title: "APIs FG-1 para adapters, fixtures e simulação canônica (US/AU/PL/CA/FR)",
    description:
      "Início do sprint macro FG-1 no billing_fiscal_service com APIs admin para inventário de adapters stub, matriz de fixtures canônicos e simulação por país/operação/cenário com telemetria padronizada.",
    links: [
      { to: "/fiscal", label: "Abrir fiscal/global" },
      { to: "/fiscal/updates", label: "Histórico FISCAL" },
    ],
  },
  {
    dateTime: "2026-04-29T17:00:00-03:00",
    scope: "Fiscal UX - handoff operacional",
    title: "Botão Copiar contexto do filtro no fiscal/countries",
    description:
      "Adicionado botão de handoff para copiar texto completo dos filtros ativos (incluindo preset, recorte da onda e contagens), facilitando passagem de turno diária sem digitação manual.",
    uiRoutesNew: ["/fiscal/countries"],
    apiRoutesNew: [],
    routes: ["Frontend: 01_source/frontend/src/pages/FiscalCountriesPage.jsx", "UI /fiscal/updates"],
    directLink: "/fiscal/countries",
    directLinkLabel: "Abrir cockpit e copiar contexto",
  },
  {
    dateTime: "2026-04-29T16:58:00-03:00",
    scope: "Fiscal UX - continuidade de plantão",
    title: "Filtros/preset persistentes + ação Limpar filtros no fiscal/countries",
    description:
      "Evolução de operação aplicada para reduzir retrabalho durante plantão: os filtros do cockpit fiscal/countries agora persistem no navegador após refresh e um botão Limpar filtros permite voltar ao estado neutro em 1 clique.",
    uiRoutesNew: ["/fiscal/countries"],
    apiRoutesNew: [],
    routes: ["Frontend: 01_source/frontend/src/pages/FiscalCountriesPage.jsx", "UI /fiscal/updates"],
    directLink: "/fiscal/countries",
    directLinkLabel: "Abrir cockpit com persistência de filtros",
  },
  {
    dateTime: "2026-04-29T16:56:00-03:00",
    scope: "Fiscal UX - identidade visual de domínio",
    title: "Tema visual FISCAL aplicado em /fiscal/* com tokens de página",
    description:
      "Foram definidos tokens visuais específicos de página FISCAL (background, cards, badges e links), aplicado wrapper de layout para rotas /fiscal/* e aderência completa em fiscal/global, fiscal/countries e fiscal/updates.",
    uiRoutesNew: ["/fiscal", "/fiscal/countries", "/fiscal/updates"],
    apiRoutesNew: [],
    routes: [
      "Frontend: 01_source/frontend/src/index.css",
      "Frontend: 01_source/frontend/src/components/FiscalPageLayout.jsx",
      "Frontend: 01_source/frontend/src/App.jsx",
      "Frontend: páginas fiscal/global, fiscal/countries, fiscal/updates",
    ],
    directLink: "/fiscal/updates",
    directLinkLabel: "Abrir histórico FISCAL com novo tema",
  },
  {
    dateTime: "2026-04-29T16:48:00-03:00",
    scope: "Fiscal UX - cockpit FG-1",
    title: "Preset Fechamento FG-1 adicionado (Somente IN WAVE + DONE)",
    description:
      "O cockpit fiscal/countries recebeu preset de fechamento para revisão rápida de conclusão da onda FG-1, aplicando em 1 clique os filtros Somente IN WAVE e DONE.",
    uiRoutesNew: ["/fiscal/countries"],
    apiRoutesNew: [],
    routes: ["Frontend: 01_source/frontend/src/pages/FiscalCountriesPage.jsx"],
    directLink: "/fiscal/countries",
    directLinkLabel: "Abrir fiscal/countries (preset fechamento)",
  },
  {
    dateTime: "2026-04-29T16:45:00-03:00",
    scope: "Fiscal UX - governança de domínio",
    title: "Registro de updates fiscais consolidado em fiscal/updates",
    description:
      "A trilha de mudanças do domínio FISCAL foi consolidada no histórico próprio fiscal/updates, evitando registro cruzado no ops/updates.",
    uiRoutesNew: ["/fiscal/updates"],
    apiRoutesNew: [],
    routes: ["Frontend: 01_source/frontend/src/pages/FiscalUpdatesPage.jsx", "UI /fiscal/updates"],
    directLink: "/fiscal/updates",
    directLinkLabel: "Abrir atualizações FISCAL",
  },
  {
    dateTime: "2026-04-29T16:40:00-03:00",
    scope: "Fiscal UX - recuperação de rota + preset de foco",
    title: "Correção de Not Found em fiscal/countries e preset FG-1 de foco",
    description:
      "Aplicada proteção de navegação para recuperar caminhos malformados que contenham fiscal/countries (redirecionando para /fiscal/countries) e adicionado preset de foco FG-1 para ativar Somente IN WAVE + IN_PROGRESS em um clique.",
    uiRoutesNew: ["/fiscal/countries"],
    apiRoutesNew: [],
    routes: ["Frontend: 01_source/frontend/src/App.jsx", "Frontend: 01_source/frontend/src/pages/FiscalCountriesPage.jsx"],
    directLink: "/fiscal/countries",
    directLinkLabel: "Abrir fiscal/countries com foco FG-1",
  },
  {
    dateTime: "2026-04-29T16:36:00-03:00",
    scope: "Fiscal UX - foco de onda + lote operacional",
    title: "Toggle Somente IN WAVE + ações em lote por filtro no fiscal/countries",
    description:
      "Microevolução aplicada com foco de execução: filtro rápido Somente IN WAVE para reduzir ruído visual e bloco de ação em lote para marcar itens filtrados como TODO/IN_PROGRESS/DONE.",
    uiRoutesNew: ["/fiscal/countries"],
    apiRoutesNew: [],
    routes: ["Frontend: 01_source/frontend/src/pages/FiscalCountriesPage.jsx"],
    directLink: "/fiscal/countries",
    directLinkLabel: "Abrir foco IN WAVE + ações em lote",
  },
  {
    dateTime: "2026-04-29T16:35:00-03:00",
    scope: "FG-0 Foundation",
    title: "Catálogo fiscal global e matriz canônica publicados via API admin",
    description:
      "Foi iniciado o ciclo de fiscalidade global com artefato executável no backend: endpoints para catálogo multipaís e scenario matrix canônica, servindo de base para execução FG-1/FG-2.",
    uiRoutesNew: ["/fiscal", "/fiscal/updates"],
    apiRoutesNew: [
      "GET /admin/fiscal/global/catalog",
      "GET /admin/fiscal/global/scenario-matrix",
    ],
    routes: [
      "Backend: 01_source/backend/billing_fiscal_service/app/services/fiscal_global_catalog_service.py",
      "Backend: 01_source/backend/billing_fiscal_service/app/api/routes_admin_fiscal.py",
      "UI /fiscal",
    ],
    directLink: "/fiscal",
    directLinkLabel: "Abrir fiscal/global",
  },
];

export default function FiscalUpdatesPage() {
  const [copyStatus, setCopyStatus] = useState("");
  const [openEntries, setOpenEntries] = useState({});

  async function handleCopyTemplate() {
    try {
      await navigator.clipboard.writeText(TIMELINE_TEMPLATE_JSON);
      setCopyStatus("Template copiado para a área de transferência.");
      window.setTimeout(() => setCopyStatus(""), 2000);
    } catch (_) {
      setCopyStatus("Não foi possível copiar automaticamente. Copie manualmente o bloco JSON.");
    }
  }

  return (
    <div style={pageStyle}>
      <section style={cardStyle}>
        <div style={shortcutRowStyle}>
          <Link to="/fiscal" style={shortcutLinkStyle}>
            Abrir fiscal/global
          </Link>
        </div>
        <OpsPageTitleHeader title="FISCAL - Updates" versionLabel={FISCAL_UPDATES_PAGE_VERSION} />
        <p style={mutedTextStyle}>Histórico dedicado das entregas da trilha fiscal global.</p>

        <details style={templateBoxStyle}>
          <summary style={templateSummaryStyle}>Mini-template JSON (novos itens da timeline)</summary>
          <p style={{ ...mutedTextStyle, marginTop: 8 }}>
            Campos obrigatórios: <b>scope</b>, <b>description</b>, <b>directLink</b>. Convenção NEW:
            use <b>uiRoutesNew</b> e <b>apiRoutesNew</b> para destacar novidades do sprint.
          </p>
          <button type="button" style={copyButtonStyle} onClick={() => void handleCopyTemplate()}>
            Copiar template
          </button>
          {copyStatus ? <div style={copyStatusStyle}>{copyStatus}</div> : null}
          <pre style={templateJsonStyle}>{TIMELINE_TEMPLATE_JSON}</pre>
        </details>

        <div style={timelineStyle}>
          {UPDATES.map((item) => (
            <details
              key={`${item.dateTime || item.date}-${item.scope}-${item.title}`}
              style={entryStyle}
              onToggle={(event) => {
                const entryKey = `${item.dateTime || item.date}-${item.scope}-${item.title}`;
                const isOpen = Boolean(event.currentTarget?.open);
                setOpenEntries((prev) => ({ ...prev, [entryKey]: isOpen }));
              }}
            >
              <summary style={entrySummaryStyle}>
                <div style={entrySummaryContentStyle}>
                  <div style={{ display: "grid", gap: 6 }}>
                    <strong>{item.title}</strong>
                    <span style={scopeBadgeStyle}>{item.scope}</span>
                  </div>
                  <span style={entryToggleBadgeStyle}>
                    {openEntries[`${item.dateTime || item.date}-${item.scope}-${item.title}`] ? "Recolher" : "Expandir"}
                  </span>
                </div>
              </summary>
              <div style={entryBodyStyle}>
                <small style={dateStyle}>{formatFiscalUpdateDateTime(item)}</small>
                <p style={descStyle}>
                  <b>{item.scope}:</b> {item.description}
                </p>
                {(item.uiRoutesNew || []).length ? (
                  <div style={newRoutesBlockStyle}>
                    <small style={newRoutesTitleStyle}>UI route NEW</small>
                    <ul style={routesListStyle}>
                      {item.uiRoutesNew.map((route) => (
                        <li key={`ui-${route}`} style={routesListItemStyle}>
                          {route} <span style={newInlineBadgeStyle}>NEW</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {(item.apiRoutesNew || []).length ? (
                  <div style={newRoutesBlockStyle}>
                    <small style={newRoutesTitleStyle}>API route NEW</small>
                    <ul style={routesListStyle}>
                      {item.apiRoutesNew.map((route) => (
                        <li key={`api-${route}`} style={routesListItemStyle}>
                          {route} <span style={newInlineBadgeStyle}>NEW</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {(item.routes || []).length ? (
                  <ul style={routesListStyle}>
                    {item.routes.map((route) => (
                      <li key={route} style={routesListItemStyle}>
                        {route}
                      </li>
                    ))}
                  </ul>
                ) : null}
                {item.directLink ? (
                  <div style={linksWrapStyle}>
                    <Link to={item.directLink} style={linkStyle}>
                      {item.directLinkLabel || "Abrir rota relacionada"}
                    </Link>
                  </div>
                ) : null}
              </div>
            </details>
          ))}
        </div>
      </section>
    </div>
  );
}

function formatFiscalUpdateDateTime(item) {
  const raw = String(item?.dateTime || item?.date || "").trim();
  if (!raw) return "-";
  const parsed = new Date(raw);
  if (Number.isNaN(parsed.getTime())) return raw;
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(parsed);
}

const pageStyle = { width: "100%", padding: 24, boxSizing: "border-box", color: "var(--fiscal-text)", fontFamily: "system-ui, sans-serif" };
const cardStyle = { background: "var(--fiscal-card-bg)", border: "1px solid var(--fiscal-card-border)", borderRadius: 16, padding: 16 };
const shortcutRowStyle = { display: "flex", justifyContent: "flex-end", marginBottom: 10 };
const shortcutLinkStyle = {
  padding: "8px 12px",
  borderRadius: 10,
  border: "1px solid var(--fiscal-link-border)",
  background: "var(--fiscal-link-bg)",
  color: "var(--fiscal-text)",
  textDecoration: "none",
  fontWeight: 700,
  fontSize: 13,
};
const mutedTextStyle = { color: "var(--fiscal-soft-text)", marginTop: 8 };
const templateBoxStyle = {
  marginTop: 10,
  marginBottom: 12,
  border: "1px solid var(--fiscal-box-border)",
  borderRadius: 10,
  background: "var(--fiscal-box-bg)",
  padding: 10,
};
const templateSummaryStyle = { cursor: "pointer", color: "var(--fiscal-accent-2)", fontWeight: 700 };
const copyButtonStyle = {
  marginTop: 8,
  padding: "6px 10px",
  borderRadius: 999,
  border: "1px solid var(--fiscal-link-border)",
  background: "var(--fiscal-link-bg)",
  color: "var(--fiscal-text)",
  fontWeight: 700,
  cursor: "pointer",
  fontSize: 12,
};
const copyStatusStyle = { marginTop: 8, fontSize: 12, color: "var(--fiscal-accent-2)" };
const templateJsonStyle = {
  marginTop: 8,
  border: "1px solid var(--fiscal-box-border)",
  borderRadius: 10,
  padding: 10,
  overflow: "auto",
  fontSize: 12,
  background: "var(--fiscal-surface)",
  color: "var(--fiscal-text)",
};
const timelineStyle = { marginTop: 12, display: "grid", gap: 10 };
const entryStyle = {
  border: "1px solid var(--fiscal-box-border)",
  borderRadius: 12,
  padding: "8px 12px",
  background: "var(--fiscal-box-bg)",
};
const entrySummaryStyle = { cursor: "pointer", display: "flex", alignItems: "center", listStyle: "none", outline: "none", padding: "2px 0" };
const entrySummaryContentStyle = { display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8, flexWrap: "wrap", width: "100%" };
const scopeBadgeStyle = {
  width: "fit-content",
  display: "inline-flex",
  alignItems: "center",
  padding: "2px 8px",
  borderRadius: 999,
  border: "1px solid var(--fiscal-link-border)",
  background: "var(--fiscal-link-bg)",
  color: "var(--fiscal-soft-text)",
  fontSize: 11,
  fontWeight: 700,
};
const entryToggleBadgeStyle = {
  border: "1px solid var(--fiscal-link-border)",
  background: "var(--fiscal-link-bg)",
  color: "var(--fiscal-text)",
  borderRadius: 999,
  padding: "4px 8px",
  fontSize: 11,
  fontWeight: 700,
};
const entryBodyStyle = { marginTop: 8 };
const dateStyle = { color: "var(--fiscal-accent-2)", fontWeight: 700 };
const descStyle = { margin: "8px 0 0", color: "var(--fiscal-soft-text)" };
const linksWrapStyle = { marginTop: 10, display: "flex", gap: 8, flexWrap: "wrap" };
const newRoutesBlockStyle = { marginTop: 8 };
const newRoutesTitleStyle = { color: "var(--fiscal-accent-2)", fontWeight: 700, fontSize: 11 };
const newInlineBadgeStyle = {
  display: "inline-flex",
  marginLeft: 6,
  padding: "1px 6px",
  borderRadius: 999,
  fontSize: 10,
  fontWeight: 700,
  color: "#ecfeff",
  border: "1px solid rgba(45, 212, 191, 0.55)",
  background: "rgba(45, 212, 191, 0.16)",
};
const routesListStyle = { margin: "8px 0 0", paddingLeft: 16, display: "grid", gap: 4 };
const routesListItemStyle = { color: "var(--fiscal-soft-text)", fontSize: 12 };
const linkStyle = {
  padding: "6px 10px",
  borderRadius: 8,
  border: "1px solid var(--fiscal-link-border)",
  background: "var(--fiscal-link-bg)",
  color: "var(--fiscal-text)",
  textDecoration: "none",
  fontSize: 12,
  fontWeight: 600,
};
