import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export default function PublicLoginPage() {
  const { login, isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    email: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!loading && isAuthenticated) {
      navigate("/meus-pedidos", { replace: true });
    }
  }, [loading, isAuthenticated, navigate]);

  function updateField(field, value) {
    setForm((old) => ({
      ...old,
      [field]: value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (submitting) {
      return;
    }

    const payload = {
      email: form.email.trim(),
      password: form.password,
    };

    if (!payload.email || !payload.password) {
      setError("Preencha email e senha.");
      return;
    }

    setError("");
    setSubmitting(true);

    try {
      await login(payload);
      navigate("/meus-pedidos", { replace: true });
    } catch (err) {
      setError(err?.message || "Falha no login.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main style={pageStyle}>
      <div style={containerStyle}>
        <section style={cardStyle}>
          <div style={headerStyle}>
            <h1 style={titleStyle}>Entrar</h1>
            <p style={subtitleStyle}>
              Acesse sua conta para acompanhar seus pedidos e retirada.
            </p>
          </div>

          <form onSubmit={handleSubmit} style={formStyle}>
            <div style={fieldBlockStyle}>
              <label htmlFor="login-email" style={labelStyle}>
                Email
              </label>
              <input
                id="login-email"
                type="email"
                placeholder="seuemail@exemplo.com"
                value={form.email}
                onChange={(e) => updateField("email", e.target.value)}
                autoComplete="email"
                style={inputStyle}
              />
            </div>

            <div style={fieldBlockStyle}>
              <label htmlFor="login-password" style={labelStyle}>
                Senha
              </label>
              <input
                id="login-password"
                type="password"
                placeholder="Digite sua senha"
                value={form.password}
                onChange={(e) => updateField("password", e.target.value)}
                autoComplete="current-password"
                style={inputStyle}
              />
            </div>

            {error ? (
              <div style={errorBoxStyle}>
                <strong>Não foi possível entrar.</strong>
                <p style={errorTextStyle}>{error}</p>
              </div>
            ) : null}

            <button
              type="submit"
              disabled={submitting || loading}
              style={{
                ...buttonStyle,
                opacity: submitting || loading ? 0.7 : 1,
                cursor: submitting || loading ? "not-allowed" : "pointer",
              }}
            >
              {submitting || loading ? "Entrando..." : "Entrar"}
            </button>
          </form>

          <div style={footerStyle}>
            <span style={footerTextStyle}>Ainda não tem conta?</span>
            <Link to="/cadastro" style={footerLinkStyle}>
              Criar conta
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

const formStyle = {
  display: "grid",
  gap: 14,
};

const fieldBlockStyle = {
  display: "grid",
  gap: 6,
};

const labelStyle = {
  fontSize: 14,
  fontWeight: 600,
};

const inputStyle = {
  width: "100%",
  padding: "12px 14px",
  borderRadius: 10,
  border: "1px solid #d1d5db",
  boxSizing: "border-box",
  fontSize: 14,
};

const buttonStyle = {
  padding: "12px 14px",
  borderRadius: 10,
  border: "1px solid #d1d5db",
  background: "#111827",
  color: "white",
  fontWeight: 700,
};

const errorBoxStyle = {
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