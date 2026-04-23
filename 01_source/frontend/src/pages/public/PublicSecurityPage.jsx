import React, { useState } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";
import { changePublicPassword, resendPublicEmailVerification } from "../../services/authApi";

export default function PublicSecurityPage() {
  const { token, user, refreshUser } = useAuth();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [savingPassword, setSavingPassword] = useState(false);
  const [passwordMessage, setPasswordMessage] = useState("");
  const [passwordError, setPasswordError] = useState("");

  const [sendingEmail, setSendingEmail] = useState(false);
  const [emailMessage, setEmailMessage] = useState("");
  const [emailError, setEmailError] = useState("");
  const [previewLink, setPreviewLink] = useState("");

  const isVerified = Boolean(user?.email_verified);

  async function handleChangePassword(event) {
    event.preventDefault();
    setPasswordMessage("");
    setPasswordError("");

    if (!currentPassword || !newPassword || !confirmPassword) {
      setPasswordError("Preencha todos os campos de senha.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordError("A confirmação da nova senha não confere.");
      return;
    }

    setSavingPassword(true);
    try {
      await changePublicPassword(token, {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setPasswordMessage("Senha atualizada com sucesso.");
    } catch (error) {
      setPasswordError(error?.message || "Falha ao atualizar senha.");
    } finally {
      setSavingPassword(false);
    }
  }

  async function handleResendVerification() {
    setEmailError("");
    setEmailMessage("");
    setPreviewLink("");
    setSendingEmail(true);
    try {
      const data = await resendPublicEmailVerification(token);
      await refreshUser();
      if (data?.already_verified) {
        setEmailMessage("Seu e-mail já está verificado.");
        return;
      }
      if (data?.delivery === "disabled_preview_only" && data?.verification_link) {
        setEmailMessage("Envio de e-mail desabilitado neste ambiente. Use o link de preview:");
        setPreviewLink(String(data.verification_link));
      } else {
        setEmailMessage("Enviamos um novo link de verificação para seu e-mail.");
      }
    } catch (error) {
      setEmailError(error?.message || "Falha ao reenviar e-mail de verificação.");
    } finally {
      setSendingEmail(false);
    }
  }

  return (
    <main style={{ maxWidth: 860, margin: "0 auto", padding: 24 }}>
      <header style={{ marginBottom: 20 }}>
        <h1 style={{ margin: 0 }}>Segurança da conta</h1>
        <p style={{ marginTop: 8, color: "#475569" }}>
          Gerencie senha e verificação de e-mail da sua conta.
        </p>
      </header>

      <section style={cardStyle}>
        <h2 style={sectionTitleStyle}>Verificação de e-mail</h2>
        <p style={{ marginTop: 0, color: "#334155" }}>
          Status atual: <strong>{isVerified ? "Verificado" : "Não verificado"}</strong>
        </p>
        {!isVerified ? (
          <>
            <button
              type="button"
              onClick={handleResendVerification}
              disabled={sendingEmail}
              style={buttonStyle}
            >
              {sendingEmail ? "Enviando..." : "Reenviar link de verificação"}
            </button>
            {emailMessage ? <p style={okStyle}>{emailMessage}</p> : null}
            {emailError ? <p style={errStyle}>{emailError}</p> : null}
            {previewLink ? (
              <p style={{ marginBottom: 0 }}>
                <a href={previewLink}>{previewLink}</a>
              </p>
            ) : null}
          </>
        ) : (
          <p style={okStyle}>Seu e-mail está confirmado.</p>
        )}
      </section>

      <section style={cardStyle}>
        <h2 style={sectionTitleStyle}>Trocar senha</h2>
        <form onSubmit={handleChangePassword} style={{ display: "grid", gap: 12 }}>
          <label style={labelStyle}>
            Senha atual
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              style={inputStyle}
              autoComplete="current-password"
            />
          </label>
          <label style={labelStyle}>
            Nova senha
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              style={inputStyle}
              autoComplete="new-password"
            />
          </label>
          <label style={labelStyle}>
            Confirmar nova senha
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              style={inputStyle}
              autoComplete="new-password"
            />
          </label>
          <small style={{ color: "#64748b" }}>
            A senha deve ter ao menos 8 caracteres, com maiúscula, minúscula e número.
          </small>
          <div>
            <button type="submit" disabled={savingPassword} style={buttonStyle}>
              {savingPassword ? "Salvando..." : "Atualizar senha"}
            </button>
          </div>
          {passwordMessage ? <p style={okStyle}>{passwordMessage}</p> : null}
          {passwordError ? <p style={errStyle}>{passwordError}</p> : null}
        </form>
      </section>

      <div>
        <Link to="/meus-pedidos">Voltar para meus pedidos</Link>
      </div>
    </main>
  );
}

const cardStyle = {
  border: "1px solid #e2e8f0",
  borderRadius: 12,
  background: "#ffffff",
  padding: 16,
  marginBottom: 16,
};

const sectionTitleStyle = {
  marginTop: 0,
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
  margin: 0,
  color: "#166534",
};

const errStyle = {
  margin: 0,
  color: "#b91c1c",
};
