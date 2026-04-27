import React from "react";
import { Link } from "react-router-dom";

import AuthorizationPolicyPanel from "../components/AuthorizationPolicyPanel";
import { fetchPublicAuthorizationPolicy } from "../services/authApi";

export default function OpsAuthorizationPolicyPage() {
  const [title, setTitle] = React.useState("Política de autorização (fonte única)");
  const [markdown, setMarkdown] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");

  React.useEffect(() => {
    let active = true;

    async function loadPolicy() {
      setLoading(true);
      setError("");
      try {
        const data = await fetchPublicAuthorizationPolicy();
        if (!active) return;
        setTitle(String(data?.title || "Política de autorização (fonte única)"));
        setMarkdown(String(data?.markdown || ""));
      } catch (err) {
        if (!active) return;
        setError(err?.message || "Falha ao carregar política de autorização.");
      } finally {
        if (active) setLoading(false);
      }
    }

    loadPolicy();
    return () => {
      active = false;
    };
  }, []);

  return (
    <main style={{ maxWidth: 980, margin: "0 auto", padding: 24 }}>
      <header style={{ marginBottom: 14 }}>
        <h1 style={{ margin: 0 }}>OPS — Política de autorização</h1>
        <p style={{ marginTop: 8, color: "#475569" }}>
          Referência operacional única de permissões e regras de acesso.
        </p>
      </header>

      <AuthorizationPolicyPanel
        title={title}
        markdown={markdown}
        loading={loading}
        error={error}
      />

      <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
        <Link to="/ops/sp">Voltar ao dashboard OPS SP</Link>
        <Link to="/ops/pt">Ir para dashboard OPS PT</Link>
        <Link to="/ops/auth/policy/versioning">Política de versionamento (ops/health)</Link>
        <Link to="/ops/updates">Registro de atualizações OPS</Link>
        <a href="/docs/ellan_lab_sprint_board.html">Board visual de sprint (ELLAN LAB)</a>
      </div>
    </main>
  );
}
