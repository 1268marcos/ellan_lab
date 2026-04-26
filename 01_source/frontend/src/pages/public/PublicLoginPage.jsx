// 01_source/frontend/src/pages/public/PublicLoginPage.jsx
import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export default function PublicLoginPage() {
  const { login, isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    email: "",
    password: "",
    rememberMe: false,
  });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    if (!loading && isAuthenticated) {
      // 🔥 ALTERAÇÃO: Redirecionamento dinâmico baseado no parâmetro redirect
      const params = new URLSearchParams(window.location.search);
      const redirect = params.get("redirect") || "/meus-pedidos";
      navigate(redirect, { replace: true });
    }
  }, [loading, isAuthenticated, navigate]);

  function updateField(field, value) {
    setForm((old) => ({ ...old, [field]: value }));
    if (error) setError("");
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (submitting) return;

    const payload = {
      email: form.email.trim().toLowerCase(),
      password: form.password,
      remember_me: form.rememberMe,
    };

    if (!payload.email || !payload.password) {
      setError("Preencha email e senha.");
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(payload.email)) {
      setError("Digite um email válido.");
      return;
    }

    setError("");
    setSubmitting(true);

    try {
      await login(payload);
      // 🔥 ALTERAÇÃO: Redirecionamento dinâmico baseado no parâmetro redirect
      const params = new URLSearchParams(window.location.search);
      const redirect = params.get("redirect") || "/meus-pedidos";
      navigate(redirect, { replace: true });
    } catch (err) {
      setError(err?.message || "Falha no login. Verifique suas credenciais.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-page" style={pageStyle}>
      <div style={containerStyle}>
        {/* Hero Section */}
        <section style={heroSectionStyle}>
          <Link to="/" style={backLinkStyle} aria-label="Voltar para página inicial">
            ← Voltar
          </Link>
          <div style={heroContentStyle}>
            <h1 style={titleStyle}>Bem-vindo de volta</h1>
            <p style={subtitleStyle}>
              Acesse sua conta para acompanhar pedidos e retiradas
            </p>
          </div>
        </section>

        {/* Login Card */}
        <section style={cardStyle} aria-labelledby="login-title">
          <h2 id="login-title" className="sr-only">Formulário de login</h2>
          
          <form onSubmit={handleSubmit} style={formStyle} noValidate>
            {/* Email Field */}
            <div style={fieldBlockStyle}>
              <label htmlFor="login-email" style={labelStyle}>
                Email
                <span style={requiredStyle} aria-hidden="true">*</span>
              </label>
              <input
                id="login-email"
                type="email"
                placeholder="seuemail@exemplo.com"
                value={form.email}
                onChange={(e) => updateField("email", e.target.value)}
                autoComplete="email"
                required
                disabled={submitting}
                style={{
                  ...inputStyle,
                  borderColor: error && !form.email ? "#ef4444" : "#d1d5db",
                }}
                aria-invalid={error && !form.email ? "true" : "false"}
                aria-describedby={error && !form.email ? "email-error" : undefined}
              />
            </div>

            {/* Password Field */}
            <div style={fieldBlockStyle}>
              <label htmlFor="login-password" style={labelStyle}>
                Senha
                <span style={requiredStyle} aria-hidden="true">*</span>
              </label>
              <div style={passwordWrapperStyle}>
                <input
                  id="login-password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Digite sua senha"
                  value={form.password}
                  onChange={(e) => updateField("password", e.target.value)}
                  autoComplete="current-password"
                  required
                  disabled={submitting}
                  style={{
                    ...inputStyle,
                    paddingRight: 50,
                    borderColor: error && !form.password ? "#ef4444" : "#d1d5db",
                  }}
                  aria-invalid={error && !form.password ? "true" : "false"}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={togglePasswordStyle}
                  aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
                >
                  {showPassword ? "🙈" : "👁️"}
                </button>
              </div>
            </div>

            {/* Remember Me & Forgot Password */}
            <div style={optionsRowStyle}>
              <label style={checkboxStyle}>
                <input
                  type="checkbox"
                  checked={form.rememberMe}
                  onChange={(e) => updateField("rememberMe", e.target.checked)}
                  disabled={submitting}
                />
                <span>Lembrar-me</span>
              </label>
              <Link 
                to="/recuperar-senha" 
                style={forgotLinkStyle}
              >
                Esqueceu a senha?
              </Link>
            </div>

            {/* Error Message */}
            {error && (
              <div 
                id="login-error"
                style={errorBoxStyle} 
                role="alert"
                aria-live="polite"
              >
                <span style={errorIconStyle}>⚠️</span>
                <div>
                  <strong>Não foi possível entrar</strong>
                  <p style={errorTextStyle}>{error}</p>
                </div>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={submitting || loading}
              style={{
                ...buttonStyle,
                opacity: submitting || loading ? 0.6 : 1,
                cursor: submitting || loading ? "not-allowed" : "pointer",
              }}
              aria-busy={submitting}
            >
              {submitting ? (
                <span style={buttonLoadingStyle}>
                  <span style={spinnerStyle} aria-hidden="true"></span>
                  Entrando...
                </span>
              ) : (
                "Entrar"
              )}
            </button>

            {/* Divider */}
            <div style={dividerStyle}>
              <span>ou</span>
            </div>

            {/* Register Link */}
            <div style={footerStyle}>
              <span style={footerTextStyle}>Ainda não tem conta?</span>
              <Link to="/cadastro" style={footerLinkStyle}>
                Criar conta grátis
              </Link>
            </div>
          </form>
        </section>

        {/* Trust Signals */}
        <section style={trustSignalsStyle} aria-label="Informações de segurança">
          <div style={trustItemStyle}>
            <span style={trustIconStyle}>🔒</span>
            <span style={trustTextStyle}>Conexão segura</span>
          </div>
          <div style={trustItemStyle}>
            <span style={trustIconStyle}>⚡</span>
            <span style={trustTextStyle}>Acesso rápido</span>
          </div>
          <div style={trustItemStyle}>
            <span style={trustIconStyle}>📱</span>
            <span style={trustTextStyle}>Multi-dispositivo</span>
          </div>
        </section>
      </div>
    </main>
  );
}

// Styles
const pageStyle = {
  minHeight: "100vh",
  background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  padding: "20px 16px",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
};

const containerStyle = {
  width: "100%",
  maxWidth: 480,
  margin: "0 auto",
};

const heroSectionStyle = {
  textAlign: "center",
  marginBottom: 24,
  color: "white",
};

const backLinkStyle = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  minHeight: 44,
  color: "rgba(255,255,255,0.9)",
  textDecoration: "none",
  fontSize: 14,
  marginBottom: 16,
  padding: "8px 12px",
  borderRadius: 8,
  background: "rgba(255,255,255,0.1)",
  transition: "all 0.2s",
};

const heroContentStyle = {
  marginBottom: 0,
};

const titleStyle = {
  margin: "0 0 8px 0",
  fontSize: 32,
  fontWeight: 800,
};

const subtitleStyle = {
  margin: 0,
  fontSize: 16,
  opacity: 0.9,
  lineHeight: 1.5,
};

const cardStyle = {
  padding: 32,
  borderRadius: 20,
  border: "1px solid rgba(255,255,255,0.2)",
  background: "rgba(255,255,255,0.95)",
  backdropFilter: "blur(10px)",
  boxShadow: "0 20px 60px rgba(0,0,0,0.3)",
};

const formStyle = {
  display: "grid",
  gap: 20,
};

const fieldBlockStyle = {
  display: "grid",
  gap: 8,
};

const labelStyle = {
  fontSize: 14,
  fontWeight: 600,
  color: "#374151",
  display: "flex",
  alignItems: "center",
  gap: 4,
};

const requiredStyle = {
  color: "#ef4444",
};

const passwordWrapperStyle = {
  position: "relative",
};

const inputStyle = {
  width: "100%",
  padding: "14px 16px",
  borderRadius: 12,
  border: "1px solid #d1d5db",
  boxSizing: "border-box",
  fontSize: 15,
  transition: "all 0.2s",
  outline: "none",
};

const togglePasswordStyle = {
  position: "absolute",
  right: 12,
  top: "50%",
  transform: "translateY(-50%)",
  background: "none",
  border: "none",
  cursor: "pointer",
  fontSize: 18,
  width: 44,
  height: 44,
  padding: 0,
  opacity: 0.6,
  transition: "opacity 0.2s",
};

const optionsRowStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 12,
  flexWrap: "wrap",
};

const checkboxStyle = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  fontSize: 14,
  color: "#6b7280",
  cursor: "pointer",
  minHeight: 44,
};

