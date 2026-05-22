
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OpsPageTitleHeader from "../components/OpsPageTitleHeader";
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

const BASE = import.meta.env.VITE_ML_ADMIN_BASE_URL || "/api/mla";
const API = `${BASE}/v1/ml-admin`;
const PAGE_VERSION = "ops/ml/admin v0.4";

const TAB_ITEMS = [
  { id: "overview", label: "Visao geral" },
  { id: "use_cases", label: "Casos de uso" },
  { id: "registry", label: "Model registry" },
  { id: "training", label: "Experimentos" },
  { id: "partners", label: "Parceiros ML" },
  { id: "networks", label: "Redes locker" },
  { id: "readiness", label: "Prontidao ML" },
  { id: "models", label: "Metadata" },
  { id: "catalog", label: "Catalogo features" },
  { id: "features", label: "Features diarias" },
  { id: "predictions", label: "Predicoes" },
  { id: "drift", label: "Drift" },
  { id: "governance", label: "SLO e alertas" },
  { id: "deployments", label: "Deployments" },
  { id: "grants", label: "Acesso parceiro" },
  { id: "feedback", label: "Feedback" },
];

function parseError(payload, fallback = "Falha na API ml-admin.") {
  if (!payload) return fallback;
  if (typeof payload?.detail === "string" && payload.detail.trim()) return payload.detail.trim();
  return fallback;
}

function normalizeNetworkError(err, endpoint) {
  const raw = String(err?.message || err || "").trim();
  if (!raw) return "Falha de comunicacao com a API.";
  const lower = raw.toLowerCase();
  if (lower.includes("failed to fetch") || lower.includes("networkerror")) {
    return `Falha de conexao (${endpoint}). Verifique proxy ${BASE} (porta 8021).`;
  }
  return raw;
}

function formatPct(v) {
  const n = Number(v);
  if (!Number.isFinite(n)) return "—";
  return `${(n * 100).toFixed(1)}%`;
}

function formatHealth(v) {
  const n = Number(v);
  if (!Number.isFinite(n)) return "—";
  return n.toFixed(1);
}

function activeModelVersion(models) {
  const active = models.find((m) => m.status === "ACTIVE");
  return active?.model_version || "";
}

