import React, { useMemo } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";
import FiscalProfileForm from "../../components/public/FiscalProfileForm";

export default function PublicFiscalDataPage() {
  const { token, user, refreshUser } = useAuth();

  const defaultCountry = useMemo(() => {
    const t = String(user?.tax_country || "").trim().toUpperCase();
    if (t === "PT") return "PT";
    return "BR";
  }, [user?.tax_country]);

  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: 24 }}>
      <header style={{ marginBottom: 20 }}>
        <p style={{ margin: "0 0 8px 0" }}>
          <Link to="/seguranca" style={{ color: "#0f766e", textDecoration: "none" }}>
            ← Conta / Segurança
          </Link>
        </p>
        <h1 style={{ margin: 0 }}>Dados fiscais</h1>
        <p style={{ marginTop: 8, color: "#475569" }}>
          Estes dados alimentam o contexto fiscal dos seus pedidos (nome, documento, morada e contacto da nota).
          Após guardar, atualizamos automaticamente as invoices pendentes no serviço de faturação, quando
          configurado.
        </p>
      </header>

      {token && user ? (
        <section
          style={{
            border: "1px solid #e2e8f0",
            borderRadius: 12,
            padding: 20,
            background: "#fff",
          }}
        >
          <FiscalProfileForm
            token={token}
            user={user}
            defaultFiscalCountry={defaultCountry}
            onSaved={refreshUser}
            variant="account"
          />
        </section>
      ) : (
        <p>Inicie sessão para gerir os dados fiscais.</p>
      )}
    </main>
  );
}