const forgotLinkStyle = {
  display: "inline-flex",
  alignItems: "center",
  minHeight: 44,
  padding: "8px 10px",
  fontSize: 14,
  color: "#667eea",
  textDecoration: "none",
  fontWeight: 600,
};

const errorBoxStyle = {
  padding: 16,
  borderRadius: 12,
  border: "1px solid #fecaca",
  background: "#fef2f2",
  color: "#991b1b",
  display: "flex",
  alignItems: "flex-start",
  gap: 12,
};

const errorIconStyle = {
  fontSize: 20,
  flexShrink: 0,
};

const errorTextStyle = {
  margin: "4px 0 0 0",
  fontSize: 14,
};

const buttonStyle = {
  width: "100%",
  padding: "16px 20px",
  borderRadius: 12,
  border: "none",
  background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  color: "white",
  fontWeight: 700,
  fontSize: 16,
  transition: "all 0.2s",
};

const buttonLoadingStyle = {
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  gap: 8,
};

const spinnerStyle = {
  width: 20,
  height: 20,
  border: "2px solid rgba(255,255,255,0.3)",
  borderTopColor: "white",
  borderRadius: "50%",
  animation: "spin 0.6s linear infinite",
};

const dividerStyle = {
  display: "flex",
  alignItems: "center",
  gap: 12,
  color: "#475569",
  fontSize: 14,
  margin: "8px 0",
};

const footerStyle = {
  textAlign: "center",
  display: "flex",
  flexDirection: "column",
  gap: 8,
  marginTop: 8,
};

const footerTextStyle = {
  color: "#6b7280",
  fontSize: 14,
};

const footerLinkStyle = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  minHeight: 44,
  padding: "8px 10px",
  color: "#667eea",
  textDecoration: "none",
  fontWeight: 700,
  fontSize: 15,
};

const trustSignalsStyle = {
  display: "flex",
  justifyContent: "center",
  gap: 24,
  marginTop: 24,
  flexWrap: "wrap",
};

const trustItemStyle = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  color: "rgba(255,255,255,0.9)",
  fontSize: 13,
};

const trustIconStyle = {
  fontSize: 16,
};

const trustTextStyle = {
  fontWeight: 500,
};

// Add animation styles
if (typeof document !== "undefined") {
  const styleSheet = document.createElement("style");
  styleSheet.textContent = `
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
    @media (max-width: 640px) {
      .auth-page {
        padding: 16px 12px;
      }
    }
  `;
  if (!document.head.querySelector("#login-styles")) {
    styleSheet.id = "login-styles";
    document.head.appendChild(styleSheet);
  }
}