import React, { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { requestPublicPasswordReset, resetPublicPassword } from "../../services/authApi";

export default function PublicForgotPasswordPage() {
  const [params] = useSearchParams();
  const token = useMemo(() => params.get("token") || "", [params]);

  const [email, setEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const resetMode = Boolean(token);

  async function handleRequestReset(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    if (!email.trim()) {
      setError("Informe seu e-mail.");
      return;
    }
    setLoading(true);
    try {
      const res = await requestPublicPasswordReset({ email: email.trim().toLowerCase() });
      setMessage(res?.message || "Se o e-mail existir, você receberá um link para redefinir a senha.");
    } catch (err) {
      setError(err?.message || "Falha ao solicitar redefinição de senha.");
    } finally {
      setLoading(false);
    }
  }

  async function handleResetPassword(event) {
    event.preventDefault();
    setError("");
    setMessage("");

    if (!newPassword || !confirmPassword) {
      setError("Preencha a nova senha e a confirmação.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("A confirmação da senha não confere.");
      return;
    }

    setLoading(true);
    try {
      const res = await resetPublicPassword({
        token,
        new_password: newPassword,
      });
      setMessage(res?.message === "password_reset_success" ? "Senha redefinida com sucesso." : "Senha atualizada.");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      setError(err?.message || "Falha ao redefinir senha.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ maxWidth: 760, margin: "0 auto", padding: 24 }}>
      <section style={cardStyle}>
        <h1 style={{ marginTop: 0 }}>{resetMode ? "Redefinir senha" : "Recuperar senha"}</h1>

        {!resetMode ? (
          <form onSubmit={handleRequestReset} style={{ display: "grid", gap: 12 }}>
            <label style={labelStyle}>
              E-mail da conta
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="seuemail@exemplo.com"
                style={inputStyle}
                autoComplete="email"
              />
            </label>
            <button type="submit" disabled={loading} style={buttonStyle}>
              {loading ? "Enviando..." : "Enviar link de redefinição"}
            </button>
          </form>
        ) : (
          <form onSubmit={handleResetPassword} style={{ display: "grid", gap: 12 }}>
            <label style={labelStyle}>
              Nova senha
              <div style={passwordWrapperStyle}>
                <input
                  type={showPassword ? "text" : "password"}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  style={{ ...inputStyle, paddingRight: 50 }}
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((prev) => !prev)}
                  style={togglePasswordStyle}
                  aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
                  tabIndex={-1}
                >
                  {showPassword ? "🙈" : "👁️"}
                </button>
              </div>
            </label>
            <label style={labelStyle}>
              Confirmar nova senha
              <input
                type={showPassword ? "text" : "password"}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                style={inputStyle}
                autoComplete="new-password"
              />
            </label>
            <small style={{ color: "#64748b" }}>
              A senha deve ter ao menos 8 caracteres, com maiúscula, minúscula e número.
            </small>
            <button type="submit" disabled={loading} style={buttonStyle}>
              {loading ? "Redefinindo..." : "Redefinir senha"}
            </button>
          </form>
        )}

        {message ? <p style={okStyle}>{message}</p> : null}
        {error ? <p style={errStyle}>{error}</p> : null}

        <div style={{ marginTop: 12, display: "flex", gap: 12 }}>
          <Link to="/login">Voltar para login</Link>
          <Link to="/cadastro">Criar conta</Link>
        </div>
      </section>
    </main>
  );
}

const cardStyle = {
  border: "1px solid #e2e8f0",
  borderRadius: 12,
  background: "#fff",
  padding: 18,
};

const labelStyle = {
  display: "grid",
  gap: 6,
  color: "#334155",
  fontWeight: 600,
};

const inputStyle = {
  border: "1px solid #cbd5e1",
  borderRadius: 8,
  padding: "10px 12px",
  fontSize: 14,
  width: "100%",
  boxSizing: "border-box",
};

const passwordWrapperStyle = {
  position: "relative",
  display: "flex",
  alignItems: "center",
};

const togglePasswordStyle = {
  position: "absolute",
  right: 10,
  top: "50%",
  transform: "translateY(-50%)",
  border: "none",
  background: "none",
  cursor: "pointer",
  fontSize: 16,
  padding: 4,
};

const buttonStyle = {
  border: "none",
  borderRadius: 8,
  background: "#0f172a",
  color: "#fff",
  padding: "10px 14px",
  cursor: "pointer",
  fontWeight: 700,
};

const okStyle = {
  color: "#166534",
  marginBottom: 0,
};

const errStyle = {
  color: "#b91c1c",
  marginBottom: 0,
};
