
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
import RopaFlowGraph from "../components/privacy/RopaFlowGraph";
import {
  apiKeyBannerStyle,
  buttonGhostStyle,
  buttonPrimaryStyle,
  cardStyle,
  criticalBannerStyle,
  crossShortcutLinkStyle,
  healthLocalFilterFieldStyle,
  healthLocalFilterInputStyle,
  healthLocalFilterRowStyle,
  mutedTextStyle,
  okBannerStyle,
  opsSanityCardStyle,
  pageStyle,
  summary24hHeaderStyle,
  summary24hHintStyle,
  tabButtonStyle,
  tableStyle,
  tdStyle,
  thStyle,
  toolbarStyle,
} from "../styles/opsShellStyles";

const BASE = import.meta.env.VITE_PRIVACY_COMPLIANCE_ADMIN_BASE_URL || "/api/pca";
const API = `${BASE}/v1/privacy-compliance-admin`;
const PAGE_VERSION = "ops/privacy-compliance/admin v0.6";

const TAB_ITEMS = [
  { id: "overview", label: "Visao geral" },
  { id: "compliance", label: "Score compliance" },
  { id: "regulation_hub", label: "Hub GDPR/LGPD/CCPA" },
  { id: "regulatory_toolkit", label: "Toolkit regulatório" },
  { id: "regulations", label: "Marcos Regulatórios" },
  { id: "policies", label: "Politicas" },
  { id: "ropa", label: "ROPA" },
  { id: "legal_bases", label: "Bases legais" },
  { id: "data_categories", label: "Categorias dados" },
  { id: "processors", label: "Processadores/DPA" },
  { id: "retention", label: "Retencao" },
  { id: "consents", label: "Consentimentos" },
  { id: "deletions", label: "Eliminacao" },
  { id: "subject_requests", label: "DSAR" },
  { id: "breaches", label: "Incidentes" },
  { id: "dpia", label: "DPIA/LIA" },
  { id: "transfers", label: "Transferencias" },
  { id: "ecosystem", label: "Ecossistema locker" },
  { id: "audit", label: "Auditoria" },
  { id: "integrations", label: "Integracao" },
];

const REGULATION_CODES = [
  "GDPR",
  "UKGDPR",
  "LGPD",
  "CCPA",
  "VCDPA",
  "PIPEDA",
  "FADP",
  "APPI",
  "PIPA_KR",
  "PDPA_SG",
  "AU_PA",
  "POPIA",
  "PDPL_SA",
  "EPRIVACY",
  "DPDP_IN",
];
const CONSENT_TYPES = ["MARKETING", "ANALYTICS", "TELEMETRY", "SALE_SHARE_OPT_OUT", "FISCAL_DATA"];
const DSAR_TYPES = ["ACCESS", "PORTABILITY", "RECTIFICATION", "RESTRICTION", "OBJECTION"];

function parseError(payload, fallback = "resposta invalida da API") {
  if (!payload) return fallback;
  const detail = payload.detail;
  if (typeof detail === "string" && detail.trim()) return detail.trim();
  if (Array.isArray(detail) && detail.length) {
    return detail
      .map((item) => (typeof item === "string" ? item : item?.msg || JSON.stringify(item)))
      .join("; ");
  }
  if (detail && typeof detail === "object" && typeof detail.message === "string") return detail.message;
  return fallback;
}

function httpError(label, response, payload) {
  return `${label} (HTTP ${response.status}): ${parseError(payload)}`;
}

function normalizeNetworkError(err, endpoint) {
  const raw = String(err?.message || err || "").trim();
  if (!raw) return "Falha de comunicacao com a API.";
  const lower = raw.toLowerCase();
  if (lower.includes("failed to fetch") || lower.includes("networkerror")) {
    return `Falha de conexao (${endpoint}). Verifique se o servico privacy-compliance-admin esta ativo na porta 8022 e o proxy ${BASE}.`;
  }
  return raw;
}

function isComplianceScore(payload) {
  return payload && typeof payload.score_pct === "number" && typeof payload.grade === "string";
}

async function fetchJsonSafe(url, options = {}) {
  const r = await fetch(url, options);
  const data = await r.json().catch(() => ({}));
  return { ok: r.ok, status: r.status, data };
}

function statusLabel(active) {
  return active ? "ativo" : "inativo";
}

