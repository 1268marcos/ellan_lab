
// Checkout: aviso + formulário fiscal reutilizável
// Estilos: `publicCheckoutChrome.css` (prefixo `public-checkout-chrome__fiscal-*`), carregado em `PublicCheckoutPage`.

import React from "react";
import { Link } from "react-router-dom";
import FiscalProfileForm from "./FiscalProfileForm";

export default function FiscalProfileCheckoutPanel({ token, user, fiscalCountry, onSaved }) {
  const pct = Number(user?.fiscal_profile_completeness ?? 0);

  return (
    <div className="public-checkout-chrome__fiscal-panel" data-testid="public-checkout-fiscal-panel">
      <h3 className="public-checkout-chrome__fiscal-panel-title">Nota fiscal — dados do destinatário</h3>
      <div className="public-checkout-chrome__fiscal-panel-notice">
        <strong>Completude: {pct}%</strong>
        <p className="public-checkout-chrome__fiscal-panel-notice-text">
          Para emissão com provedor fiscal real, o perfil deve estar completo. Pode também preencher em{" "}
          <Link to="/conta/dados-fiscais" className="public-checkout-chrome__fiscal-panel-link">
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

