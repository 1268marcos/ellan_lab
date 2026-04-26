// 01_source/frontend/src/pages/public/PublicRegisterPage/jsx
// Otimizado
import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export default function PublicRegisterPage() {
  const { register, isAuthenticated, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    fullName: "",
    email: "",
    phone: "",
    password: "",
    confirmPassword: "",
    acceptTerms: false,
  });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(0);

  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      // 🔥 ALTERAÇÃO: Redirecionamento dinâmico baseado no parâmetro redirect
      const params = new URLSearchParams(window.location.search);
      const redirect = params.get("redirect") || "/meus-pedidos";
      navigate(redirect, { replace: true });
    }
  }, [authLoading, isAuthenticated, navigate]);

  useEffect(() => {
    // Calcular força da senha
    const pwd = form.password;
    let strength = 0;
    if (pwd.length >= 6) strength++;
    if (pwd.length >= 10) strength++;
    if (/[a-z]/.test(pwd) && /[A-Z]/.test(pwd)) strength++;
    if (/\d/.test(pwd)) strength++;
    if (/[^a-zA-Z0-9]/.test(pwd)) strength++;
    setPasswordStrength(strength);
  }, [form.password]);

  function updateField(field, value) {
    setForm((old) => ({ ...old, [field]: value }));
    if (error) setError("");
  }

  function validateForm() {
    if (!form.fullName.trim() || form.fullName.trim().length < 3) {
      return "Nome completo deve ter pelo menos 3 caracteres.";
    }
    if (!form.email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      return "Digite um email válido.";
    }
    if (!form.password || form.password.length < 6) {
      return "A senha deve ter pelo menos 6 caracteres.";
    }
    if (form.password !== form.confirmPassword) {
      return "As senhas não coincidem.";
    }
    if (!form.acceptTerms) {
      return "Você deve aceitar os termos de uso.";
    }
    return "";
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (submitting) return;

    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setError("");
    setSubmitting(true);

    try {
      await register({
        full_name: form.fullName.trim(),
        email: form.email.trim().toLowerCase(),
        phone: form.phone.trim() || null,
        password: form.password,
      });
      // 🔥 ALTERAÇÃO: Redirecionamento dinâmico baseado no parâmetro redirect
      const params = new URLSearchParams(window.location.search);
      const redirect = params.get("redirect") || "/meus-pedidos";
      navigate(redirect, { replace: true });
    } catch (err) {
      setError(err?.message || "Falha ao criar conta. Tente novamente.");
    } finally {
      setSubmitting(false);
    }
  }

  const getPasswordStrengthLabel = () => {
    switch (passwordStrength) {
      case 0:
      case 1:
        return { text: "Muito fraca", color: "#ef4444" };
      case 2:
        return { text: "Fraca", color: "#f97316" };
      case 3:
        return { text: "Média", color: "#eab308" };
      case 4:
        return { text: "Forte", color: "#22c55e" };
      case 5:
        return { text: "Muito forte", color: "#16a34a" };
      default:
        return { text: "", color: "#d1d5db" };
    }
  };

  const strengthInfo = getPasswordStrengthLabel();

  return (
    <main className="auth-page" style={pageStyle}>
      <div style={containerStyle}>
        {/* Hero Section */}
        <section style={heroSectionStyle}>
          <Link to="/" style={backLinkStyle} aria-label="Voltar para página inicial">
            ← Voltar
          </Link>
          <div style={heroContentStyle}>
            <h1 style={titleStyle}>Criar conta grátis</h1>
            <p style={subtitleStyle}>
              Cadastre-se em menos de 1 minuto e comece a acompanhar seus pedidos
            </p>
          </div>
        </section>

        {/* Register Card */}
        <section style={cardStyle} aria-labelledby="register-title">
          <h2 id="register-title" className="sr-only">Formulário de cadastro</h2>
          
          <form onSubmit={handleSubmit} style={formStyle} noValidate>
            {/* Full Name */}
            <div style={fieldBlockStyle}>
              <label htmlFor="register-fullname" style={labelStyle}>
                Nome completo
                <span style={requiredStyle} aria-hidden="true">*</span>
              </label>
              <input
                id="register-fullname"
                type="text"
                placeholder="Ex: João Silva"
                value={form.fullName}
                onChange={(e) => updateField("fullName", e.target.value)}
                autoComplete="name"
                required
                disabled={submitting}
                style={inputStyle}
              />
            </div>

            {/* Email */}
            <div style={fieldBlockStyle}>
              <label htmlFor="register-email" style={labelStyle}>
                Email
                <span style={requiredStyle} aria-hidden="true">*</span>
              </label>
              <input
                id="register-email"
                type="email"
                placeholder="seuemail@exemplo.com"
                value={form.email}
                onChange={(e) => updateField("email", e.target.value)}
                autoComplete="email"
                required
                disabled={submitting}
                style={inputStyle}
              />
            </div>

            {/* Phone (Optional) */}
            <div style={fieldBlockStyle}>
              <label htmlFor="register-phone" style={labelStyle}>
                Telefone <span style={optionalStyle}>(opcional)</span>
              </label>
              <input
                id="register-phone"
                type="tel"
                placeholder="+55 (11) 99999-9999"
                value={form.phone}
                onChange={(e) => updateField("phone", e.target.value)}
                autoComplete="tel"
                disabled={submitting}
                style={inputStyle}
              />
            </div>

            {/* Password */}
            <div style={fieldBlockStyle}>
              <label htmlFor="register-password" style={labelStyle}>
                Senha
                <span style={requiredStyle} aria-hidden="true">*</span>
              </label>
              <div style={passwordWrapperStyle}>
                <input
                  id="register-password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Mínimo 6 caracteres"
                  value={form.password}
                  onChange={(e) => updateField("password", e.target.value)}
                  autoComplete="new-password"
                  required
                  disabled={submitting}
                  style={{ ...inputStyle, paddingRight: 50 }}
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
              {form.password && (
                <div style={passwordStrengthContainerStyle}>
                  <div style={passwordStrengthBarStyle}>
                    <div 
                      style={{ 
                        ...passwordStrengthFillStyle, 
                        width: `${(passwordStrength / 5) * 100}%`,
                        background: strengthInfo.color 
                      }} 
                    />
                  </div>
                  <span
                    style={{
                      fontSize: 11,
                      color: strengthInfo.color,
                      display: "inline-flex",
                      alignItems: "center",
                      gap: 6,
                    }}
                  >
                    {passwordStrength >= 3 ? "✅" : "⚠️"} {strengthInfo.text}
                  </span>
                </div>
              )}
            </div>

            {/* Confirm Password */}
            <div style={fieldBlockStyle}>
              <label htmlFor="register-confirm-password" style={labelStyle}>
                Confirmar senha
                <span style={requiredStyle} aria-hidden="true">*</span>
              </label>
              <input
                id="register-confirm-password"
                type={showPassword ? "text" : "password"}
                placeholder="Digite a senha novamente"
                value={form.confirmPassword}
                onChange={(e) => updateField("confirmPassword", e.target.value)}
                autoComplete="new-password"
                required
                disabled={submitting}
                style={{
                  ...inputStyle,
                  borderColor: form.confirmPassword && form.password !== form.confirmPassword ? "#ef4444" : "#d1d5db",
                }}
              />
              {form.confirmPassword && form.password !== form.confirmPassword && (
                <span style={errorTextStyle}>As senhas não coincidem</span>
              )}
            </div>

            {/* Terms */}
            <div style={checkboxContainerStyle}>
              <label style={checkboxStyle}>
                <input
                  type="checkbox"
                  checked={form.acceptTerms}
                  onChange={(e) => updateField("acceptTerms", e.target.checked)}
                  disabled={submitting}
                  required
                />
                <span>
                  Aceito os{" "}
                  <a href="/termos" target="_blank" rel="noopener noreferrer" style={linkStyle}>
                    Termos de Uso
                  </a>{" "}
                  e{" "}
                  <a href="/privacidade" target="_blank" rel="noopener noreferrer" style={linkStyle}>
                    Política de Privacidade
                  </a>
                  <span style={requiredStyle} aria-hidden="true">*</span>
                </span>
              </label>
            </div>

            {/* Error Message */}
            {error && (
              <div style={errorBoxStyle} role="alert" aria-live="polite">
                <span style={errorIconStyle}>⚠️</span>
                <div>
                  <strong>Não foi possível criar conta</strong>
                  <p style={errorTextDetailStyle}>{error}</p>
                </div>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={submitting || authLoading}
              style={{
                ...buttonStyle,
                opacity: submitting || authLoading ? 0.6 : 1,
                cursor: submitting || authLoading ? "not-allowed" : "pointer",
              }}
              aria-busy={submitting}
            >
              {submitting ? (
                <span style={buttonLoadingStyle}>
                  <span style={spinnerStyle} aria-hidden="true"></span>
                  Criando conta...
                </span>
              ) : (
                "Criar conta grátis"
              )}
            </button>

            {/* Benefits */}
            <div style={benefitsStyle}>
              <div style={benefitItemStyle}>
                <span style={benefitIconStyle}>✅</span>
                <span style={benefitTextStyle}>Acompanhe seus pedidos</span>
              </div>
              <div style={benefitItemStyle}>
                <span style={benefitIconStyle}>🔔</span>
                <span style={benefitTextStyle}>Receba notificações</span>
              </div>
              <div style={benefitItemStyle}>
                <span style={benefitIconStyle}>⚡</span>
                <span style={benefitTextStyle}>Checkout rápido</span>
              </div>
            </div>

            {/* Divider */}
            <div style={dividerStyle}>
              <span>ou</span>
            </div>

            {/* Login Link */}
            <div style={footerStyle}>
              <span style={footerTextStyle}>Já tem conta?</span>
              <Link to="/login" style={footerLinkStyle}>
                Fazer login
              </Link>
            </div>
          </form>
        </section>

        {/* Trust Signals */}
        <section style={trustSignalsStyle} aria-label="Informações de segurança">
          <div style={trustItemStyle}>
            <span style={trustIconStyle}>🔒</span>
            <span style={trustTextStyle}>Dados protegidos</span>
          </div>
          <div style={trustItemStyle}>
            <span style={trustIconStyle}>📧</span>
            <span style={trustTextStyle}>Sem spam</span>
          </div>
          <div style={trustItemStyle}>
            <span style={trustIconStyle}>⚡</span>
            <span style={trustTextStyle}>Cadastro rápido</span>
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
  maxWidth: 520,
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
  gap: 18,
};

const fieldBlockStyle = {
  display: "grid",
  gap: 6,
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

const optionalStyle = {
  color: "#6b7280",
  fontWeight: 400,
  fontSize: 13,
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

const passwordStrengthContainerStyle = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  marginTop: 6,
};

const passwordStrengthBarStyle = {
  flex: 1,
  height: 4,
  background: "#e5e7eb",
  borderRadius: 2,
  overflow: "hidden",
};

const passwordStrengthFillStyle = {
  height: "100%",
  transition: "all 0.3s",
  borderRadius: 2,
};

const checkboxContainerStyle = {
  marginTop: 4,
};

const checkboxStyle = {
  display: "flex",
  alignItems: "flex-start",
  gap: 10,
  fontSize: 14,
  color: "#6b7280",
  cursor: "pointer",
  lineHeight: 1.4,
  minHeight: 44,
};

const linkStyle = {
  display: "inline-flex",
  alignItems: "center",
  minHeight: 32,
  padding: "2px 4px",
  color: "#667eea",
  textDecoration: "underline",
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

const errorTextDetailStyle = {
  margin: "4px 0 0 0",
  fontSize: 14,
};

const errorTextStyle = {
  fontSize: 12,
  color: "#ef4444",
  marginTop: 4,
  display: "block",
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

const benefitsStyle = {
  display: "grid",
  gap: 10,
  padding: "16px 0",
  borderTop: "1px solid #e5e7eb",
  borderBottom: "1px solid #e5e7eb",
};

const benefitItemStyle = {
  display: "flex",
  alignItems: "center",
  gap: 10,
  fontSize: 14,
  color: "#374151",
};

const benefitIconStyle = {
  fontSize: 16,
};

const benefitTextStyle = {
  fontWeight: 500,
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
  if (!document.head.querySelector("#register-styles")) {
    styleSheet.id = "register-styles";
    document.head.appendChild(styleSheet);
  }
}