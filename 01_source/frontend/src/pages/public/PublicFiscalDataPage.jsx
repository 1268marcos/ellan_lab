import React, { useMemo } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";
import FiscalProfileForm from "../../components/public/FiscalProfileForm";
import { PageHeader } from "./myAreaSharedComponents";
import {
  pageStyle,
  containerStyle,
  pageHeaderStyle,
  titleStyle,
  subtitleStyle,
  newOrderButtonStyle,
} from "./myAreaSharedStyles";
import { elevatedCardBaseStyle } from "./myAreaSharedCardStyles";
import { resolvePersonalGreeting } from "./myAreaDisplayName";

export default function PublicFiscalDataPage() {
  const { token, user, refreshUser } = useAuth();
  const greeting = resolvePersonalGreeting(user);

  const defaultCountry = useMemo(() => {
    const t = String(user?.tax_country || "").trim().toUpperCase();
    if (t === "PT") return "PT";
    return "BR";
  }, [user?.tax_country]);

  return (
    <main style={pageStyle}>
      <div style={containerStyle}>
        <PageHeader
          title="Dados fiscais"
          subtitle={`${greeting}Gerencie os dados fiscais usados nos seus pedidos.`}
          ctaTo="/comprar"
          ctaLabel="✨ Novo Pedido"
          headerStyle={pageHeaderStyle}
          titleStyle={titleStyle}
          subtitleStyle={subtitleStyle}
          ctaStyle={newOrderButtonStyle}
        />
        <p style={descriptionStyle}>
          Estes dados alimentam o contexto fiscal dos seus pedidos (nome, documento, morada e contacto da nota).
          Após guardar, atualizamos automaticamente as invoices pendentes no serviço de faturação, quando configurado.
        </p>
        <p style={securityLinkWrapStyle}>
          <Link to="/seguranca" style={{ color: "#0f766e", textDecoration: "none", fontWeight: 600 }}>
            ← Conta / Segurança
          </Link>
        </p>

      {token && user ? (
        <div style={fiscalFormWrapStyle}>
          <section
            style={{
              ...elevatedCardBaseStyle,
              padding: 20,
              borderLeft: "5px solid #0ea5e9",
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
        </div>
      ) : (
        <p>Inicie sessão para gerir os dados fiscais.</p>
      )}
      </div>
    </main>
  );
}

const fiscalFormWrapStyle = {
  maxWidth: 720,
};

const descriptionStyle = {
  margin: "0 0 8px 0",
  color: "#475569",
  lineHeight: 1.5,
  maxWidth: 720,
};

const securityLinkWrapStyle = {
  margin: "0 0 16px 0",
};
