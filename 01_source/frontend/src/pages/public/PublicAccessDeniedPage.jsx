import React from "react";
import { Link } from "react-router-dom";

export default function PublicAccessDeniedPage() {
  return (
    <main style={{ maxWidth: 760, margin: "0 auto", padding: 24 }}>
      <section
        style={{
          border: "1px solid #fecaca",
          borderRadius: 12,
          background: "#fff1f2",
          color: "#7f1d1d",
          padding: 18,
        }}
      >
        <h1 style={{ marginTop: 0 }}>Acesso negado</h1>
        <p>
          Seu usuário não possui a role necessária para acessar esta área operacional.
        </p>
        <p style={{ marginBottom: 0 }}>
          Se você precisa desse acesso, solicite a liberação de role para um administrador.
        </p>
      </section>

      <div style={{ marginTop: 14, display: "flex", gap: 12, flexWrap: "wrap" }}>
        <Link to="/">Voltar para início</Link>
        <Link to="/meus-pedidos">Ir para meus pedidos</Link>
      </div>
    </main>
  );
}
