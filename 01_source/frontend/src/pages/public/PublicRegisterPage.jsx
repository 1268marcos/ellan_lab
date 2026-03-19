import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import RegisterForm from "../../components/public/RegisterForm";
import { useAuth } from "../../context/AuthContext";

export default function PublicRegisterPage() {
  const { register, isAuthenticated, loading: authLoading } = useAuth();
  const navigate = useNavigate();

  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      navigate("/meus-pedidos", { replace: true });
    }
  }, [authLoading, isAuthenticated, navigate]);

  async function handleRegister(payload) {
    if (submitting) {
      return;
    }

    setError("");
    setSubmitting(true);

    try {
      await register(payload);
      navigate("/meus-pedidos", { replace: true });
    } catch (err) {
      setError(err?.message || "Falha ao criar conta.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main style={pageStyle}>
      <div style={containerStyle}>
        <section style={cardStyle}>
          <div style={headerStyle}>
            <h1 style={titleStyle}>Criar conta</h1>
            <p style={subtitleStyle}>
              Cadastre-se para acompanhar seus pedidos e receber as informações de retirada.
            </p>
          </div>

          {error ? (
            <div style={errorBoxStyle}>
              <strong>Não foi possível concluir o cadastro.</strong>
              <p style={errorTextStyle}>{error}</p>
            </div>
          ) : null}

          <RegisterForm onSubmit={handleRegister} loading={submitting || authLoading} />

          <div style={footerStyle}>
            <span style={footerTextStyle}>Já tem conta?</span>
            <Link to="/login" style={footerLinkStyle}>
              Entrar
            </Link>
          </div>
        </section>
      </div>
    </main>
  );
}

const pageStyle = {
  padding: 24,
};

const containerStyle = {
  maxWidth: 480,
  margin: "0 auto",
};

const cardStyle = {
  padding: 24,
  borderRadius: 16,
  border: "1px solid #e5e7eb",
  background: "rgba(255,255,255,0.06)",
};

const headerStyle = {
  marginBottom: 20,
};

const titleStyle = {
  margin: 0,
  fontSize: 28,
};

const subtitleStyle = {
  marginTop: 8,
  marginBottom: 0,
  color: "#666",
  lineHeight: 1.5,
};

const errorBoxStyle = {
  marginBottom: 16,
  padding: 14,
  borderRadius: 12,
  border: "1px solid #fecaca",
  background: "#fff1f2",
  color: "#991b1b",
};

const errorTextStyle = {
  marginTop: 8,
  marginBottom: 0,
};

const footerStyle = {
  marginTop: 18,
  display: "flex",
  gap: 8,
  flexWrap: "wrap",
  alignItems: "center",
};

const footerTextStyle = {
  color: "#666",
};

const footerLinkStyle = {
  textDecoration: "none",
  fontWeight: 700,
  color: "#111827",
};