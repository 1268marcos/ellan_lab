import React from "react";
import { Link } from "react-router-dom";

export default function PublicCheckoutPage() {
  return (
    <main style={pageStyle}>
      <div style={containerStyle}>
        <section style={heroCardStyle}>
          <span style={eyebrowStyle}>Checkout público</span>

          <h1 style={titleStyle}>Checkout</h1>

          <p style={subtitleStyle}>
            A etapa pública de checkout ainda está em evolução. Esta tela
            permanece temporária enquanto o fluxo oficial de compra online é
            concluído com catálogo real, pagamento e geração de retirada.
          </p>

          <div style={actionsStyle}>
            <Link to="/" style={secondaryActionStyle}>
              Voltar ao início
            </Link>

            <Link to="/comprar" style={secondaryActionStyle}>
              Ir para catálogo
            </Link>

            <Link to="/login" style={primaryActionStyle}>
              Entrar
            </Link>
          </div>
        </section>

        <section style={gridStyle}>
          <article style={infoCardStyle}>
            <h2 style={cardTitleStyle}>Situação atual</h2>
            <p style={cardTextStyle}>
              Esta tela ainda não executa o checkout completo do canal público.
            </p>
          </article>

          <article style={infoCardStyle}>
            <h2 style={cardTitleStyle}>O que falta integrar</h2>
            <p style={cardTextStyle}>
              Seleção final de produto, confirmação do pedido, pagamento e
              disponibilização dos dados de retirada.
            </p>
          </article>

          <article style={infoCardStyle}>
            <h2 style={cardTitleStyle}>Próxima evolução</h2>
            <p style={cardTextStyle}>
              A próxima etapa desta área é conectar o checkout ao catálogo real
              e ao fluxo público de autenticação e pedidos.
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
  fontSize: 34,
  lineHeight: 1.1,
};

const subtitleStyle = {
  marginTop: 14,
  marginBottom: 0,
  fontSize: 16,
  lineHeight: 1.6,
  color: "#555",
  maxWidth: 700,
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