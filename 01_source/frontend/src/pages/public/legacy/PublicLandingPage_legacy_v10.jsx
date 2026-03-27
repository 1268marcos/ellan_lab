// 01_source/frontend/src/pages/public/PublicLandingPage.jsx
import React from "react";
import { Link } from "react-router-dom";

export default function PublicLandingPage() {
  return (
    <main style={pageStyle}>
      <div style={containerStyle}>
        <section style={heroCardStyle}>
          <div style={heroContentStyle}>
            <span style={eyebrowStyle}>Canal público oficial</span>

            <h1 style={titleStyle}>ELLAN Lab Locker</h1>

            <p style={subtitleStyle}>
              Compre online, acompanhe seus pedidos e consulte as informações
              de retirada de forma simples e organizada.
            </p>

            <div style={actionsStyle}>
              <Link to="/comprar" style={primaryActionStyle}>
                Comprar agora
              </Link>

              <Link to="/login" style={secondaryActionStyle}>
                Entrar
              </Link>

              <Link to="/cadastro" style={secondaryActionStyle}>
                Criar conta
              </Link>
            </div>
          </div>
        </section>

        <section style={gridStyle}>
          <article style={infoCardStyle}>
            <h2 style={cardTitleStyle}>Comprar online2</h2>
            <p style={cardTextStyle}>
              Escolha o produto, siga o fluxo de checkout e acompanhe o pedido
              na sua área logada.
            </p>
          </article>

          <article style={infoCardStyle}>
            <h2 style={cardTitleStyle}>Acompanhar pedidos</h2>
            <p style={cardTextStyle}>
              Veja o status do pedido, detalhes da compra e informações
              relacionadas à retirada.
            </p>
          </article>

          <article style={infoCardStyle}>
            <h2 style={cardTitleStyle}>Retirada no kiosk/totem</h2>
            <p style={cardTextStyle}>
              Quando disponível, os dados de retirada ficam visíveis no detalhe
              do pedido para uso no locker.
            </p>
          </article>
        </section>
      </div>
    </main>
  );
}

const pageStyle = {
  padding: 24,
};

const containerStyle = {
  maxWidth: 1040,
  margin: "0 auto",
};

const heroCardStyle = {
  borderRadius: 20,
  padding: 28,
  marginBottom: 20,
  border: "1px solid #e5e7eb",
  background: "rgba(255,255,255,0.06)",
};

const heroContentStyle = {
  maxWidth: 720,
};

const eyebrowStyle = {
  display: "inline-block",
  marginBottom: 10,
  fontSize: 12,
  fontWeight: 700,
  letterSpacing: "0.08em",
  textTransform: "uppercase",
  color: "#666",
};

const titleStyle = {
  margin: 0,
  fontSize: 36,
  lineHeight: 1.1,
};

const subtitleStyle = {
  marginTop: 14,
  marginBottom: 0,
  fontSize: 16,
  lineHeight: 1.6,
  color: "#555",
  maxWidth: 640,
};

const actionsStyle = {
  display: "flex",
  flexWrap: "wrap",
  gap: 12,
  marginTop: 22,
};

const primaryActionStyle = {
  textDecoration: "none",
  padding: "12px 16px",
  borderRadius: 12,
  border: "1px solid #111827",
  background: "#111827",
  color: "white",
  fontWeight: 700,
};

const secondaryActionStyle = {
  textDecoration: "none",
  padding: "12px 16px",
  borderRadius: 12,
  border: "1px solid #d1d5db",
  background: "#f9fafb",
  color: "#111827",
  fontWeight: 700,
};

const gridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  gap: 14,
};

const infoCardStyle = {
  borderRadius: 16,
  padding: 18,
  border: "1px solid #e5e7eb",
  background: "rgba(255,255,255,0.06)",
};

const cardTitleStyle = {
  marginTop: 0,
  marginBottom: 10,
  fontSize: 18,
};

const cardTextStyle = {
  margin: 0,
  color: "#666",
  lineHeight: 1.6,
};