import React, { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";
import { confirmPublicEmailVerification } from "../../services/authApi";

export default function PublicEmailVerificationPage() {
  const [params] = useSearchParams();
  const { refreshUser } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const token = useMemo(() => params.get("token") || "", [params]);

  useEffect(() => {
    let active = true;

    async function run() {
      if (!token) {
        if (!active) return;
        setError("Link inválido: token ausente.");
        setLoading(false);
        return;
      }

      try {
        const data = await confirmPublicEmailVerification(token);
        if (!active) return;
        setMessage(data?.message === "email_verified" ? "E-mail verificado com sucesso." : "E-mail confirmado.");
        setError("");
        await refreshUser();
      } catch (err) {
        if (!active) return;
        setError(err?.message || "Não foi possível confirmar o e-mail.");
      } finally {
        if (active) setLoading(false);
      }
    }

    run();
    return () => {
      active = false;
    };
  }, [refreshUser, token]);

  return (
    <main style={{ maxWidth: 760, margin: "0 auto", padding: 24 }}>
      <section
        style={{
          border: "1px solid #e2e8f0",
          borderRadius: 12,
          background: "#fff",
          padding: 18,
        }}
      >
        <h1 style={{ marginTop: 0 }}>Verificação de e-mail</h1>

        {loading ? <p>Confirmando seu e-mail...</p> : null}
        {!loading && message ? <p style={{ color: "#166534" }}>{message}</p> : null}
        {!loading && error ? <p style={{ color: "#b91c1c" }}>{error}</p> : null}

        <div style={{ marginTop: 12, display: "flex", gap: 12, flexWrap: "wrap" }}>
          <Link to="/seguranca">Ir para Segurança</Link>
          <Link to="/meus-pedidos">Ir para Meus pedidos</Link>
        </div>
      </section>
    </main>
  );
}
