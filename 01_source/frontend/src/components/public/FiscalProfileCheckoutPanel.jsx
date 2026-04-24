// Checkout: aviso + formulário fiscal reutilizável

import React from "react";
import { Link } from "react-router-dom";
import FiscalProfileForm from "./FiscalProfileForm";

const noticeStyle = {
  background: "#f8fafc",
  border: "1px solid #e2e8f0",
  borderRadius: 10,
  padding: 12,
  marginBottom: 14,
  fontSize: 13,
  color: "#334155",
};

export default function FiscalProfileCheckoutPanel({ token, user, fiscalCountry, onSaved }) {
  const pct = Number(user?.fiscal_profile_completeness ?? 0);

  return (
    <div style={{ marginTop: 16, marginBottom: 8 }}>
      <h3 style={{ margin: "0 0 8px 0", fontSize: 16, color: "#0f172a" }}>Nota fiscal — dados do destinatário</h3>
      <div style={noticeStyle}>
        <strong>Completude: {pct}%</strong>
        <p style={{ margin: "8px 0 0 0" }}>
          Para emissão com provedor fiscal real, o perfil deve estar completo.           Pode também preencher em{" "}
          <Link to="/conta/dados-fiscais" style={{ color: "#0f766e" }}>
            Conta → Dados fiscais
          </Link>
          .
        </p>
      </div>
      <FiscalProfileForm
        token={token}
        user={user}
        defaultFiscalCountry={fiscalCountry}
        onSaved={onSaved}
        variant="checkout"
      />
    </div>
  );
}