export default function OpsMlAdminPage() {
  const { token, hasRole } = useAuth();
  const canMutate = hasRole("admin_operacao");
  const [searchParams, setSearchParams] = useSearchParams();
  const initialTab = searchParams.get("tab") || "overview";
  const [tab, setTab] = useState(TAB_ITEMS.some((t) => t.id === initialTab) ? initialTab : "overview");
  const [dash, setDash] = useState(null);
  const [partners, setPartners] = useState([]);
  const [models, setModels] = useState([]);
  const [features, setFeatures] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [feedback, setFeedback] = useState([]);
  const [useCases, setUseCases] = useState([]);
  const [registry, setRegistry] = useState([]);
  const [trainingRuns, setTrainingRuns] = useState([]);
  const [featureCatalog, setFeatureCatalog] = useState([]);
  const [driftReports, setDriftReports] = useState([]);
  const [slos, setSlos] = useState([]);
  const [alertRules, setAlertRules] = useState([]);
  const [deployments, setDeployments] = useState([]);
  const [grants, setGrants] = useState([]);
  const [networkPlayers, setNetworkPlayers] = useState([]);
  const [networkProfiles, setNetworkProfiles] = useState([]);
  const [playerCapabilities, setPlayerCapabilities] = useState([]);
  const [playerRelations, setPlayerRelations] = useState([]);
  const [mlReadiness, setMlReadiness] = useState([]);
  const [mlReadinessHub, setMlReadinessHub] = useState(null);
  const [networkPriorityOnly, setNetworkPriorityOnly] = useState(false);
  const [selectedUseCase, setSelectedUseCase] = useState("");
  const [useCaseForm, setUseCaseForm] = useState({ code: "", name: "", domain: "LOCKER", tier: "STANDARD" });
  const [registryForm, setRegistryForm] = useState({ model_version: "", algorithm: "RandomForest", stage: "DEV" });
  const [trainingForm, setTrainingForm] = useState({ run_name: "" });
  const [catalogForm, setCatalogForm] = useState({ feature_name: "", feature_group: "telemetry", source_table: "ml_features_daily" });
  const [driftForm, setDriftForm] = useState({ model_version: "rf-v1-demo", psi_score: "0.1", status: "OK" });
  const [sloForm, setSloForm] = useState({ p95_latency_ms: "500", min_availability_pct: "99.5" });
  const [alertForm, setAlertForm] = useState({ rule_code: "DRIFT_PSI", metric: "psi_score", threshold: "0.25" });
  const [grantPartnerId, setGrantPartnerId] = useState("");
  const [promoteRegistryId, setPromoteRegistryId] = useState("");
  const [partnerForm, setPartnerForm] = useState({ name: "", code: "", partner_type: "TELEMETRY" });
  const [modelForm, setModelForm] = useState({ model_version: "", status: "ACTIVE" });
  const [featureForm, setFeatureForm] = useState({
    locker_id: "",
    feature_date: "",
    battery_min: "",
    door_failures_7d: "0",
  });
  const [predForm, setPredForm] = useState({
    locker_id: "",
    failure_probability: "0.12",
    health_score: "88",
    model_version: "",
  });
  const [featureLockerFilter, setFeatureLockerFilter] = useState("");
  const [predLockerFilter, setPredLockerFilter] = useState("");
  const [selectedPartner, setSelectedPartner] = useState("");
  const [webhookUrl, setWebhookUrl] = useState("");
  const [webhookSecret, setWebhookSecret] = useState("");
  const [lastApiKey, setLastApiKey] = useState("");
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

  const setTabAndUrl = (next) => {
    setTab(next);
    if (next === "overview") {
      setSearchParams({}, { replace: true });
    } else {
      setSearchParams({ tab: next }, { replace: true });
    }
  };

  useEffect(() => {
    const q = searchParams.get("tab");
    if (!q && tab !== "overview") setTab("overview");
    if (q && TAB_ITEMS.some((t) => t.id === q) && q !== tab) setTab(q);
  }, [searchParams, tab]);

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setErr("");
    setOk("");
    try {
      const featQ = featureLockerFilter ? `?locker_id=${encodeURIComponent(featureLockerFilter)}&limit=80` : "?limit=80";
      const predQ = predLockerFilter ? `?locker_id=${encodeURIComponent(predLockerFilter)}&limit=80` : "?limit=80";
      const netQ = networkPriorityOnly ? "?active_only=true&priority_only=true" : "?active_only=true";
      const [d, p, m, f, pr, fb, uc, reg, tr, cat, dr, slo, al, dep, gr, net, nprof, pcap, prel, mlrd, mlhub] = await Promise.all([
        fetch(`${API}/dashboard`, { headers }),
        fetch(`${API}/ml-data-partners`, { headers }),
        fetch(`${API}/ml-model-metadata`, { headers }),
        fetch(`${API}/ml-features-daily${featQ}`, { headers }),
        fetch(`${API}/ml-predictions-log${predQ}`, { headers }),
        fetch(`${API}/ml-prediction-feedback?limit=80`, { headers }),
        fetch(`${API}/ml-use-cases`, { headers }),
        fetch(`${API}/ml-model-registry`, { headers }),
        fetch(`${API}/ml-training-runs?limit=50`, { headers }),
        fetch(`${API}/ml-feature-definitions`, { headers }),
        fetch(`${API}/ml-drift-reports?limit=50`, { headers }),
        fetch(`${API}/ml-inference-slo`, { headers }),
        fetch(`${API}/ml-alert-rules`, { headers }),
        fetch(`${API}/ml-deployment-events?limit=50`, { headers }),
        fetch(`${API}/ml-partner-use-case-grants`, { headers }),
        fetch(`${API}/ml-locker-network-players${netQ}`, { headers }),
        fetch(`${API}/ml-network-ml-profiles`, { headers }),
        fetch(`${API}/ml-player-capabilities`, { headers }),
        fetch(`${API}/ml-player-relations`, { headers }),
        fetch(`${API}/ml-integration-readiness?limit=80`, { headers }),
        fetch(`${API}/ml-readiness-hub/summary`, { headers }),
      ]);
      const bodies = await Promise.all(
        [d, p, m, f, pr, fb, uc, reg, tr, cat, dr, slo, al, dep, gr, net, nprof, pcap, prel, mlrd, mlhub].map((r) =>
          r.json().catch(() => ({})),
        ),
      );
      if (!d.ok) throw new Error(parseError(bodies[0]));
      setDash(bodies[0]);
      setPartners(bodies[1].partners || []);
      const modelList = bodies[2].items || [];
      setModels(modelList);
      setFeatures(bodies[3].items || []);
      setPredictions(bodies[4].items || []);
      setFeedback(bodies[5].items || []);
      const ucList = bodies[6].items || [];
      setUseCases(ucList);
      setRegistry(bodies[7].items || []);
      setTrainingRuns(bodies[8].items || []);
      setFeatureCatalog(bodies[9].items || []);
      setDriftReports(bodies[10].items || []);
      setSlos(bodies[11].items || []);
      setAlertRules(bodies[12].items || []);
      setDeployments(bodies[13].items || []);
      setGrants(bodies[14].items || []);
      setNetworkPlayers(bodies[15].items || []);
      setNetworkProfiles(bodies[16].items || []);
      setPlayerCapabilities(bodies[17].items || []);
      setPlayerRelations(bodies[18].items || []);
      setMlReadiness(bodies[19].items || []);
      setMlReadinessHub(bodies[20] || null);
      setSelectedUseCase((prev) => prev || ucList[0]?.id || "");
      setGrantPartnerId((prev) => prev || bodies[1].partners?.[0]?.id || "");
      const ver = activeModelVersion(modelList);
      if (ver) {
        setPredForm((f) => (f.model_version ? f : { ...f, model_version: ver }));
      }
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
      setDash(null);
      setPartners([]);
      setModels([]);
      setFeatures([]);
      setPredictions([]);
      setFeedback([]);
      setUseCases([]);
      setRegistry([]);
      setTrainingRuns([]);
      setFeatureCatalog([]);
      setDriftReports([]);
      setSlos([]);
      setAlertRules([]);
      setDeployments([]);
      setGrants([]);
      setNetworkPlayers([]);
      setNetworkProfiles([]);
      setPlayerCapabilities([]);
      setPlayerRelations([]);
    } finally {
      setLoading(false);
    }
  }, [token, headers, networkPriorityOnly, featureLockerFilter, predLockerFilter]);

  useEffect(() => {
    void load();
  }, [load]);

  const onSeedNetworks = async () => {
    if (!token || !canMutate) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/ml-locker-network-players/seed-from-catalog`, { method: "POST", headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(
        `Redes locker: ${j.inserted ?? 0} novas, ${j.updated ?? 0} atualizadas, ${j.profiles_created ?? 0} perfis ML, catálogo ${j.catalog_size ?? 0}.`,
      );
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/ml-locker-network-players/seed-from-catalog`));
    } finally {
      setLoading(false);
    }
  };

  const onSeed = async () => {
    if (!token || !canMutate) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/seed`, { method: "POST", headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk("Seed ML aplicado (casos de uso, redes locker mundiais, registry, catalogo, SLO, drift e demo locker).");
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/seed`));
    } finally {
      setLoading(false);
    }
  };

  const onValidate = async () => {
    if (!token || !canMutate) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/ops/validate-feedback`, { method: "POST", headers });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Validacao de feedback: ${j.inserted ?? 0} registros inseridos (${j.candidates ?? 0} candidatos).`);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/ops/validate-feedback`));
    } finally {
      setLoading(false);
    }
  };

  const onCreatePartner = async () => {
    if (!token || !canMutate || !partnerForm.name || !partnerForm.code) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/ml-data-partners`, {
        method: "POST",
        headers,
        body: JSON.stringify(partnerForm),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setSelectedPartner(j.id);
      setOk(`Parceiro ML ${j.code} criado.`);
      setPartnerForm({ name: "", code: "", partner_type: "TELEMETRY" });
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/ml-data-partners`));
    } finally {
      setLoading(false);
    }
  };

  const onWebhook = async () => {
    if (!token || !canMutate || !selectedPartner || !webhookUrl) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/ml-data-partners/${encodeURIComponent(selectedPartner)}/webhook`, {
        method: "PUT",
        headers,
        body: JSON.stringify({
          url: webhookUrl,
          secret: webhookSecret || undefined,
          events: ["prediction.*", "feedback.*"],
        }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Webhook salvo para parceiro ${selectedPartner}.`);
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/ml-data-partners/.../webhook`));
    } finally {
      setLoading(false);
    }
  };

  const onRotateKey = async () => {
    if (!token || !canMutate || !selectedPartner) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(
        `${API}/ml-data-partners/${encodeURIComponent(selectedPartner)}/api-keys/rotate`,
        { method: "POST", headers },
      );
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setLastApiKey(j.api_key || "");
      setOk(`Nova API key (${j.key_prefix}…). Copie agora.`);
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/ml-data-partners/.../api-keys/rotate`));
    } finally {
      setLoading(false);
    }
  };

  const onCreateModel = async () => {
    if (!token || !canMutate || !modelForm.model_version) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/ml-model-metadata`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          model_version: modelForm.model_version,
          status: modelForm.status,
          metrics: { registered_via: "ops" },
        }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Modelo ${j.model_version} registrado (${j.status}).`);
      setModelForm({ model_version: "", status: "ACTIVE" });
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/ml-model-metadata`));
    } finally {
      setLoading(false);
    }
  };

  const onCreateFeature = async () => {
    if (!token || !canMutate || !featureForm.locker_id || !featureForm.feature_date) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/ml-features-daily`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          locker_id: featureForm.locker_id,
          feature_date: featureForm.feature_date,
          battery_min: featureForm.battery_min ? Number(featureForm.battery_min) : null,
          door_failures_7d: Number(featureForm.door_failures_7d) || 0,
          usage_events_7d: 0,
          uptime_hours_7d: 0,
          failure_label_7d: 0,
        }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Feature ${j.locker_id} · ${j.feature_date} criada.`);
      setFeatureForm({ locker_id: "", feature_date: "", battery_min: "", door_failures_7d: "0" });
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/ml-features-daily`));
    } finally {
      setLoading(false);
    }
  };

  const onCreatePrediction = async () => {
    if (!token || !canMutate || !predForm.locker_id || !predForm.model_version) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/ml-predictions-log`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          locker_id: predForm.locker_id,
          failure_probability: Number(predForm.failure_probability),
          health_score: Number(predForm.health_score),
          model_version: predForm.model_version,
        }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Predicao registrada para ${j.locker_id} (health ${j.health_score}).`);
      setPredForm((f) => ({ ...f, locker_id: "" }));
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, `${API}/ml-predictions-log`));
    } finally {
      setLoading(false);
    }
  };

  const useCaseLabel = (id) => useCases.find((u) => u.id === id)?.code || id;

  const postJson = async (path, body) => {
    const r = await fetch(`${API}${path}`, { method: "POST", headers, body: JSON.stringify(body) });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(parseError(j));
    return j;
  };

  const onCreateUseCase = async () => {
    if (!canMutate || !useCaseForm.code || !useCaseForm.name) return;
    setLoading(true);
    setErr("");
    try {
      const j = await postJson("/ml-use-cases", useCaseForm);
      setSelectedUseCase(j.id);
      setOk(`Caso de uso ${j.code} criado.`);
      setUseCaseForm({ code: "", name: "", domain: "LOCKER", tier: "STANDARD" });
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
    } finally {
      setLoading(false);
    }
  };

  const onCreateRegistry = async () => {
    if (!canMutate || !selectedUseCase || !registryForm.model_version) return;
    setLoading(true);
    setErr("");
    try {
      await postJson("/ml-model-registry", { use_case_id: selectedUseCase, ...registryForm });
      setOk("Entrada no model registry criada.");
      setRegistryForm({ model_version: "", algorithm: "RandomForest", stage: "DEV" });
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
    } finally {
      setLoading(false);
    }
  };

  const onPromoteRegistry = async () => {
    if (!canMutate || !promoteRegistryId) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/ml-model-registry/${encodeURIComponent(promoteRegistryId)}/promote`, {
        method: "POST",
        headers,
        body: JSON.stringify({ actor_id: "ops-ui" }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk(`Modelo ${j.model_version} promovido para PRODUCTION.`);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
    } finally {
      setLoading(false);
    }
  };

  const onCreateTraining = async () => {
    if (!canMutate || !selectedUseCase || !trainingForm.run_name) return;
    setLoading(true);
    setErr("");
    try {
      await postJson("/ml-training-runs", { use_case_id: selectedUseCase, run_name: trainingForm.run_name, triggered_by: "ops-ui" });
      setOk("Experimento enfileirado (QUEUED).");
      setTrainingForm({ run_name: "" });
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
    } finally {
      setLoading(false);
    }
  };

  const onCreateCatalogFeature = async () => {
    if (!canMutate || !catalogForm.feature_name) return;
    setLoading(true);
    setErr("");
    try {
      await postJson("/ml-feature-definitions", { use_case_id: selectedUseCase || null, ...catalogForm });
      setOk(`Feature ${catalogForm.feature_name} no catalogo.`);
      setCatalogForm({ feature_name: "", feature_group: "telemetry", source_table: "ml_features_daily" });
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
    } finally {
      setLoading(false);
    }
  };

  const onCreateDrift = async () => {
    if (!canMutate || !selectedUseCase) return;
    setLoading(true);
    setErr("");
    try {
      await postJson("/ml-drift-reports", {
        use_case_id: selectedUseCase,
        model_version: driftForm.model_version,
        psi_score: Number(driftForm.psi_score),
        status: driftForm.status,
      });
      setOk("Relatorio de drift registrado.");
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
    } finally {
      setLoading(false);
    }
  };

  const onUpsertSlo = async () => {
    if (!canMutate || !selectedUseCase) return;
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/ml-inference-slo`, {
        method: "PUT",
        headers,
        body: JSON.stringify({
          use_case_id: selectedUseCase,
          p95_latency_ms: Number(sloForm.p95_latency_ms),
          min_availability_pct: Number(sloForm.min_availability_pct),
        }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(parseError(j));
      setOk("SLO de inferencia salvo.");
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
    } finally {
      setLoading(false);
    }
  };

  const onCreateAlert = async () => {
    if (!canMutate || !selectedUseCase) return;
    setLoading(true);
    setErr("");
    try {
      await postJson("/ml-alert-rules", {
        use_case_id: selectedUseCase,
        ...alertForm,
        threshold: Number(alertForm.threshold),
      });
      setOk(`Alerta ${alertForm.rule_code} criado.`);
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
    } finally {
      setLoading(false);
    }
  };

  const onCreateGrant = async () => {
    if (!canMutate || !grantPartnerId || !selectedUseCase) return;
    setLoading(true);
    setErr("");
    try {
      await postJson("/ml-partner-use-case-grants", { partner_id: grantPartnerId, use_case_id: selectedUseCase });
      setOk("Grant parceiro ↔ caso de uso criado.");
      await load();
    } catch (e) {
      setErr(normalizeNetworkError(e, API));
    } finally {
      setLoading(false);
    }
  };

  const tableRows =
    tab === "use_cases"
      ? useCases.map((u) => ({
          key: u.id,
          tipo: "use_case",
          id: u.code,
          detalhe: `${u.name} · ${u.domain} · tier ${u.tier} · ${u.active ? "ativo" : "off"}`,
        }))
      : tab === "registry"
        ? registry.map((r) => ({
            key: r.id,
            tipo: "registry",
            id: r.model_version,
            detalhe: `${useCaseLabel(r.use_case_id)} · ${r.stage} · ${r.algorithm}`,
          }))
        : tab === "training"
          ? trainingRuns.map((t) => ({
              key: t.id,
              tipo: "run",
              id: t.run_name,
              detalhe: `${useCaseLabel(t.use_case_id)} · ${t.status} · ${t.model_version || "—"}`,
            }))
          : tab === "catalog"
            ? featureCatalog.map((c) => ({
                key: c.id,
                tipo: "def",
                id: c.feature_name,
                detalhe: `${c.feature_group} · ${c.source_table || "—"} · SLA ${c.freshness_hours}h`,
              }))
            : tab === "drift"
              ? driftReports.map((d) => ({
                  key: d.id,
                  tipo: d.drift_type,
                  id: d.model_version,
                  detalhe: `${useCaseLabel(d.use_case_id)} · PSI ${d.psi_score ?? "—"} · ${d.status}`,
                }))
              : tab === "governance"
                ? [
                    ...slos.map((s) => ({
                      key: `slo-${s.id}`,
                      tipo: "slo",
                      id: useCaseLabel(s.use_case_id),
                      detalhe: `p95 ${s.p95_latency_ms}ms · avail ${s.min_availability_pct}%`,
                    })),
                    ...alertRules.map((a) => ({
                      key: `al-${a.id}`,
                      tipo: "alert",
                      id: a.rule_code,
                      detalhe: `${a.metric} ${a.operator} ${a.threshold} · ${a.severity}`,
                    })),
                  ]
                : tab === "deployments"
                  ? deployments.map((d) => ({
                      key: d.id,
                      tipo: d.event_type,
                      id: d.to_version,
                      detalhe: `${useCaseLabel(d.use_case_id)} · from ${d.from_version || "—"} · ${d.created_at}`,
                    }))
                  : tab === "grants"
                    ? grants.map((g) => ({
                        key: `${g.partner_id}-${g.use_case_id}`,
                        tipo: "grant",
                        id: useCaseLabel(g.use_case_id),
                        detalhe: `partner ${g.partner_id.slice(0, 8)}… · ${g.scopes_json}`,
                      }))
                    : tab === "readiness"
                      ? mlReadiness.map((row) => ({
                          key: `mlrd-${row.id}`,
                          tipo: row.readiness_band,
                          id: row.network_player_code,
                          detalhe: `score ${row.score_total} · telemetria ${row.score_telemetry} · caps ${row.score_capabilities} · ops ${row.score_ml_ops}`,
                        }))
                      : tab === "networks"
                      ? [
                          ...networkPlayers.map((n) => ({
                            key: `net-${n.id}`,
                            tipo: n.parent_group,
                            id: n.code,
                            detalhe: `${n.name} · ${n.country} · ${n.global_tier || "—"} / ${n.integration_status || "—"} · ${n.player_role}`,
                          })),
                          ...playerCapabilities.map((c) => ({
                            key: `cap-${c.id}`,
                            tipo: "capability",
                            id: c.capability_code,
                            detalhe: `${c.network_player_code} · ${c.capability_name} · ${c.protocol}/${c.direction}${c.production_ready ? " · PROD" : ""}`,
                          })),
                          ...playerRelations.map((r) => ({
                            key: `rel-${r.id}`,
                            tipo: r.relation_type,
                            id: `${r.from_player_code} → ${r.to_player_code}`,
                            detalhe: `força ${r.strength}`,
                          })),
                          ...networkProfiles.map((pr) => ({
                            key: `prof-${pr.id}`,
                            tipo: "ml_profile",
                            id: pr.network_player_code || pr.network_player_id?.slice(0, 8),
                            detalhe: `${pr.use_case_code || "—"} · telemetria ${pr.telemetry_density} · PSI base ${pr.drift_baseline_psi ?? "—"} · pack ${(pr.feature_pack || []).join(", ")}`,
                          })),
                        ]
                      : tab === "partners"
      ? partners.map((p) => ({
          key: `p-${p.id}`,
          tipo: "partner",
          id: p.code,
          detalhe: `${p.name} · ${p.partner_type} · ${p.active ? "ativo" : "inativo"}${p.region_code ? ` · ${p.region_code}` : ""}${p.network_player_code ? ` · rede ${p.network_player_code}` : ""}`,
        }))
      : tab === "models"
        ? models.map((m) => ({
            key: `m-${m.id}`,
            tipo: "model",
            id: m.model_version,
            detalhe: `${m.status} · treinado ${m.trained_at || "—"}`,
          }))
        : tab === "features"
          ? features.map((f) => ({
              key: `f-${f.id}`,
              tipo: "feature",
              id: f.locker_id,
              detalhe: `${f.feature_date} · batt ${f.battery_min ?? "—"}% · portas 7d ${f.door_failures_7d ?? 0}`,
            }))
          : tab === "predictions"
            ? predictions.map((p) => ({
                key: `pr-${p.id}`,
                tipo: "prediction",
                id: p.locker_id,
                detalhe: `P(falha) ${formatPct(p.failure_probability)} · health ${formatHealth(p.health_score)} · ${p.model_version}`,
              }))
            : tab === "feedback"
              ? feedback.map((f) => ({
                  key: `fb-${f.id}`,
                  tipo: "feedback",
                  id: String(f.prediction_id ?? f.id),
                  detalhe: `erro ${f.error_pct ?? "—"}% · ${f.model_performance_status ?? "—"}`,
                }))
              : [];

  const listCount =
    tab === "use_cases"
      ? useCases.length
      : tab === "registry"
        ? registry.length
        : tab === "training"
          ? trainingRuns.length
          : tab === "catalog"
            ? featureCatalog.length
            : tab === "drift"
              ? driftReports.length
              : tab === "governance"
                ? slos.length + alertRules.length
                : tab === "deployments"
                  ? deployments.length
                  : tab === "grants"
                    ? grants.length
                    : tab === "readiness"
                      ? mlReadiness.length
                    : tab === "networks"
                      ? networkPlayers.length + networkProfiles.length + playerCapabilities.length + playerRelations.length
                    : tab === "partners"
                      ? partners.length
                      : tab === "models"
                        ? models.length
                        : tab === "features"
                          ? features.length
                          : tab === "predictions"
                            ? predictions.length
                            : tab === "feedback"
                              ? feedback.length
                              : 0;

  const listTitle =
    tab === "overview"
      ? "Indicadores (dashboard ML)"
      : tab === "use_cases"
        ? `Casos de uso (${useCases.length})`
        : tab === "registry"
          ? `Model registry (${registry.length})`
          : tab === "training"
            ? `Experimentos (${trainingRuns.length})`
            : tab === "catalog"
              ? `Catalogo de features (${featureCatalog.length})`
              : tab === "drift"
                ? `Relatorios de drift (${driftReports.length})`
                : tab === "governance"
                  ? `SLO (${slos.length}) e alertas (${alertRules.length})`
                  : tab === "deployments"
                    ? `Eventos de deploy (${deployments.length})`
                    : tab === "grants"
                      ? `Grants parceiro (${grants.length})`
                      : tab === "readiness"
                        ? `Prontidao ML (${mlReadiness.length}) · GO_LIVE ${mlReadinessHub?.bands?.GO_LIVE ?? "—"}`
                        : tab === "networks"
                          ? `Redes locker mundiais (${networkPlayers.length}) · perfis ML (${networkProfiles.length})`
                          : tab === "partners"
                            ? `Parceiros de dados (${partners.length})`
                            : tab === "models"
                            ? `Metadata (${models.length})`
                            : tab === "features"
                              ? `Features diarias (${features.length})`
                              : tab === "predictions"
                                ? `Log de predicoes (${predictions.length})`
                                : `Feedback de modelo (${feedback.length})`;

  return (
    <div style={pageStyle} data-testid="ops-ml-admin-page">
      <section style={cardStyle}>
        <div style={{ display: "flex", justifyContent: "flex-end", flexWrap: "wrap", marginBottom: 10, gap: 8 }}>
          <Link to="/ops/tenants/admin" style={crossShortcutLinkStyle}>
            Tenants
          </Link>
          <Link to="/ops/partners/admin" style={crossShortcutLinkStyle}>
            Parceiros
          </Link>
          <Link to="/ops/payment-gateway/admin" style={crossShortcutLinkStyle}>
            Payment Gateway
          </Link>
          <Link to="/ops/marketplace/admin" style={crossShortcutLinkStyle}>
            Marketplace
          </Link>
          <Link to="/intelligence/dashboard" style={crossShortcutLinkStyle}>
            Inteligencia
          </Link>
          <Link to="/intelligence/at-risk" style={crossShortcutLinkStyle}>
            Lockers em risco
          </Link>
        </div>

        <OpsPageTitleHeader
          title="OPS — ML (admin)"
          versionLabel={PAGE_VERSION}
          versionTo="/ops/auth/policy/versioning"
          containerStyle={{ marginBottom: 0 }}
          titleStyle={{ margin: 0 }}
        />
        <p style={mutedTextStyle}>
          Parceiros de ingestao, modelos, features, predicoes e feedback — tabelas{" "}
          <code style={{ color: "#e2e8f0" }}>ml_*</code> — API{" "}
          <code style={{ color: "#e2e8f0" }}>{API}</code> — role{" "}
          <code style={{ color: "#e2e8f0" }}>admin_operacao</code> para escrita.
        </p>

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
              Plataforma ML Ops: catalogo de casos de uso, model registry com promote, experimentos, drift PSI, SLO de inferencia e trilha de deployments.
            </p>
          ) : null}

          {["registry", "training", "catalog", "drift", "governance", "grants"].includes(tab) ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                use_case_id (foco)
                <select
                  value={selectedUseCase}
                  onChange={(e) => setSelectedUseCase(e.target.value)}
                  style={healthLocalFilterInputStyle}
                >
                  <option value="">— selecione —</option>
                  {useCases.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.code} — {u.tier}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          ) : null}

          {tab === "use_cases" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                code
                <input
                  value={useCaseForm.code}
                  onChange={(e) => setUseCaseForm((f) => ({ ...f, code: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                  placeholder="LOCKER_HEALTH"
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                name
                <input
                  value={useCaseForm.name}
                  onChange={(e) => setUseCaseForm((f) => ({ ...f, name: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                domain
                <select
                  value={useCaseForm.domain}
                  onChange={(e) => setUseCaseForm((f) => ({ ...f, domain: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                >
                  <option value="LOCKER">LOCKER</option>
                  <option value="PARTNER">PARTNER</option>
                  <option value="CUSTOMER">CUSTOMER</option>
                  <option value="LOGISTICS">LOGISTICS</option>
                  <option value="PRICING">PRICING</option>
                </select>
              </label>
              <label style={healthLocalFilterFieldStyle}>
                tier
                <select
                  value={useCaseForm.tier}
                  onChange={(e) => setUseCaseForm((f) => ({ ...f, tier: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                >
                  <option value="CRITICAL">CRITICAL</option>
                  <option value="STANDARD">STANDARD</option>
                  <option value="EXPERIMENTAL">EXPERIMENTAL</option>
                </select>
              </label>
            </div>
          ) : null}

          {tab === "registry" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                model_version
                <input
                  value={registryForm.model_version}
                  onChange={(e) => setRegistryForm((f) => ({ ...f, model_version: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                stage
                <select
                  value={registryForm.stage}
                  onChange={(e) => setRegistryForm((f) => ({ ...f, stage: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                >
                  <option value="DEV">DEV</option>
                  <option value="STAGING">STAGING</option>
                  <option value="PRODUCTION">PRODUCTION</option>
                </select>
              </label>
              <label style={healthLocalFilterFieldStyle}>
                promote entry_id
                <select
                  value={promoteRegistryId}
                  onChange={(e) => setPromoteRegistryId(e.target.value)}
                  style={healthLocalFilterInputStyle}
                >
                  <option value="">—</option>
                  {registry.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.model_version} ({r.stage})
                    </option>
                  ))}
                </select>
              </label>
            </div>
          ) : null}

          {tab === "training" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                run_name
                <input
                  value={trainingForm.run_name}
                  onChange={(e) => setTrainingForm((f) => ({ ...f, run_name: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                  placeholder="nightly-health-v2"
                />
              </label>
            </div>
          ) : null}

          {tab === "catalog" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                feature_name
                <input
                  value={catalogForm.feature_name}
                  onChange={(e) => setCatalogForm((f) => ({ ...f, feature_name: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                feature_group
                <input
                  value={catalogForm.feature_group}
                  onChange={(e) => setCatalogForm((f) => ({ ...f, feature_group: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
            </div>
          ) : null}

          {tab === "drift" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                model_version
                <input
                  value={driftForm.model_version}
                  onChange={(e) => setDriftForm((f) => ({ ...f, model_version: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                psi_score
                <input
                  value={driftForm.psi_score}
                  onChange={(e) => setDriftForm((f) => ({ ...f, psi_score: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                status
                <select
                  value={driftForm.status}
                  onChange={(e) => setDriftForm((f) => ({ ...f, status: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                >
                  <option value="OK">OK</option>
                  <option value="WARNING">WARNING</option>
                  <option value="CRITICAL">CRITICAL</option>
                </select>
              </label>
            </div>
          ) : null}

          {tab === "governance" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                p95_latency_ms
                <input
                  value={sloForm.p95_latency_ms}
                  onChange={(e) => setSloForm((f) => ({ ...f, p95_latency_ms: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                min_availability_pct
                <input
                  value={sloForm.min_availability_pct}
                  onChange={(e) => setSloForm((f) => ({ ...f, min_availability_pct: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                alert rule_code
                <input
                  value={alertForm.rule_code}
                  onChange={(e) => setAlertForm((f) => ({ ...f, rule_code: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                threshold
                <input
                  value={alertForm.threshold}
                  onChange={(e) => setAlertForm((f) => ({ ...f, threshold: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
            </div>
          ) : null}

          {tab === "grants" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                partner_id
                <select
                  value={grantPartnerId}
                  onChange={(e) => setGrantPartnerId(e.target.value)}
                  style={healthLocalFilterInputStyle}
                >
                  <option value="">—</option>
                  {partners.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.code}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          ) : null}

          {tab === "networks" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                <input
                  type="checkbox"
                  checked={networkPriorityOnly}
                  onChange={(e) => setNetworkPriorityOnly(e.target.checked)}
                />{" "}
                Somente redes prioritarias (InPost, DHL, Magalu, Mercado Livre, Amazon, DPD, Correios, CTT…)
              </label>
            </div>
          ) : null}

          {tab === "networks" ? (
            <p style={summary24hHintStyle}>
              Catalogo alinhado ao marketplace (channel_players). Seed sincroniza operadores locker, perfis ML por caso de
              uso e parceiros TELEMETRY-* por rede.
            </p>
          ) : null}

          {tab === "partners" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                name
                <input
                  value={partnerForm.name}
                  onChange={(e) => setPartnerForm((f) => ({ ...f, name: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                  placeholder="Telemetria Brasil"
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                code
                <input
                  value={partnerForm.code}
                  onChange={(e) => setPartnerForm((f) => ({ ...f, code: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                  placeholder="TELEMETRY-BR"
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                partner_type
                <select
                  value={partnerForm.partner_type}
                  onChange={(e) => setPartnerForm((f) => ({ ...f, partner_type: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                >
                  <option value="TELEMETRY">TELEMETRY</option>
                  <option value="SCORING">SCORING</option>
                  <option value="EXTERNAL">EXTERNAL</option>
                </select>
              </label>
            </div>
          ) : null}

          {tab === "models" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                model_version
                <input
                  value={modelForm.model_version}
                  onChange={(e) => setModelForm((f) => ({ ...f, model_version: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                  placeholder="rf-v2-prod"
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                status
                <select
                  value={modelForm.status}
                  onChange={(e) => setModelForm((f) => ({ ...f, status: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                >
                  <option value="ACTIVE">ACTIVE</option>
                  <option value="STALE">STALE</option>
                  <option value="FAILED">FAILED</option>
                </select>
              </label>
            </div>
          ) : null}

          {tab === "features" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                locker_id (filtro listagem)
                <input
                  value={featureLockerFilter}
                  onChange={(e) => setFeatureLockerFilter(e.target.value)}
                  style={healthLocalFilterInputStyle}
                  placeholder="opcional"
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                locker_id (nova feature)
                <input
                  value={featureForm.locker_id}
                  onChange={(e) => setFeatureForm((f) => ({ ...f, locker_id: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                feature_date
                <input
                  type="date"
                  value={featureForm.feature_date}
                  onChange={(e) => setFeatureForm((f) => ({ ...f, feature_date: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                battery_min
                <input
                  value={featureForm.battery_min}
                  onChange={(e) => setFeatureForm((f) => ({ ...f, battery_min: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                  placeholder="78"
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                door_failures_7d
                <input
                  value={featureForm.door_failures_7d}
                  onChange={(e) => setFeatureForm((f) => ({ ...f, door_failures_7d: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
            </div>
          ) : null}

          {tab === "predictions" ? (
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                locker_id (filtro)
                <input
                  value={predLockerFilter}
                  onChange={(e) => setPredLockerFilter(e.target.value)}
                  style={healthLocalFilterInputStyle}
                  placeholder="opcional"
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                locker_id (nova predicao)
                <input
                  value={predForm.locker_id}
                  onChange={(e) => setPredForm((f) => ({ ...f, locker_id: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                failure_probability
                <input
                  value={predForm.failure_probability}
                  onChange={(e) => setPredForm((f) => ({ ...f, failure_probability: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                  placeholder="0.0–1.0"
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                health_score
                <input
                  value={predForm.health_score}
                  onChange={(e) => setPredForm((f) => ({ ...f, health_score: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                />
              </label>
              <label style={healthLocalFilterFieldStyle}>
                model_version
                <input
                  value={predForm.model_version}
                  onChange={(e) => setPredForm((f) => ({ ...f, model_version: e.target.value }))}
                  style={healthLocalFilterInputStyle}
                  placeholder={activeModelVersion(models) || "rf-v1-demo"}
                />
              </label>
            </div>
          ) : null}

          {tab === "feedback" ? (
            <p style={summary24hHintStyle}>
              Feedback compara predicao vs. resultado real (funcao validate_ml_predictions). Use Validar feedback para
              gerar registros de predições com mais de 7 dias.
            </p>
          ) : null}

          {tab === "networks" && networkPlayers.length === 0 ? (
            <p style={summary24hHintStyle}>Nenhuma rede locker. Use Seed redes ou Seed completo (admin_operacao).</p>
          ) : null}

          {tab === "partners" && partners.length === 0 ? (
            <p style={summary24hHintStyle}>Nenhum parceiro ML. Use Listar ou Seed (admin_operacao).</p>
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
                {tab === "networks" ? (
                  <button type="button" style={buttonPrimaryStyle} onClick={() => void onSeedNetworks()} disabled={loading}>
                    Seed redes locker
                  </button>
                ) : null}
                {tab === "use_cases" ? (
                  <button
                    type="button"
                    style={buttonPrimaryStyle}
                    onClick={() => void onCreateUseCase()}
                    disabled={loading || !useCaseForm.code || !useCaseForm.name}
                  >
                    Criar caso de uso
                  </button>
                ) : null}
                {tab === "registry" ? (
                  <>
                    <button
                      type="button"
                      style={buttonPrimaryStyle}
                      onClick={() => void onCreateRegistry()}
                      disabled={loading || !selectedUseCase || !registryForm.model_version}
                    >
                      Registrar modelo
                    </button>
                    <button
                      type="button"
                      style={buttonGhostStyle}
                      onClick={() => void onPromoteRegistry()}
                      disabled={loading || !promoteRegistryId}
                    >
                      Promover PRODUCTION
                    </button>
                  </>
                ) : null}
                {tab === "training" ? (
                  <button
                    type="button"
                    style={buttonPrimaryStyle}
                    onClick={() => void onCreateTraining()}
                    disabled={loading || !selectedUseCase || !trainingForm.run_name}
                  >
                    Novo experimento
                  </button>
                ) : null}
                {tab === "catalog" ? (
                  <button
                    type="button"
                    style={buttonPrimaryStyle}
                    onClick={() => void onCreateCatalogFeature()}
                    disabled={loading || !catalogForm.feature_name}
                  >
                    Catalogar feature
                  </button>
                ) : null}
                {tab === "drift" ? (
                  <button
                    type="button"
                    style={buttonPrimaryStyle}
                    onClick={() => void onCreateDrift()}
                    disabled={loading || !selectedUseCase}
                  >
                    Registrar drift
                  </button>
                ) : null}
                {tab === "governance" ? (
                  <>
                    <button
                      type="button"
                      style={buttonGhostStyle}
                      onClick={() => void onUpsertSlo()}
                      disabled={loading || !selectedUseCase}
                    >
                      Salvar SLO
                    </button>
                    <button
                      type="button"
                      style={buttonPrimaryStyle}
                      onClick={() => void onCreateAlert()}
                      disabled={loading || !selectedUseCase}
                    >
                      Criar alerta
                    </button>
                  </>
                ) : null}
                {tab === "grants" ? (
                  <button
                    type="button"
                    style={buttonPrimaryStyle}
                    onClick={() => void onCreateGrant()}
                    disabled={loading || !grantPartnerId || !selectedUseCase}
                  >
                    Conceder acesso
                  </button>
                ) : null}
                {tab === "partners" ? (
                  <button
                    type="button"
                    style={buttonPrimaryStyle}
                    onClick={() => void onCreatePartner()}
                    disabled={loading || !partnerForm.name || !partnerForm.code}
                  >
                    Criar parceiro
                  </button>
                ) : null}
                {tab === "models" ? (
                  <button
                    type="button"
                    style={buttonPrimaryStyle}
                    onClick={() => void onCreateModel()}
                    disabled={loading || !modelForm.model_version}
                  >
                    Registrar modelo
                  </button>
                ) : null}
                {tab === "features" ? (
                  <button
                    type="button"
                    style={buttonPrimaryStyle}
                    onClick={() => void onCreateFeature()}
                    disabled={loading || !featureForm.locker_id || !featureForm.feature_date}
                  >
                    Inserir feature
                  </button>
                ) : null}
                {tab === "predictions" ? (
                  <button
                    type="button"
                    style={buttonPrimaryStyle}
                    onClick={() => void onCreatePrediction()}
                    disabled={loading || !predForm.locker_id || !predForm.model_version}
                  >
                    Registrar predicao
                  </button>
                ) : null}
                {tab === "feedback" ? (
                  <button type="button" style={buttonGhostStyle} onClick={() => void onValidate()} disabled={loading}>
                    Validar feedback
                  </button>
                ) : null}
              </>
            ) : null}
          </div>
        </section>

        {tab === "partners" ? (
          <section style={opsSanityCardStyle}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 14 }}>Webhook e API key (parceiro ML)</h3>
            </div>
            <div style={healthLocalFilterRowStyle}>
              <label style={healthLocalFilterFieldStyle}>
                partner_id
                <select
                  value={selectedPartner}
                  onChange={(e) => setSelectedPartner(e.target.value)}
                  style={healthLocalFilterInputStyle}
                >
                  <option value="">— selecione —</option>
                  {partners.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.code}
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
                disabled={!canMutate || !selectedPartner || !webhookUrl}
              >
                Salvar webhook
              </button>
              <button type="button" style={buttonGhostStyle} onClick={() => void onRotateKey()} disabled={!canMutate || !selectedPartner}>
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

        {tab === "overview" && dash ? (
          <section style={opsSanityCardStyle}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 14 }}>{listTitle}</h3>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 12 }}>
              {[
                ["Casos de uso", dash.use_cases],
                ["Modelos em PROD", dash.registry_production],
                ["Modelos ativos (metadata)", dash.active_models],
                ["Predicoes (24h)", dash.predictions_24h],
                ["Drift CRITICAL", dash.drift_critical],
                ["Features catalogadas", dash.feature_definitions],
                ["Experimentos RUNNING", dash.training_running],
                ["Alertas ativos", dash.alert_rules],
                ["Deploys (7d)", dash.deployments_7d],
                ["Linhas features diarias", dash.features_rows],
                ["Feedback", dash.feedback_rows],
                ["Parceiros ML", dash.partners],
                ["Redes locker (catálogo)", dash.locker_network_players],
                ["Redes prioritarias", dash.locker_network_priority],
                ["Perfis ML por rede", dash.network_ml_profiles],
                ["Capacidades integração", dash.player_capabilities],
                ["Relações ecossistema", dash.player_relations],
                ["Players TIER1", dash.tier1_players],
                ["Prontidao ML (redes)", dash.ml_readiness_rows],
                ["ML GO_LIVE", dash.ml_readiness_go_live],
              ].map(([label, value]) => (
                <div key={label} style={{ padding: 10, borderRadius: 8, border: "1px solid rgba(148,163,184,0.25)" }}>
                  <p style={{ margin: 0, fontSize: 11, opacity: 0.75 }}>{label}</p>
                  <p style={{ margin: "4px 0 0", fontSize: 18, fontWeight: 600 }}>{value}</p>
                </div>
              ))}
            </div>
            <p style={{ ...summary24hHintStyle, marginTop: 12 }}>
              Atalhos:{" "}
              <button type="button" style={{ ...buttonGhostStyle, padding: "4px 8px", fontSize: 11 }} onClick={() => setTabAndUrl("networks")}>
                Redes locker
              </button>{" "}
              <button type="button" style={{ ...buttonGhostStyle, padding: "4px 8px", fontSize: 11 }} onClick={() => setTabAndUrl("partners")}>
                Parceiros
              </button>{" "}
              <button type="button" style={{ ...buttonGhostStyle, padding: "4px 8px", fontSize: 11 }} onClick={() => setTabAndUrl("models")}>
                Modelos
              </button>{" "}
              <button type="button" style={{ ...buttonGhostStyle, padding: "4px 8px", fontSize: 11 }} onClick={() => setTabAndUrl("predictions")}>
                Predicoes
              </button>
            </p>
          </section>
        ) : null}

        {tab !== "overview" && listCount > 0 ? (
          <section style={opsSanityCardStyle}>
            <div style={summary24hHeaderStyle}>
              <h3 style={{ margin: 0, fontSize: 14 }}>{listTitle}</h3>
            </div>
            <div style={{ overflowX: "auto" }}>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    {["tipo", "id / versao", "detalhe"].map((h) => (
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
        ) : null}

        {tab !== "overview" && token && listCount === 0 && !loading ? (
          <p style={summary24hHintStyle}>Nenhum registro nesta aba. Use Listar ou Seed (admin_operacao).</p>
        ) : null}

        {tab === "overview" && token && !dash && !loading ? (
          <p style={summary24hHintStyle}>Clique em Listar para carregar o dashboard ML.</p>
        ) : null}
      </section>
    </div>
  );
}
