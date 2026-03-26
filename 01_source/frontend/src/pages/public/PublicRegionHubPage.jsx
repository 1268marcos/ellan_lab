// 01_source/frontend/src/pages/public/PublicRegionHubPage.jsx
import React from "react";
import { Link } from "react-router-dom";

const REGION_META = {
  SP: {
    title: "ELLAN LAB SP",
    subtitle: "Compre online e retire no locker em São Paulo.",
    accent: "linear-gradient(135deg, rgba(0,155,58,0.92), rgba(254,221,0,0.92), rgba(0,39,118,0.92))",
    regionName: "São Paulo",
  },
  PT: {
    title: "ELLAN LAB PT",
    subtitle: "Compre online e retire no cacifo em Portugal.",
    accent: "linear-gradient(135deg, rgba(0,102,0,0.92), rgba(206,17,38,0.92))",
    regionName: "Portugal",
  },
};

export default function PublicRegionHubPage({ region = "SP" }) {
  const meta = REGION_META[region] || REGION_META.SP;

  return (
    <main style={pageStyle}>
      <section style={{ ...heroStyle, background: meta.accent }}>
        <div style={heroInnerStyle}>
          <div>
            <div style={eyebrowStyle}>Região {region}</div>
            <h1 style={titleStyle}>{meta.title}</h1>
            <p style={subtitleStyle}>{meta.subtitle}</p>
          </div>

          <div style={heroActionsStyle}>
            <Link to={`/comprar?region=${region}`} style={primaryButtonStyle}>
              Comprar agora
            </Link>

            <Link to="/login" style={secondaryButtonStyle}>
              Entrar
            </Link>

            <Link to="/cadastro" style={secondaryButtonStyle}>
              Criar conta
            </Link>
          </div>
        </div>
      </section>

      <section style={gridStyle}>
        <article style={cardStyle}>
          <h2 style={cardTitleStyle}>Como funciona</h2>
          <ol style={listStyle}>
            <li>Escolha o produto disponível para {meta.regionName}.</li>
            <li>Conclua a reserva e o pagamento online.</li>
            <li>Receba os dados de retirada na sua conta e por email.</li>
            <li>Vá ao locker/cacifo e retire com QR Code ou código manual.</li>
          </ol>
        </article>

        <article style={cardStyle}>
          <h2 style={cardTitleStyle}>Acessos rápidos</h2>
          <div style={actionsColumnStyle}>
            <Link to={`/comprar?region=${region}`} style={cardActionStyle}>
              Ver catálogo da região
            </Link>
            <Link to="/meus-pedidos" style={cardActionStyle}>
              Meus pedidos
            </Link>
            <Link to="/comprovante" style={cardActionStyle}>
              Consultar comprovante
            </Link>
          </div>
        </article>

        <article style={cardStyle}>
          <h2 style={cardTitleStyle}>Importante</h2>
          <p style={bodyTextStyle}>
            O dashboard operacional não faz parte da jornada do comprador final.
            Nesta área pública, o foco é compra, pagamento e retirada.
          </p>
        </article>
      </section>
    </main>
  );
}

const pageStyle = {
  padding: 24,
  display: "grid",
  gap: 20,
};

const heroStyle = {
  borderRadius: 20,
  padding: 24,
  color: "white",
  border: "1px solid rgba(255,255,255,0.14)",
  boxShadow: "0 10px 30px rgba(0,0,0,0.18)",
};

const heroInnerStyle = {
  display: "grid",
  gap: 20,
};

const eyebrowStyle = {
  fontSize: 12,
  fontWeight: 800,
  letterSpacing: 1,
  opacity: 0.92,
  textTransform: "uppercase",
};

const titleStyle = {
  margin: "8px 0 10px 0",
  fontSize: 34,
  lineHeight: 1.1,
};

const subtitleStyle = {
  margin: 0,
  maxWidth: 700,
  fontSize: 16,
  lineHeight: 1.5,
  opacity: 0.95,
};

const heroActionsStyle = {
  display: "flex",
  gap: 12,
  flexWrap: "wrap",
};

const primaryButtonStyle = {
  textDecoration: "none",
  padding: "12px 16px",
  borderRadius: 12,
  background: "rgba(255,255,255,0.16)",
  color: "white",
  border: "1px solid rgba(255,255,255,0.24)",
  fontWeight: 700,
};

const secondaryButtonStyle = {
  textDecoration: "none",
  padding: "12px 16px",
  borderRadius: 12,
  background: "rgba(0,0,0,0.12)",
  color: "white",
  border: "1px solid rgba(255,255,255,0.18)",
  fontWeight: 700,
};

const gridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
  gap: 16,
};

const cardStyle = {
  padding: 18,
  borderRadius: 16,
  border: "1px solid #e5e7eb",
  background: "rgba(255,255,255,0.7)",
};

const cardTitleStyle = {
  marginTop: 0,
  marginBottom: 12,
  fontSize: 20,
};

const bodyTextStyle = {
  margin: 0,
  lineHeight: 1.55,
  color: "#4b5563",
};

const listStyle = {
  margin: 0,
  paddingLeft: 18,
  color: "#374151",
  lineHeight: 1.65,
};

const actionsColumnStyle = {
  display: "grid",
  gap: 10,
};

const cardActionStyle = {
  textDecoration: "none",
  padding: "12px 14px",
  borderRadius: 12,
  border: "1px solid #d1d5db",
  background: "#f9fafb",
  color: "#111827",
  fontWeight: 700,
};