export default function OpsPrivacyComplianceAdminPage() {
  const { token, hasRole } = useAuth();
  const canMutate = hasRole("admin_operacao");
  const [searchParams, setSearchParams] = useSearchParams();
  const initialTab = searchParams.get("tab") || "overview";
  const [tab, setTab] = useState(TAB_ITEMS.some((t) => t.id === initialTab) ? initialTab : "overview");
  const [dashboard, setDashboard] = useState(null);
  const [regulations, setRegulations] = useState([]);
  const [policies, setPolicies] = useState([]);
  const [consents, setConsents] = useState([]);
  const [deletions, setDeletions] = useState([]);
  const [subjectRequests, setSubjectRequests] = useState([]);
  const [webhooks, setWebhooks] = useState([]);
  const [regulationHub, setRegulationHub] = useState(null);
  const [hubHint, setHubHint] = useState("");
  const [legalBases, setLegalBases] = useState([]);
  const [dataCategories, setDataCategories] = useState([]);
  const [processingActivities, setProcessingActivities] = useState([]);
  const [processors, setProcessors] = useState([]);
  const [processorAgreements, setProcessorAgreements] = useState([]);
  const [retentionRules, setRetentionRules] = useState([]);
  const [breachIncidents, setBreachIncidents] = useState([]);
  const [impactAssessments, setImpactAssessments] = useState([]);
  const [transferRecords, setTransferRecords] = useState([]);
  const [ecosystemPlayers, setEcosystemPlayers] = useState([]);
  const [ecosystemRelations, setEcosystemRelations] = useState([]);
  const [ecosystemMeta, setEcosystemMeta] = useState(null);
  const [complianceScore, setComplianceScore] = useState(null);
  const [complianceScoreHint, setComplianceScoreHint] = useState("");
  const [complianceCompare, setComplianceCompare] = useState(null);
  const [auditEvents, setAuditEvents] = useState([]);
  const [consentAnalytics, setConsentAnalytics] = useState(null);
  const [ecosystemHealth, setEcosystemHealth] = useState(null);
  const [ropaGraph, setRopaGraph] = useState(null);
  const [ropaGraphLoading, setRopaGraphLoading] = useState(false);
  const [ropaGraphErr, setRopaGraphErr] = useState("");
  const [transferWizard, setTransferWizard] = useState(null);
  const [webhookDeliveries, setWebhookDeliveries] = useState([]);
  const [globalOpsBridge, setGlobalOpsBridge] = useState(null);
  const [playerCertifications, setPlayerCertifications] = useState([]);
  const [regulatoryToolkit, setRegulatoryToolkit] = useState(null);
  const [regulatoryToolkitErr, setRegulatoryToolkitErr] = useState("");
  const [rightsCompare, setRightsCompare] = useState(null);
  const [playerLegalDocuments, setPlayerLegalDocuments] = useState([]);
  const [dsarSelectedRight, setDsarSelectedRight] = useState("");
  const [dsarDraftHint, setDsarDraftHint] = useState("");
  const [filterRegulation, setFilterRegulation] = useState("");
  const [selectedRegulationCode, setSelectedRegulationCode] = useState("GDPR");
  const [webhookUrl, setWebhookUrl] = useState("");
  const [webhookSecret, setWebhookSecret] = useState("");
  const [lastApiKey, setLastApiKey] = useState("");
  const [consentForm, setConsentForm] = useState({
    regulation_code: "GDPR",
    consent_type: "MARKETING",
    granted: true,
    user_id: "",
    channel: "KIOSK",
    policy_version: "3.0",
  });
  const [deletionForm, setDeletionForm] = useState({
    regulation_code: "GDPR",
    user_id: "",
    reason: "",
  });
  const [dsarForm, setDsarForm] = useState({
    regulation_code: "LGPD",
    request_type: "ACCESS",
    user_id: "",
    details: "",
  });
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");

  const headers = useMemo(
    () => ({
      Accept: "application/json",
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    }),
    [token],
  );

  const selectedRegulation = regulations.find((r) => r.code === selectedRegulationCode);

  const setTabAndUrl = (next) => {
    setTab(next);
    setSearchParams(next === "overview" ? {} : { tab: next }, { replace: true });
  };

  useEffect(() => {
    const q = searchParams.get("tab");
    if (q && TAB_ITEMS.some((t) => t.id === q) && q !== tab) setTab(q);
  }, [searchParams, tab]);

  const loadRegulationHub = useCallback(
    async (code) => {
      const hubCode = (code || "").trim();
      if (!token || !hubCode) {
        setRegulationHub(null);
        setHubHint("");
        return;
      }
      try {
        const hubR = await fetch(`${API}/regulations/${encodeURIComponent(hubCode)}/hub`, { headers });
        const hub = await hubR.json().catch(() => ({}));
        if (!hubR.ok) {
          setRegulationHub(null);
          if (hubR.status === 404 && hub?.detail === "regulation_not_found") {
            setHubHint(
              `Marco ${hubCode} ainda nao cadastrado. Clique Seed (admin_operacao) para carregar GDPR, LGPD, CCPA e demais marcos.`,
            );
          } else {
            setHubHint(httpError(`Hub ${hubCode}`, hubR, hub));
          }
          return;
        }
        setHubHint("");
        setRegulationHub(hub);
      } catch (e) {
        setRegulationHub(null);
        setHubHint(normalizeNetworkError(e, `${API}/regulations/${hubCode}/hub`));
      }
    },
    [token, headers],
  );

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setErr("");
    setOk("");
    try {
      const regQ = filterRegulation ? `?regulation_code=${encodeURIComponent(filterRegulation)}` : "";
      const [
        dashR, regR, polR, conR, delR, subR, whR,
        lbR, dcR, ropaR, procR, dpaR, retR, brR, dpiaR, xferR, ecoPR, ecoRelR, ecoMetaR, auditR, healthR,
      ] = await Promise.all([
        fetch(`${API}/dashboard`, { headers }),
        fetch(`${API}/regulations`, { headers }),
        fetch(`${API}/policy-versions`, { headers }),
        fetch(`${API}/consents${regQ}`, { headers }),
        fetch(`${API}/deletion-requests${regQ}`, { headers }),
        fetch(`${API}/subject-requests${regQ}`, { headers }),
        fetch(`${API}/webhooks`, { headers }),
        fetch(`${API}/legal-bases${regQ}`, { headers }),
        fetch(`${API}/data-categories${regQ}`, { headers }),
        fetch(`${API}/processing-activities${regQ}`, { headers }),
        fetch(`${API}/processors${regQ}`, { headers }),
        fetch(`${API}/processor-agreements${regQ}`, { headers }),
        fetch(`${API}/retention-rules${regQ}`, { headers }),
        fetch(`${API}/breach-incidents${regQ}`, { headers }),
        fetch(`${API}/impact-assessments${regQ}`, { headers }),
        fetch(`${API}/transfer-records${regQ}`, { headers }),
        fetch(`${API}/ecosystem/players${regQ}`, { headers }),
        fetch(`${API}/ecosystem/relations`, { headers }),
        fetch(`${API}/ecosystem/meta`, { headers }),
        fetch(`${API}/audit-events?limit=50`, { headers }),
        fetch(`${API}/ecosystem/health`, { headers }),
      ]);
      const dash = await dashR.json().catch(() => ({}));
      const reg = await regR.json().catch(() => ({}));
      const pol = await polR.json().catch(() => ({}));
      const con = await conR.json().catch(() => ({}));
      const del = await delR.json().catch(() => ({}));
      const sub = await subR.json().catch(() => ({}));
      const wh = await whR.json().catch(() => ({}));
      const lb = await lbR.json().catch(() => ({}));
      const dc = await dcR.json().catch(() => ({}));
      const ropa = await ropaR.json().catch(() => ({}));
      const proc = await procR.json().catch(() => ({}));
      const dpa = await dpaR.json().catch(() => ({}));
      const ret = await retR.json().catch(() => ({}));
      const br = await brR.json().catch(() => ({}));
      const dpia = await dpiaR.json().catch(() => ({}));
      const xfer = await xferR.json().catch(() => ({}));
      const ecoP = await ecoPR.json().catch(() => ({}));
      const ecoRel = await ecoRelR.json().catch(() => ({}));
      const ecoM = await ecoMetaR.json().catch(() => ({}));
      const audit = await auditR.json().catch(() => ({}));
      const health = await healthR.json().catch(() => ({}));
      if (!dashR.ok) throw new Error(httpError("Dashboard", dashR, dash));
      if (!regR.ok) throw new Error(httpError("Marcos regulatorios", regR, reg));
      setDashboard(dash);
      const regList = reg.items || [];
      setRegulations(regList);
      setPolicies(pol.items || []);
      setConsents(con.items || []);
      setDeletions(del.items || []);
      setSubjectRequests(sub.items || []);
      setWebhooks(wh.items || []);
      setLegalBases(lb.items || []);
      setDataCategories(dc.items || []);
      setProcessingActivities(ropa.items || []);
      setProcessors(proc.items || []);
      setProcessorAgreements(dpa.items || []);
      setRetentionRules(ret.items || []);
      setBreachIncidents(br.items || []);
      setImpactAssessments(dpia.items || []);
      setTransferRecords(xfer.items || []);
      setEcosystemPlayers(ecoP.items || []);
      setEcosystemRelations(ecoRel.items || []);
      setEcosystemMeta(ecoMetaR.ok ? ecoM : null);
      setAuditEvents(audit.items || []);
      setEcosystemHealth(healthR.ok ? health : null);
      setSelectedRegulationCode((prev) => prev || regList[0]?.code || "GDPR");
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
      setDashboard(null);
      setRegulations([]);
      setPolicies([]);
      setConsents([]);
      setDeletions([]);
      setSubjectRequests([]);
      setWebhooks([]);
      setRegulationHub(null);
      setHubHint("");
      setLegalBases([]);
      setDataCategories([]);
      setProcessingActivities([]);
      setProcessors([]);
      setProcessorAgreements([]);
      setRetentionRules([]);
      setBreachIncidents([]);
      setImpactAssessments([]);
      setTransferRecords([]);
      setEcosystemPlayers([]);
      setEcosystemRelations([]);
      setEcosystemMeta(null);
      setAuditEvents([]);
      setEcosystemHealth(null);
      setComplianceScore(null);
      setComplianceCompare(null);
      setConsentAnalytics(null);
    } finally {
      setLoading(false);
    }
  }, [token, headers, filterRegulation]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (tab !== "regulation_hub" || !token) return;
    void loadRegulationHub(selectedRegulationCode || "GDPR");
  }, [tab, token, selectedRegulationCode, loadRegulationHub]);

  useEffect(() => {
    if (!token) return;
    const code = selectedRegulationCode || "GDPR";
    if (tab === "compliance" || tab === "overview") {
      void (async () => {
        const { ok, status, data } = await fetchJsonSafe(
          `${API}/compliance/score?regulation_code=${encodeURIComponent(code)}&persist=false`,
          { headers },
        );
        if (ok && isComplianceScore(data)) {
          setComplianceScore(data);
          setComplianceScoreHint("");
        } else {
          setComplianceScore(null);
          setComplianceScoreHint(
            ok
              ? "Resposta de score invalida."
              : `Score compliance indisponivel (HTTP ${status}). Reinicie o servico na porta 8022 com a versao v0.6+ (rotas /compliance/score).`,
          );
        }
      })();
    }
    if (tab === "compliance") {
      void fetchJsonSafe(`${API}/compliance/compare?codes=GDPR,LGPD,CCPA`, { headers }).then(({ ok, data }) => {
        setComplianceCompare(ok && Array.isArray(data?.scores) ? data : null);
      });
    }
    if (tab === "consents") {
      const regQ = filterRegulation ? `&regulation_code=${encodeURIComponent(filterRegulation)}` : "";
      void fetch(`${API}/analytics/consents?days=30${regQ}`, { headers })
        .then((r) => r.json())
        .then((j) => setConsentAnalytics(j))
        .catch(() => setConsentAnalytics(null));
    }
    if (tab === "ropa") {
      const code = selectedRegulationCode || filterRegulation || "GDPR";
      setRopaGraphLoading(true);
      setRopaGraphErr("");
      void fetch(`${API}/ropa/graph?regulation_code=${encodeURIComponent(code)}`, { headers })
        .then(async (r) => {
          const j = await r.json().catch(() => ({}));
          if (!r.ok) throw new Error(parseError(j));
          setRopaGraph(j);
        })
        .catch((e) => {
          setRopaGraph(null);
          setRopaGraphErr(normalizeNetworkError(e, `${API}/ropa/graph`));
        })
        .finally(() => setRopaGraphLoading(false));
    }
    if (tab === "integrations") {
      void fetch(`${API}/webhook-deliveries?limit=50`, { headers })
        .then((r) => r.json())
        .then((j) => setWebhookDeliveries(j.items || []))
        .catch(() => setWebhookDeliveries([]));
    }
    if (tab === "ecosystem") {
      void fetch(`${API}/ecosystem/global-ops-bridge`, { headers })
        .then((r) => r.json())
        .then((j) => setGlobalOpsBridge(j))
        .catch(() => setGlobalOpsBridge(null));
      void fetch(`${API}/ecosystem/certifications?limit=30`, { headers })
        .then((r) => r.json())
        .then((j) => setPlayerCertifications(j.items || []))
        .catch(() => setPlayerCertifications([]));
      void fetch(`${API}/ecosystem/player-legal-documents?limit=50`, { headers })
        .then((r) => r.json())
        .then((j) => setPlayerLegalDocuments(j.items || []))
        .catch(() => setPlayerLegalDocuments([]));
    }
    if (tab === "subject_requests" || tab === "regulatory_toolkit") {
      const code = tab === "subject_requests" ? (dsarForm.regulation_code || selectedRegulationCode || "GDPR") : (selectedRegulationCode || "GDPR");
      if (tab === "subject_requests" || !regulatoryToolkit) {
        void fetch(`${API}/regulatory/toolkit?regulation_code=${encodeURIComponent(code)}`, { headers })
          .then(async (r) => {
            const j = await r.json().catch(() => ({}));
            if (r.ok) setRegulatoryToolkit(j);
          })
          .catch(() => {});
      }
    }
    if (tab === "regulatory_toolkit") {
      const code = selectedRegulationCode || "GDPR";
      setRegulatoryToolkitErr("");
      void fetch(`${API}/regulatory/toolkit?regulation_code=${encodeURIComponent(code)}`, { headers })
        .then(async (r) => {
          const j = await r.json().catch(() => ({}));
          if (!r.ok) throw new Error(parseError(j));
          setRegulatoryToolkit(j);
        })
        .catch((e) => {
          setRegulatoryToolkit(null);
          setRegulatoryToolkitErr(normalizeNetworkError(e, `${API}/regulatory/toolkit`));
        });
      void fetch(`${API}/regulatory/compare-rights?codes=GDPR,LGPD,CCPA`, { headers })
        .then((r) => r.json())
        .then((j) => setRightsCompare(j))
        .catch(() => setRightsCompare(null));
    }
  }, [tab, token, headers, selectedRegulationCode, filterRegulation]);

  const onSeed = async () => {
    if (!token || !canMutate) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/seed`, { method: "POST", headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk("Seed aplicado (marcos, ROPA, ecossistema, toolkit regulatório, score compliance, auditoria, DPA, retencao, incidentes, DPIA e transferencias).");
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/seed`));
    } finally {
      setLoading(false);
    }
  };

  const onCreateConsent = async () => {
    if (!token || !canMutate || !consentForm.regulation_code || !consentForm.consent_type) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/consents`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          ...consentForm,
          user_id: consentForm.user_id || undefined,
        }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Consentimento ${j.id} registrado (${j.regulation_code} · ${j.consent_type}).`);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/consents`));
    } finally {
      setLoading(false);
    }
  };

  const onStartTransferWizard = async () => {
    if (!token || !canMutate) return;
    setLoading(true);
    setErr("");
    try {
      const code = selectedRegulationCode || filterRegulation || "GDPR";
      const r = await fetch(`${API}/transfer-wizard/sessions`, {
        method: "POST",
        headers,
        body: JSON.stringify({ regulation_code: code }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setTransferWizard(j);
      setOk(`Wizard transferencia iniciado (${j.id.slice(0, 8)}… · passo ${j.current_step}).`);
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/transfer-wizard/sessions`));
    } finally {
      setLoading(false);
    }
  };

  const onAdvanceTransferWizard = async (payload) => {
    if (!token || !canMutate || !transferWizard?.id) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/transfer-wizard/sessions/${transferWizard.id}/step`, {
        method: "PATCH",
        headers,
        body: JSON.stringify(payload),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setTransferWizard(j);
      setOk(`Wizard passo ${payload.step} concluido → ${j.current_step}.`);
      if (j.current_step === "REVIEW") setOk("Wizard pronto para revisao. Clique Finalizar SCC/BCR.");
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/transfer-wizard/sessions/.../step`));
    } finally {
      setLoading(false);
    }
  };

  const onCompleteTransferWizard = async () => {
    if (!token || !canMutate || !transferWizard?.id) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/transfer-wizard/sessions/${transferWizard.id}/complete`, { method: "POST", headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Transferencia registrada ${j.id.slice(0, 8)} (${j.mechanism} → ${j.destination_country}).`);
      setTransferWizard(null);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/transfer-wizard/sessions/.../complete`));
    } finally {
      setLoading(false);
    }
  };

  const onDispatchTestWebhook = async () => {
    if (!token || !canMutate) return;
    const code = selectedRegulationCode || "GDPR";
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/webhooks/dispatch`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          regulation_code: code,
          event_name: "consent.granted",
          payload: { demo: true, ts: new Date().toISOString() },
          aggregate_id: `demo-${Date.now()}`,
        }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Webhook enfileirado ${j.id.slice(0, 8)} · status ${j.status}.`);
      const dl = await fetch(`${API}/webhook-deliveries?limit=50`, { headers }).then((x) => x.json());
      setWebhookDeliveries(dl.items || []);
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/webhooks/dispatch`));
    } finally {
      setLoading(false);
    }
  };

  const onSyncGlobalOpsCerts = async () => {
    if (!token || !canMutate) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/ecosystem/certifications/sync`, { method: "POST", headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Certificacoes sincronizadas (${j.synced} via ${j.source}).`);
      const [bridge, certs] = await Promise.all([
        fetch(`${API}/ecosystem/global-ops-bridge`, { headers }).then((x) => x.json()),
        fetch(`${API}/ecosystem/certifications?limit=30`, { headers }).then((x) => x.json()),
      ]);
      setGlobalOpsBridge(bridge);
      setPlayerCertifications(certs.items || []);
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/ecosystem/certifications/sync`));
    } finally {
      setLoading(false);
    }
  };

  const onCreateDeletion = async () => {
    if (!token || !canMutate || !deletionForm.regulation_code || !deletionForm.user_id) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/deletion-requests`, {
        method: "POST",
        headers,
        body: JSON.stringify(deletionForm),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Pedido eliminacao ${j.id} criado (${j.regulation_code}).`);
      setDeletionForm((f) => ({ ...f, user_id: "", reason: "" }));
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/deletion-requests`));
    } finally {
      setLoading(false);
    }
  };

  const onCreateDsar = async () => {
    if (!token || !canMutate || !dsarForm.regulation_code || !dsarForm.user_id) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/subject-requests`, {
        method: "POST",
        headers,
        body: JSON.stringify(dsarForm),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`DSAR ${j.id} aberto — prazo ${j.due_at?.slice(0, 10) || "—"}.`);
      setDsarForm((f) => ({ ...f, user_id: "", details: "" }));
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/subject-requests`));
    } finally {
      setLoading(false);
    }
  };

  const onCompleteDeletion = async (id) => {
    if (!token || !canMutate || !id) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/deletion-requests/${encodeURIComponent(id)}`, {
        method: "PATCH",
        headers,
        body: JSON.stringify({ status: "COMPLETED" }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Eliminacao ${id} concluida.`);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/deletion-requests/${id}`));
    } finally {
      setLoading(false);
    }
  };

  const onWebhook = async () => {
    if (!token || !canMutate || !selectedRegulationCode || !webhookUrl) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/webhooks`, {
        method: "PUT",
        headers,
        body: JSON.stringify({
          regulation_code: selectedRegulationCode,
          url: webhookUrl.trim(),
          secret: webhookSecret || undefined,
          events: ["consent.granted", "consent.revoked", "deletion.completed", "dsar.completed"],
        }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Webhook salvo para ${selectedRegulationCode}.`);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/webhooks`));
    } finally {
      setLoading(false);
    }
  };

  const onRotateKey = async () => {
    if (!token || !canMutate || !selectedRegulationCode) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/regulations/${encodeURIComponent(selectedRegulationCode)}/api-keys/rotate`, {
        method: "POST",
        headers,
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setLastApiKey(j.api_key || "");
      setOk(`Nova API key (${j.key_prefix}…). Copie agora.`);
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/regulations/.../api-keys/rotate`));
    } finally {
      setLoading(false);
    }
  };

  const onApplyDsarDraft = async (regulationCode, rightCode, switchTab = false) => {
    if (!token || !regulationCode || !rightCode) return;
    setErr("");
    try {
      const r = await fetch(
        `${API}/regulatory/dsar-draft?regulation_code=${encodeURIComponent(regulationCode)}&right_code=${encodeURIComponent(rightCode)}`,
        { headers },
      );
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setDsarForm((f) => ({
        ...f,
        regulation_code: j.regulation_code,
        request_type: j.request_type,
        details: j.details,
      }));
      setDsarSelectedRight(rightCode);
      setDsarDraftHint(`${j.right_name} (${j.article_ref || j.right_code}) · SLA ${j.response_sla_days}d`);
      setOk(`DSAR pré-preenchido: ${j.subject_line}`);
      if (switchTab) setTabAndUrl("subject_requests");
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/regulatory/dsar-draft`));
    }
  };

  const onPatchObligation = async (obligationId, complianceStatus) => {
    if (!token || !canMutate) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/regulatory/obligations/${obligationId}`, {
        method: "PATCH",
        headers,
        body: JSON.stringify({ compliance_status: complianceStatus }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Obrigacao ${j.obligation_code} → ${j.compliance_status}.`);
      const code = selectedRegulationCode || "GDPR";
      const tr = await fetch(`${API}/regulatory/toolkit?regulation_code=${encodeURIComponent(code)}`, { headers });
      const tj = await tr.json().catch(() => ({}));
      if (tr.ok) setRegulatoryToolkit(tj);
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/regulatory/obligations/...`));
    } finally {
      setLoading(false);
    }
  };

  const tableRows = useMemo(() => {
    if (tab === "regulations") {
      return regulations.map((r) => ({
        key: r.id,
        tipo: "regulation",
        id: r.code,
        detalhe: `${r.name} · ${r.jurisdiction} · retencao ${r.default_retention_days}d · SLA ${r.response_sla_days}d · ${statusLabel(r.active)}`,
      }));
    }
    if (tab === "policies") {
      return policies.map((p) => {
        const reg = regulations.find((r) => r.id === p.regulation_id);
        return {
          key: p.id,
          tipo: "policy",
          id: `${reg?.code || "?"} v${p.version}`,
          detalhe: `${p.title} · vigencia ${p.effective_at?.slice(0, 10) || "—"} · ${p.is_current ? "atual" : "historico"}`,
        };
      });
    }
    if (tab === "consents") {
      return consents.map((c) => ({
        key: c.id,
        tipo: "consent",
        id: c.consent_type,
        detalhe: `${c.regulation_code} · ${c.user_id || c.guest_identifier || "guest"} · ${c.granted && !c.revoked_at ? "concedido" : "revogado"} · ${c.channel || "—"}`,
      }));
    }
    if (tab === "deletions") {
      return deletions.map((d) => ({
        key: d.id,
        tipo: "deletion",
        id: d.id.slice(0, 12),
        detalhe: `${d.regulation_code} · ${d.user_id || "—"} · ${d.status} · ${d.reason || "sem motivo"}`,
      }));
    }
    if (tab === "subject_requests") {
      return subjectRequests.map((s) => ({
        key: s.id,
        tipo: "dsar",
        id: s.request_type,
        detalhe: `${s.regulation_code} · ${s.user_id || s.guest_identifier || "—"} · ${s.status} · prazo ${s.due_at?.slice(0, 10) || "—"}`,
      }));
    }
    if (tab === "integrations") {
      return [
        ...webhookDeliveries.map((d) => ({
          key: d.id,
          tipo: `delivery/${d.status}`,
          id: d.event_name,
          detalhe: `${d.regulation_code} · tentativas ${d.attempt_count} · HTTP ${d.last_status_code ?? "—"} · ${d.delivered_at ? "entregue" : d.status}`,
        })),
        ...webhooks.map((w) => ({
          key: w.id,
          tipo: "webhook",
          id: w.regulation_code,
          detalhe: `${w.url} · ${(w.events || []).join(", ")} · ${w.active ? "ativo" : "inativo"}`,
        })),
      ];
    }
    if (tab === "legal_bases") {
      return legalBases.map((b) => ({
        key: b.id,
        tipo: "legal_basis",
        id: `${b.regulation_code}/${b.code}`,
        detalhe: `${b.name} · ${b.article_ref || "—"} · ${b.requires_consent ? "exige consentimento" : "sem consentimento"}`,
      }));
    }
    if (tab === "data_categories") {
      return dataCategories.map((c) => ({
        key: c.id,
        tipo: "data_category",
        id: `${c.regulation_code}/${c.code}`,
        detalhe: `${c.name} · ${c.sensitivity} · ${c.special_category ? "categoria especial" : "normal"}`,
      }));
    }
    if (tab === "ropa") {
      return processingActivities.map((a) => ({
        key: a.id,
        tipo: "ropa",
        id: `${a.regulation_code}/${a.code}`,
        detalhe: `${a.name} · ${a.status} · retencao ${a.retention_days || "—"}d · ${a.cross_border ? "cross-border" : "local"}`,
      }));
    }
    if (tab === "processors") {
      return [
        ...processors.map((p) => ({
          key: p.id,
          tipo: "processor",
          id: p.name.slice(0, 24),
          detalhe: `${p.processor_type} · ${p.country || "—"} · ${(p.regulation_codes || []).join(", ")}`,
        })),
        ...processorAgreements.map((a) => ({
          key: a.id,
          tipo: "dpa",
          id: `${a.regulation_code}/${a.agreement_type}`,
          detalhe: `processor ${a.processor_id.slice(0, 8)} · ${a.status} · ${a.document_url ? "doc" : "—"}`,
        })),
      ];
    }
    if (tab === "retention") {
      return retentionRules.map((r) => ({
        key: r.id,
        tipo: "retention",
        id: r.regulation_code,
        detalhe: `${r.retention_days}d · ${r.purge_method} · cat ${r.data_category_id?.slice(0, 8) || "—"}`,
      }));
    }
    if (tab === "breaches") {
      return breachIncidents.map((b) => ({
        key: b.id,
        tipo: "breach",
        id: b.title.slice(0, 28),
        detalhe: `${b.regulation_code} · ${b.severity} · ${b.status} · afetados ${b.affected_count ?? "—"}`,
      }));
    }
    if (tab === "dpia") {
      return impactAssessments.map((d) => ({
        key: d.id,
        tipo: "dpia",
        id: d.title.slice(0, 28),
        detalhe: `${d.regulation_code} · risco ${d.risk_level} · ${d.status} · ${d.reviewer || "—"}`,
      }));
    }
    if (tab === "transfers") {
      return transferRecords.map((t) => ({
        key: t.id,
        tipo: "transfer",
        id: `${t.regulation_code}→${t.destination_country}`,
        detalhe: `${t.mechanism} · ${t.status} · ${t.document_ref || "—"}`,
      }));
    }
    if (tab === "ecosystem") {
      return [
        ...(ecosystemHealth?.items || []).map((h) => ({
          key: h.id,
          tipo: `health/${h.status}`,
          id: h.player_code,
          detalhe: `${h.relation_type || "—"} · score ${h.score_pct}% · ${h.latency_ms != null ? `${h.latency_ms}ms` : "—"} · ${h.last_error || "OK"}`,
        })),
        ...ecosystemPlayers.map((p) => ({
          key: p.id,
          tipo: p.player_segment || "player",
          id: p.code,
          detalhe: `${p.name} · ${p.network_type} · ${p.region_group} · ${(p.regulation_codes || []).join(", ")} · ${(p.countries || []).slice(0, 4).join("/")}`,
        })),
        ...ecosystemRelations.map((r) => ({
          key: r.id,
          tipo: r.relation_type,
          id: `${r.from_player_code}→${r.to_player_code}`,
          detalhe: `${r.integration_mode} · ${r.description || "—"}`,
        })),
      ];
    }
    if (tab === "audit") {
      return auditEvents.map((a) => ({
        key: a.id,
        tipo: a.action,
        id: a.resource_type,
        detalhe: `${a.regulation_code || "—"} · ${a.summary} · ${a.created_at?.slice(0, 19) || "—"}`,
      }));
    }
    if (tab === "regulatory_toolkit" && regulatoryToolkit) {
      return [
        ...(regulatoryToolkit.obligations || []).map((o) => ({
          key: o.id,
          tipo: `obl/${o.category}`,
          id: o.obligation_code,
          detalhe: `${o.name} · ${o.compliance_status} · ${o.article_ref || "—"}`,
        })),
        ...(regulatoryToolkit.subject_rights || []).map((r) => ({
          key: r.id,
          tipo: "right",
          id: r.right_code,
          detalhe: `${r.name} · ${r.article_ref || "—"} · SLA ${r.response_sla_days || "—"}d · ${r.automated_available ? "auto" : "manual"}`,
        })),
        ...(regulatoryToolkit.lia_records || []).map((l) => ({
          key: l.id,
          tipo: "lia",
          id: l.title.slice(0, 24),
          detalhe: `${l.regulation_code} · ${l.status} · ${l.reviewer || "—"}`,
        })),
        ...(regulatoryToolkit.opt_out_records || []).map((o) => ({
          key: o.id,
          tipo: `opt/${o.opt_out_type}`,
          id: o.user_id || o.guest_identifier || "—",
          detalhe: `${o.signal_source} · GPC ${o.gpc_signal ? "sim" : "nao"} · ${o.active ? "ativo" : "revogado"}`,
        })),
      ];
    }
    return [];
  }, [tab, regulations, policies, consents, deletions, subjectRequests, webhooks, webhookDeliveries, legalBases, dataCategories, processingActivities, processors, processorAgreements, retentionRules, breachIncidents, impactAssessments, transferRecords, ecosystemPlayers, ecosystemRelations, auditEvents, ecosystemHealth, regulatoryToolkit]);

  const listCount = tableRows.length;

  const listTitle =
    tab === "regulation_hub"
      ? `Hub ${selectedRegulationCode || "—"}`
      : tab === "regulatory_toolkit"
        ? `Toolkit ${selectedRegulationCode || "GDPR"}`
        : tab === "compliance"
        ? `Score compliance ${selectedRegulationCode || "GDPR"}`
        : tab === "audit"
          ? `Trilha de auditoria (${auditEvents.length})`
          : tab === "regulations"
        ? `Marcos regulatorios (${regulations.length})`
        : tab === "policies"
          ? `Politicas de privacidade (${policies.length})`
          : tab === "ropa"
            ? `ROPA — registro de tratamentos (${processingActivities.length})`
            : tab === "legal_bases"
              ? `Bases legais (${legalBases.length})`
              : tab === "data_categories"
                ? `Categorias de dados (${dataCategories.length})`
                : tab === "processors"
                  ? `Processadores e DPA (${processors.length + processorAgreements.length})`
                  : tab === "retention"
                    ? `Regras de retencao (${retentionRules.length})`
                    : tab === "consents"
                      ? `Consentimentos (${consents.length})`
                      : tab === "deletions"
                        ? `Pedidos de eliminacao (${deletions.length})`
                        : tab === "subject_requests"
                          ? `Solicitacoes titular / DSAR (${subjectRequests.length})`
                          : tab === "breaches"
                            ? `Incidentes de violacao (${breachIncidents.length})`
                            : tab === "dpia"
                              ? `DPIA / LIA / PIA (${impactAssessments.length})`
                              : tab === "transfers"
                                ? `Transferencias internacionais (${transferRecords.length})`
                                : tab === "ecosystem"
                                  ? `Ecossistema (${ecosystemPlayers.length} players · ${ecosystemRelations.length} rel · health ${ecosystemHealth?.healthy_count ?? "—"}/${ecosystemHealth?.total ?? "—"} OK)`
                                  : tab === "integrations"
                                  ? `Webhooks + entregas (${webhooks.length} endpoints · ${webhookDeliveries.length} deliveries)`
                                  : "Visao geral";

  const pendingDeletions = deletions.filter((d) => d.status === "PENDING");
  const pendingDsar = subjectRequests.filter((s) => s.status === "PENDING");

  return (
    <div style={pageStyle} data-testid="ops-privacy-compliance-admin-page">
      <section style={cardStyle}>
        <div style={{ display: "flex", justifyContent: "flex-end", flexWrap: "wrap", marginBottom: 10, gap: 8 }}>
          <Link to="/ops/tenants/admin" style={crossShortcutLinkStyle}>
            Tenants
          </Link>
          <Link to="/ops/partners/admin" style={crossShortcutLinkStyle}>
            Parceiros
          </Link>
          <Link to="/ops/marketplace/admin?tab=kyc" style={crossShortcutLinkStyle}>
            Marketplace KYC
          </Link>
          <Link to="/ops/payment-gateway/admin" style={crossShortcutLinkStyle}>
            Payment Gateway
          </Link>
          <Link to="/ops/order-pickup/admin" style={crossShortcutLinkStyle}>
            Order Pickup
          </Link>
          <Link to="/ops/access/user-roles" style={crossShortcutLinkStyle}>
            user_roles
          </Link>
        </div>

        <OpsPageTitleHeader
          title="OPS — Privacy Compliance (global)"
          versionLabel={PAGE_VERSION}
          versionTo="/ops/auth/policy/versioning"
          containerStyle={{ marginBottom: 0 }}
          titleStyle={{ margin: 0 }}
        />
        <p style={mutedTextStyle}>
          Consentimentos, ROPA, bases legais, categorias, processadores/DPA, retencao, DSAR, incidentes, DPIA, transferencias —{" "}
          <code style={{ color: "#e2e8f0" }}>{API}</code> — role{" "}
          <code style={{ color: "#e2e8f0" }}>admin_operacao</code> para escrita.
        </p>

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>Marco regulatorio em foco</h3>
          </div>
          <div style={healthLocalFilterRowStyle}>
            <label style={healthLocalFilterFieldStyle}>
              regulation_code
              <select
                value={selectedRegulationCode}
                onChange={(e) => setSelectedRegulationCode(e.target.value)}
                style={healthLocalFilterInputStyle}
              >
                <option value="">— selecione —</option>
                {regulations.map((r) => (
                  <option key={r.id} value={r.code}>
                    {r.code} — {r.jurisdiction}
                  </option>
                ))}
                {regulations.length === 0
                  ? REGULATION_CODES.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))
                  : null}
              </select>
            </label>
            <label style={healthLocalFilterFieldStyle}>
              filtro listagem
              <select
                value={filterRegulation}
                onChange={(e) => setFilterRegulation(e.target.value)}
                style={healthLocalFilterInputStyle}
              >
                <option value="">— todos —</option>
                {REGULATION_CODES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </label>
          </div>
          {selectedRegulation ? (
            <p style={summary24hHintStyle}>
              {selectedRegulation.name} · DPO {selectedRegulation.dpo_email || "—"} · autoridade{" "}
              {selectedRegulation.supervisory_authority || "—"} · retencao {selectedRegulation.default_retention_days}d · SLA{" "}
              {selectedRegulation.response_sla_days}d
            </p>
          ) : (
            <p style={summary24hHintStyle}>
              Selecione um marco (GDPR, UKGDPR, LGPD, CCPA, PIPEDA, APPI, PDPA_SG, …). Use Listar ou Seed para carregar.
            </p>
          )}
        </section>

        <section style={opsSanityCardStyle}>
          <div style={summary24hHeaderStyle}>
            <h3 style={{ margin: 0, fontSize: 14 }}>Area de cadastro</h3>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {TAB_ITEMS.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  style={tabButtonStyle(tab === t.id)}
                  onClick={() => setTabAndUrl(t.id)}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          {tab === "overview" ? (
            <p style={summary24hHintStyle}>
              KPIs globais + score de maturidade compliance por marco. Use a aba Score compliance para comparar GDPR/LGPD/CCPA.
            </p>
          ) : null}

          {tab === "compliance" ? (
            <p style={summary24hHintStyle}>
              Score ponderado (politica, ROPA, DPA, retencao, DPIA, incidentes, DSAR). Gaps listados por dimensao — evidencia para DPO e auditorias.
            </p>
          ) : null}

          {tab === "audit" ? (
            <p style={summary24hHintStyle}>
              Trilha imutavel de acoes administrativas — seed, publicacao politica, DSAR, incidentes, webhooks e transferencias.
            </p>
          ) : null}

          {tab === "regulation_hub" ? (
            <p style={summary24hHintStyle}>
              Visao 360 do marco em foco (GDPR, LGPD, CCPA, …): tratamentos, subprocessors, titulares pendentes e conformidade operacional.
            </p>
          ) : null}

          {tab === "ropa" ? (
            <p style={summary24hHintStyle}>
              Registro de atividades de tratamento (ROPA) — Art. 30 GDPR / Art. 37 LGPD / inventario CCPA.
            </p>
          ) : null}

          {tab === "processors" ? (
            <p style={summary24hHintStyle}>
              Subprocessadores e redes locker (InPost, DPD, DHL, CTT, Worten, El Corte Inglés, Magalu, Mercado Livre, Correios, Amazon Hub) — DPA/SCC por marco.
            </p>
          ) : null}

          {tab === "breaches" ? (
            <p style={summary24hHintStyle}>
              Gestao de incidentes — notificacao autoridade (72h GDPR / ANPD LGPD / AG CCPA) e titulares afetados.
            </p>
          ) : null}

          {tab === "dpia" ? (
            <p style={summary24hHintStyle}>
              DPIA (GDPR), LIA (LGPD) e PIA (CCPA) vinculados a atividades de alto risco.
            </p>
          ) : null}

          {tab === "transfers" ? (
            <p style={summary24hHintStyle}>
              Transferencias internacionais — SCC, BCR, adequacy decisions e documentacao.
            </p>
          ) : null}

          {tab === "ecosystem" ? (
            <p style={summary24hHintStyle}>
              Redes locker, carriers (UPS, FedEx, DHL, Correios), marketplaces (Magalu, MELI, Amazon, Shopee),
              PUDO (Worten, El Corte Inglés, CTT), agregadores (Cainiao, Melhor Envio, EasyPost) e food delivery
              (iFood, Uber Eats, Glovo). {ecosystemMeta ? `${ecosystemMeta.player_count} players · ${ecosystemMeta.relation_count} relacoes.` : ""}
              {ecosystemHealth ? ` Probes: ${ecosystemHealth.healthy_count} healthy · ${ecosystemHealth.degraded_count} degraded · ${ecosystemHealth.down_count} down · media ${ecosystemHealth.avg_score_pct}%.` : ""}
            </p>
          ) : null}

          {tab === "consents" && consentAnalytics ? (
            <p style={summary24hHintStyle}>
              Analytics 30d: {consentAnalytics.total_granted} concedidos · {consentAnalytics.total_revoked} revogados · opt-out {consentAnalytics.opt_out_rate_pct}% · canais {Object.keys(consentAnalytics.by_channel || {}).join(", ") || "—"}
            </p>
          ) : null}

          {tab === "regulations" ? (
            <p style={summary24hHintStyle}>
              Marcos globais: UE/UK (GDPR, UKGDPR, ePrivacy), Americas (LGPD, CCPA, VCDPA, PIPEDA), APAC (APPI, PIPA_KR, PDPA_SG, AU_PA, DPDP_IN), MENA/África (PDPL_SA, POPIA), CH (FADP).
            </p>
          ) : null}

          {tab === "consents" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                regulation_code
                <select
                  value={consentForm.regulation_code}
                  onChange={(e) => setConsentForm((f) => ({ ...f, regulation_code: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                >
                  {REGULATION_CODES.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </label>
              <label style={healthLocalFilterFieldStyle}>
                consent_type
                <select
                  value={consentForm.consent_type}
                  onChange={(e) => setConsentForm((f) => ({ ...f, consent_type: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                >
                  {CONSENT_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </label>
              <label style={healthLocalFilterFieldStyle}>
                user_id
                <input
                  value={consentForm.user_id}
                  onChange={(e) => setConsentForm((f) => ({ ...f, user_id: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                  placeholder="usr-demo-eu-001"
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                channel
                <select
                  value={consentForm.channel}
                  onChange={(e) => setConsentForm((f) => ({ ...f, channel: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                >
                  {["KIOSK", "WEB", "APP", "API"].map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </label>
              <label style={healthLocalFilterFieldStyle}>
                policy_version
                <input
                  value={consentForm.policy_version}
                  onChange={(e) => setConsentForm((f) => ({ ...f, policy_version: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
            </div>
          ) : null}

          {tab === "deletions" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                regulation_code
                <select
                  value={deletionForm.regulation_code}
                  onChange={(e) => setDeletionForm((f) => ({ ...f, regulation_code: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                >
                  {REGULATION_CODES.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </label>
              <label style={healthLocalFilterFieldStyle}>
                user_id
                <input
                  value={deletionForm.user_id}
                  onChange={(e) => setDeletionForm((f) => ({ ...f, user_id: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                reason
                <input
                  value={deletionForm.reason}
                  onChange={(e) => setDeletionForm((f) => ({ ...f, reason: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                  placeholder="Account closure after pickup"
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                deletion_id (concluir PENDING)
                <select style={healthLocalFilterInputStyle} defaultValue="">
                  <option value="">— selecione apos listar —</option>
                  {pendingDeletions.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.id.slice(0, 12)} · {d.regulation_code}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          ) : null}

          {tab === "subject_requests" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                regulation_code
                <select
                  value={dsarForm.regulation_code}
                  onChange={(e) => {
                    setDsarForm((f) => ({ ...f, regulation_code: e.target.value }));
                    setDsarSelectedRight("");
                    setDsarDraftHint("");
                  }}
                  style={healthLocalFilterInputStyle}
                >
                  {REGULATION_CODES.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </label>
              <label style={healthLocalFilterFieldStyle}>
                direito (prefill DSAR)
                <select
                  value={dsarSelectedRight}
                  onChange={(e) => {
                    const code = e.target.value;
                    setDsarSelectedRight(code);
                    if (code) void onApplyDsarDraft(dsarForm.regulation_code, code);
                  }}
                  style={healthLocalFilterInputStyle}
                >
                  <option value="">— manual / request_type abaixo —</option>
                  {(regulatoryToolkit?.subject_rights || [])
                    .filter((r) => r.regulation_code === dsarForm.regulation_code)
                    .map((r) => (
                      <option key={r.id} value={r.right_code}>
                        {r.right_code} — {r.name}
                      </option>
                    ))}
                </select>
              </label>
              <label style={healthLocalFilterFieldStyle}>
                request_type
                <select
                  value={dsarForm.request_type}
                  onChange={(e) => setDsarForm((f) => ({ ...f, request_type: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                >
                  {DSAR_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </label>
              <label style={healthLocalFilterFieldStyle}>
                user_id
                <input
                  value={dsarForm.user_id}
                  onChange={(e) => setDsarForm((f) => ({ ...f, user_id: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                details
                <input
                  value={dsarForm.details}
                  onChange={(e) => setDsarForm((f) => ({ ...f, details: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                  placeholder="Preenchido automaticamente ao selecionar direito"
                />
              </label>
              {dsarDraftHint ? (
                <p style={{ ...summary24hHintStyle, flex: "1 1 100%", margin: 0 }}>{dsarDraftHint}</p>
              ) : null}
            </div>
          ) : null}

          {tab === "deletions" && pendingDeletions.length === 0 && token ? (
            <p style={summary24hHintStyle}>Nenhuma eliminacao PENDING. Abra pedido ou use Seed.</p>
          ) : null}

          {tab === "subject_requests" && pendingDsar.length === 0 && token ? (
            <p style={summary24hHintStyle}>Nenhum DSAR PENDING. Abra solicitacao ou use Seed.</p>
          ) : null}

          <div style={toolbarStyle}>
            <button type="button" style={buttonGhostStyle} onClick={() => void load()} disabled={loading || !token}>
              {loading ? "Atualizando..." : "Listar"}
            </button>
            {canMutate ? (
              <>
                <button type="button" style={buttonGhostStyle} onClick={() => void onSeed()} disabled={loading}>
                  Seed
                </button>
                {tab === "consents" ? (
                  <button
                    type="button"
                    style={buttonPrimaryStyle}
                    onClick={() => void onCreateConsent()}
                    disabled={loading || !consentForm.regulation_code || !consentForm.consent_type}
                  >
                    Registrar consentimento
                  </button>
                ) : null}
                {tab === "deletions" ? (
                  <>
                    <button
                      type="button"
                      style={buttonPrimaryStyle}
                      onClick={() => void onCreateDeletion()}
                      disabled={loading || !deletionForm.regulation_code || !deletionForm.user_id}
                    >
                      Abrir eliminacao
                    </button>
                    {pendingDeletions[0] ? (
                      <button
                        type="button"
                        style={buttonGhostStyle}
                        onClick={() => void onCompleteDeletion(pendingDeletions[0].id)}
                        disabled={loading}
                      >
                        Concluir 1o PENDING
                      </button>
                    ) : null}
                  </>
                ) : null}
                {tab === "subject_requests" ? (
                  <button
                    type="button"
                    style={buttonPrimaryStyle}
                    onClick={() => void onCreateDsar()}
                    disabled={loading || !dsarForm.regulation_code || !dsarForm.user_id}
                  >
                    Abrir DSAR
                  </button>
                ) : null}
              </>
            ) : null}
          </div>
        </section>

        {tab === "integrations" || tab === "consents" || tab === "deletions" ? (
          <section style={opsSanityCardStyle}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 14 }}>Webhook e API key (marco regulatorio)</h3>
            </div>
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                regulation_code
                <select
                  value={selectedRegulationCode}
                  onChange={(e) => setSelectedRegulationCode(e.target.value)}
                  style={healthLocalFilterInputStyle}
                >
                  <option value="">— selecione —</option>
                  {(regulations.length ? regulations : REGULATION_CODES.map((c) => ({ id: c, code: c }))).map((r) => (
                    <option key={r.id || r.code} value={r.code}>
                      {r.code}
                    </option>
                  ))}
                </select>
              </label>
              <label style={healthLocalFilterFieldStyle}>
                webhook URL
                <input value={webhookUrl} onChange={(e) => setWebhookUrl(e.target.value)} style={healthLocalFilterInputStyle} />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                secret (opcional)
                <input value={webhookSecret} onChange={(e) => setWebhookSecret(e.target.value)} style={healthLocalFilterInputStyle} />
              </label>
            </div>
            <div style={toolbarStyle}>
              <button
                type="button"
                style={buttonGhostStyle}
                onClick={() => void onWebhook()}
                disabled={!canMutate || !selectedRegulationCode || !webhookUrl}
              >
                Salvar webhook
              </button>
              <button
                type="button"
                style={buttonGhostStyle}
                onClick={() => void onRotateKey()}
                disabled={!canMutate || !selectedRegulationCode}
              >
                Rotacionar API key
              </button>
            </div>
            {lastApiKey ? (
              <p style={apiKeyBannerStyle}>
                API key: <code>{lastApiKey}</code>
              </p>
            ) : null}
          </section>
        ) : null}

        {err ? (
          <div style={criticalBannerStyle} role="alert">
            {err}
          </div>
        ) : null}
        {ok ? <p style={okBannerStyle}>{ok}</p> : null}
        {!token ? <p style={summary24hHintStyle}>Faca login com perfil admin_operacao.</p> : null}
        {token && !canMutate ? <p style={summary24hHintStyle}>Escrita exige admin_operacao.</p> : null}

        {tab === "overview" && dashboard ? (
          <section style={opsSanityCardStyle}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 14 }}>{listTitle}</h3>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 12 }}>
              {[
                ["Marcos regulatorios", dashboard.regulations],
                ["Politicas ativas", dashboard.active_policies],
                ["ROPA / tratamentos", dashboard.processing_activities],
                ["Bases legais", dashboard.legal_bases],
                ["Categorias dados", dashboard.data_categories],
                ["Processadores", dashboard.processors],
                ["DPAs ativos", dashboard.active_dpas],
                ["Regras retencao", dashboard.retention_rules],
                ["Incidentes abertos", dashboard.open_breaches],
                ["DPIA pendentes", dashboard.dpia_pending],
                ["Transferencias ativas", dashboard.active_transfers],
                ["Eliminacoes pendentes", dashboard.pending_deletions],
                ["DSAR pendentes", dashboard.pending_subject_requests],
                ["Consentimentos ativos", dashboard.consents_granted],
                ["Webhooks ativos", dashboard.webhooks_active],
                isComplianceScore(complianceScore)
                  ? [`Score ${selectedRegulationCode || "GDPR"}`, `${complianceScore.score_pct}% (${complianceScore.grade})`]
                  : null,
              ].filter(Boolean).map(([label, value]) => (
                <div key={label} style={{ padding: 10, borderRadius: 8, border: "1px solid rgba(148,163,184,0.25)" }}>
                  <p style={{ margin: 0, fontSize: 11, opacity: 0.75 }}>{label}</p>
                  <p style={{ margin: "4px 0 0", fontSize: 18, fontWeight: 600 }}>{value}</p>
                </div>
              ))}
            </div>
            {complianceScoreHint ? (
              <p style={summary24hHintStyle}>{complianceScoreHint}</p>
            ) : null}
          </section>
        ) : null}

        {tab === "compliance" && !isComplianceScore(complianceScore) && complianceScoreHint ? (
          <p style={summary24hHintStyle}>{complianceScoreHint}</p>
        ) : null}

        {tab === "compliance" && isComplianceScore(complianceScore) ? (
          <section style={opsSanityCardStyle}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 14 }}>
                {complianceScore.regulation_name} — {complianceScore.score_pct}% (nota {complianceScore.grade})
              </h3>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 12, marginBottom: 12 }}>
              {(complianceScore.dimensions || []).map((d) => (
                <div key={d.key} style={{ padding: 10, borderRadius: 8, border: "1px solid rgba(148,163,184,0.25)" }}>
                  <p style={{ margin: 0, fontSize: 11, opacity: 0.75 }}>{d.label} ({d.weight_pct}%)</p>
                  <p style={{ margin: "4px 0 0", fontSize: 16, fontWeight: 600 }}>{d.score_pct}% · {d.status}</p>
                  <p style={{ margin: "4px 0 0", fontSize: 11, opacity: 0.7 }}>{d.detail}</p>
                </div>
              ))}
            </div>
            {complianceScore.gaps?.length ? (
              <p style={criticalBannerStyle}>Gaps: {complianceScore.gaps.join(" · ")}</p>
            ) : (
              <p style={okBannerStyle}>Sem gaps criticos neste marco.</p>
            )}
            {complianceCompare?.scores?.length ? (
              <div style={{ marginTop: 12 }}>
                <p style={{ margin: "0 0 8px", fontSize: 13, fontWeight: 600 }}>Comparativo GDPR / LGPD / CCPA</p>
                <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                  {complianceCompare.scores.map((s) => (
                    <div key={s.regulation_code} style={{ padding: 8, borderRadius: 8, border: "1px solid rgba(148,163,184,0.25)" }}>
                      {s.regulation_code}: {s.score_pct}% ({s.grade})
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </section>
        ) : null}

        {tab === "ropa" ? (
          <section style={opsSanityCardStyle}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 14 }}>Mapa de fluxo ROPA — {selectedRegulationCode || filterRegulation || "GDPR"}</h3>
            </div>
            <RopaFlowGraph graph={ropaGraph} loading={ropaGraphLoading} error={ropaGraphErr} />
          </section>
        ) : null}

        {tab === "transfers" ? (
          <section style={opsSanityCardStyle}>
            <div style={{ ...summary24hHeaderStyle, flexWrap: "wrap", gap: 8 }}>
              <h3 style={{ margin: 0, fontSize: 14 }}>Wizard SCC / BCR / Adequacy</h3>
              {canMutate ? (
                <button type="button" style={buttonPrimaryStyle} onClick={() => void onStartTransferWizard()} disabled={loading}>
                  Iniciar wizard
                </button>
              ) : null}
            </div>
            {transferWizard ? (
              <div style={{ fontSize: 13, marginBottom: 10 }}>
                <p style={summary24hHintStyle}>
                  Sessao {transferWizard.id.slice(0, 12)} · passo <strong>{transferWizard.current_step}</strong>
                  {transferWizard.destination_country ? ` · destino ${transferWizard.destination_country}` : ""}
                  {transferWizard.mechanism ? ` · ${transferWizard.mechanism}` : ""}
                </p>
                {transferWizard.current_step === "SCOPE" && canMutate ? (
                  <button type="button" style={buttonGhostStyle} onClick={() => void onAdvanceTransferWizard({ step: "SCOPE", destination_country: "US" })} disabled={loading}>
                    Scope → US
                  </button>
                ) : null}
                {transferWizard.current_step === "MECHANISM" && canMutate ? (
                  <button type="button" style={buttonGhostStyle} onClick={() => void onAdvanceTransferWizard({ step: "MECHANISM", mechanism: "SCC" })} disabled={loading}>
                    Mecanismo SCC
                  </button>
                ) : null}
                {transferWizard.current_step === "PROCESSOR" && canMutate ? (
                  <button type="button" style={buttonGhostStyle} onClick={() => void onAdvanceTransferWizard({ step: "PROCESSOR" })} disabled={loading}>
                    Processador (opcional)
                  </button>
                ) : null}
                {transferWizard.current_step === "DOCUMENT" && canMutate ? (
                  <button type="button" style={buttonGhostStyle} onClick={() => void onAdvanceTransferWizard({ step: "DOCUMENT", document_ref: `SCC-${selectedRegulationCode || "GDPR"}-${Date.now()}` })} disabled={loading}>
                    Documento SCC
                  </button>
                ) : null}
                {transferWizard.current_step === "REVIEW" && canMutate ? (
                  <button type="button" style={buttonPrimaryStyle} onClick={() => void onCompleteTransferWizard()} disabled={loading}>
                    Finalizar → privacy_transfer_records
                  </button>
                ) : null}
              </div>
            ) : (
              <p style={summary24hHintStyle}>Passos: SCOPE → MECHANISM → PROCESSOR → DOCUMENT → REVIEW → registro ativo.</p>
            )}
          </section>
        ) : null}

        {tab === "integrations" && canMutate ? (
          <section style={opsSanityCardStyle}>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
              <button type="button" style={buttonGhostStyle} onClick={() => void onDispatchTestWebhook()} disabled={loading}>
                Disparar teste consent.granted
              </button>
              <span style={summary24hHintStyle}>DLQ privacy_webhook_deliveries · simula hooks.ellanlab.example</span>
            </div>
          </section>
        ) : null}

        {tab === "ecosystem" && (globalOpsBridge || playerCertifications.length) ? (
          <section style={opsSanityCardStyle}>
            <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 8, marginBottom: 8 }}>
              <h3 style={{ margin: 0, fontSize: 14 }}>Bridge Partner global-ops</h3>
              {canMutate ? (
                <button type="button" style={buttonGhostStyle} onClick={() => void onSyncGlobalOpsCerts()} disabled={loading}>
                  Sync certificacoes
                </button>
              ) : null}
            </div>
            {globalOpsBridge ? (
              <p style={summary24hHintStyle}>
                {globalOpsBridge.certifications_valid}/{globalOpsBridge.certifications_cached} certificacoes validas ·
                bridge {globalOpsBridge.bridge_status} · readiness rows {globalOpsBridge.partner_readiness_rows}
              </p>
            ) : null}
            {playerCertifications.length ? (
              <p style={{ fontSize: 12, opacity: 0.85 }}>
                {playerCertifications.slice(0, 6).map((c) => `${c.player_code}/${c.certification_type}`).join(" · ")}
                {playerCertifications.length > 6 ? " …" : ""}
              </p>
            ) : null}
          </section>
        ) : null}

        {tab === "ecosystem" && playerLegalDocuments.length ? (
          <section style={opsSanityCardStyle}>
            <h3 style={{ margin: "0 0 8px", fontSize: 14 }}>Documentos legais por player ({playerLegalDocuments.length})</h3>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {playerLegalDocuments.slice(0, 30).map((d) => (
                <a
                  key={d.id}
                  href={d.public_path}
                  target="_blank"
                  rel="noreferrer"
                  style={{ fontSize: 12, color: "#38bdf8" }}
                >
                  {d.player_code} v{d.version} ({d.regulation_code})
                </a>
              ))}
            </div>
            <p style={{ margin: "8px 0 0", fontSize: 11, opacity: 0.75 }}>
              Indice publico: <a href="/legal/privacy/players" target="_blank" rel="noreferrer">/legal/privacy/players</a>
            </p>
          </section>
        ) : null}

        {tab === "regulatory_toolkit" && regulatoryToolkit ? (
          <section style={opsSanityCardStyle}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 14 }}>
                {regulatoryToolkit.regulation_name} ({regulatoryToolkit.jurisdiction})
              </h3>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))", gap: 10, marginBottom: 12 }}>
              {[
                ["Direitos titular", regulatoryToolkit.summary?.subject_rights_count],
                ["Obrigacoes", regulatoryToolkit.summary?.obligations_count],
                ["% compliant", `${regulatoryToolkit.summary?.obligations_compliant_pct ?? 0}%`],
                ["LIA", regulatoryToolkit.summary?.lia_count],
                ["Opt-outs", regulatoryToolkit.summary?.opt_out_count],
                ["Prazo incidente", regulatoryToolkit.summary?.breach_notification_hours ? `${regulatoryToolkit.summary.breach_notification_hours}h` : "variavel"],
              ].map(([label, value]) => (
                <div key={label} style={{ padding: 10, borderRadius: 8, border: "1px solid rgba(148,163,184,0.25)" }}>
                  <p style={{ margin: 0, fontSize: 11, opacity: 0.75 }}>{label}</p>
                  <p style={{ margin: "4px 0 0", fontSize: 17, fontWeight: 600 }}>{value}</p>
                </div>
              ))}
            </div>
            {regulatoryToolkit.authority_templates?.length ? (
              <div style={{ marginBottom: 12 }}>
                <p style={{ margin: "0 0 6px", fontSize: 12, fontWeight: 600 }}>Notificacao autoridade</p>
                {regulatoryToolkit.authority_templates.map((t) => (
                  <p key={t.regulation_code} style={{ margin: 0, fontSize: 12, opacity: 0.9 }}>
                    {t.authority_name} · {t.deadline_label} · {t.channel}
                  </p>
                ))}
              </div>
            ) : null}
            {rightsCompare ? (
              <p style={{ margin: 0, fontSize: 12, opacity: 0.85 }}>
                Comparativo GDPR/LGPD/CCPA: tipos DSAR comuns {rightsCompare.common_dsar_types?.join(", ") || "—"}
              </p>
            ) : null}
            {regulatoryToolkit.subject_rights?.length ? (
              <div style={{ marginTop: 12 }}>
                <p style={{ margin: "0 0 6px", fontSize: 12, fontWeight: 600 }}>Direitos → DSAR pre-preenchido</p>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                  {regulatoryToolkit.subject_rights.slice(0, 8).map((r) => (
                    <button
                      key={r.id}
                      type="button"
                      style={buttonGhostStyle}
                      disabled={loading}
                      onClick={() => void onApplyDsarDraft(regulatoryToolkit.regulation_code, r.right_code, true)}
                    >
                      DSAR: {r.right_code}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}
            {canMutate && regulatoryToolkit.obligations?.length ? (
              <div style={{ marginTop: 10, display: "flex", flexWrap: "wrap", gap: 6 }}>
                {regulatoryToolkit.obligations.slice(0, 4).map((o) => (
                  <button
                    key={o.id}
                    type="button"
                    style={buttonGhostStyle}
                    disabled={loading}
                    onClick={() => void onPatchObligation(o.id, o.compliance_status === "COMPLIANT" ? "PARTIAL" : "COMPLIANT")}
                  >
                    {o.obligation_code}: marcar {o.compliance_status === "COMPLIANT" ? "parcial" : "OK"}
                  </button>
                ))}
              </div>
            ) : null}
          </section>
        ) : tab === "regulatory_toolkit" && regulatoryToolkitErr ? (
          <p style={criticalBannerStyle} role="alert">
            {regulatoryToolkitErr}
          </p>
        ) : tab === "regulatory_toolkit" && token && !loading ? (
          <p style={summary24hHintStyle}>Selecione GDPR, LGPD ou CCPA em foco. Execute Seed se o toolkit estiver vazio.</p>
        ) : null}

        {tab === "regulation_hub" && regulationHub ? (
          <section style={opsSanityCardStyle}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 14 }}>
                {listTitle} — {regulationHub.regulation_name} ({regulationHub.jurisdiction})
              </h3>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: 12 }}>
              {[
                ["ROPA", regulationHub.processing_activities],
                ["Bases legais", regulationHub.legal_bases],
                ["Categorias", regulationHub.data_categories],
                ["Processadores", regulationHub.processors],
                ["DPAs", regulationHub.active_dpas],
                ["Retencao", regulationHub.retention_rules],
                ["Incidentes abertos", regulationHub.open_breaches],
                ["DPIA pendentes", regulationHub.dpia_pending],
                ["Transferencias", regulationHub.active_transfers],
                ["DSAR pendentes", regulationHub.pending_dsar],
                ["Eliminacoes pendentes", regulationHub.pending_deletions],
                ["Consentimentos", regulationHub.active_consents],
              ].map(([label, value]) => (
                <div key={label} style={{ padding: 10, borderRadius: 8, border: "1px solid rgba(148,163,184,0.25)" }}>
                  <p style={{ margin: 0, fontSize: 11, opacity: 0.75 }}>{label}</p>
                  <p style={{ margin: "4px 0 0", fontSize: 18, fontWeight: 600 }}>{value}</p>
                </div>
              ))}
            </div>
          </section>
        ) : tab === "regulation_hub" && token && !loading ? (
          <p style={hubHint ? criticalBannerStyle : summary24hHintStyle} role={hubHint ? "alert" : undefined}>
            {hubHint || "Selecione GDPR, LGPD ou CCPA em foco. Os dados carregam automaticamente apos login."}
          </p>
        ) : null}

        {tab !== "overview" && tab !== "regulation_hub" && tab !== "regulatory_toolkit" && tab !== "compliance" && tab !== "ropa" && listCount > 0 ? (
          <section style={opsSanityCardStyle}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 14 }}>{listTitle}</h3>
            </div>
            <div style={{ overflowX: "auto" }}>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    {["tipo", "id", "detalhe"].map((h) => (
                      <th key={h} style={thStyle}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {tableRows.map((row) => (
                    <tr key={row.key}>
                      <td style={tdStyle}>{row.tipo}</td>
                      <td style={tdStyle}>
                        <code>{row.id}</code>
                      </td>
                      <td style={tdStyle}>{row.detalhe}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ) : tab !== "overview" && tab !== "regulation_hub" && tab !== "regulatory_toolkit" && tab !== "compliance" && tab !== "ropa" && token && !loading ? (
          <p style={summary24hHintStyle}>Nenhum registro. Use Listar ou Seed (admin_operacao).</p>
        ) : null}
      </section>
    </div>
  );
}
