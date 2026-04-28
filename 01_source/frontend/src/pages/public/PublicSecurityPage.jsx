import React, { useState } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";
import { changePublicPassword, resendPublicEmailVerification } from "../../services/authApi";
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
import {
  formLabelStyle,
  formInputStyle,
  passwordFieldWrapperStyle,
  passwordToggleButtonStyle,
  primaryFormButtonStyle,
} from "../../components/public/myAreaSharedFormStyles";
import { resolvePersonalGreeting } from "./myAreaDisplayName";

export default function PublicSecurityPage() {
  const { token, user, refreshUser } = useAuth();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(0);
  const [savingPassword, setSavingPassword] = useState(false);
  const [passwordMessage, setPasswordMessage] = useState("");
  const [passwordError, setPasswordError] = useState("");

  const [sendingEmail, setSendingEmail] = useState(false);
  const [emailMessage, setEmailMessage] = useState("");
  const [emailError, setEmailError] = useState("");
  const [previewLink, setPreviewLink] = useState("");

  const isVerified = Boolean(user?.email_verified);
  const strengthInfo = getPasswordStrengthLabel(passwordStrength);
  const isPasswordAcceptable = passwordStrength >= 3;
  const greeting = resolvePersonalGreeting(user);

  React.useEffect(() => {
    let strength = 0;
    if (newPassword.length >= 6) strength++;
    if (newPassword.length >= 10) strength++;
    if (/[a-z]/.test(newPassword) && /[A-Z]/.test(newPassword)) strength++;
    if (/\d/.test(newPassword)) strength++;
    if (/[^a-zA-Z0-9]/.test(newPassword)) strength++;
    setPasswordStrength(strength);
  }, [newPassword]);

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
    <main style={pageStyle}>
      <div style={containerStyle}>
        <PageHeader
          title="Segurança da conta"
          subtitle={`${greeting}Gerencie senha e verificação de e-mail da sua conta.`}
          ctaTo="/conta/dados-fiscais"
          ctaLabel="📄 Dados fiscais"
          headerStyle={pageHeaderStyle}
          titleStyle={titleStyle}
          subtitleStyle={subtitleStyle}
          ctaStyle={newOrderButtonStyle}
        />

      <section style={{ ...cardStyle, borderLeft: `5px solid ${isVerified ? "#22c55e" : "#f59e0b"}` }}>
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

      <section style={{ ...cardStyle, borderLeft: "5px solid #3b82f6" }}>
        <h2 style={sectionTitleStyle}>Trocar senha</h2>
        <form onSubmit={handleChangePassword} style={{ display: "grid", gap: 12 }}>
          <label style={labelStyle}>
            Senha atual
            <div style={passwordWrapperStyle}>
              <input
                type={showCurrentPassword ? "text" : "password"}
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                style={{ ...inputStyle, paddingRight: 50 }}
                autoComplete="current-password"
              />
              <button
                type="button"
                onClick={() => setShowCurrentPassword((prev) => !prev)}
                style={togglePasswordStyle}
                aria-label={showCurrentPassword ? "Ocultar senha atual" : "Mostrar senha atual"}
                tabIndex={-1}
              >
                {showCurrentPassword ? "🙈" : "👁️"}
              </button>
            </div>
          </label>
          <label style={labelStyle}>
            Nova senha
            <div style={passwordWrapperStyle}>
              <input
                type={showNewPassword ? "text" : "password"}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                style={{ ...inputStyle, paddingRight: 50 }}
                autoComplete="new-password"
              />
              <button
                type="button"
                onClick={() => setShowNewPassword((prev) => !prev)}
                style={togglePasswordStyle}
                aria-label={showNewPassword ? "Ocultar nova senha" : "Mostrar nova senha"}
                tabIndex={-1}
              >
                {showNewPassword ? "🙈" : "👁️"}
              </button>
            </div>
            {newPassword ? (
              <div style={passwordStrengthContainerStyle}>
                <div style={passwordStrengthBarStyle}>
                  <div
                    style={{
                      ...passwordStrengthFillStyle,
                      width: `${(passwordStrength / 5) * 100}%`,
                      background: strengthInfo.color,
                    }}
                  />
                </div>
                <span style={{ fontSize: 11, color: strengthInfo.color }}>{strengthInfo.text}</span>
              </div>
            ) : null}
          </label>
          <label style={labelStyle}>
            Confirmar nova senha
            <div style={passwordWrapperStyle}>
              <input
                type={showConfirmPassword ? "text" : "password"}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                style={{ ...inputStyle, paddingRight: 50 }}
                autoComplete="new-password"
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword((prev) => !prev)}
                style={togglePasswordStyle}
                aria-label={showConfirmPassword ? "Ocultar confirmação da senha" : "Mostrar confirmação da senha"}
                tabIndex={-1}
              >
                {showConfirmPassword ? "🙈" : "👁️"}
              </button>
            </div>
          </label>
          <small
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
              color: newPassword
                ? isPasswordAcceptable
                  ? "#166534"
                  : strengthInfo.color
                : "#64748b",
              fontWeight: newPassword ? 600 : 400,
            }}
          >
            {newPassword ? (isPasswordAcceptable ? "✅" : "⚠️") : null}
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

      <div style={backLinkWrapStyle}>
        <Link to="/meus-pedidos" style={backLinkStyle}>Voltar para meus pedidos</Link>
      </div>
      </div>
    </main>
  );
}

const cardStyle = {
  ...elevatedCardBaseStyle,
  padding: 20,
  marginBottom: 18,
};

const sectionTitleStyle = {
  marginTop: 0,
};

const labelStyle = {
  ...formLabelStyle,
};

const inputStyle = {
  ...formInputStyle,
};

const passwordWrapperStyle = {
  ...passwordFieldWrapperStyle,
};

const togglePasswordStyle = {
  ...passwordToggleButtonStyle,
};

const buttonStyle = {
  ...primaryFormButtonStyle,
};

const okStyle = {
  margin: 0,
  color: "#166534",
};

const errStyle = {
  margin: 0,
  color: "#b91c1c",
};

const passwordStrengthContainerStyle = {
  marginTop: 6,
  display: "flex",
  alignItems: "center",
  gap: 8,
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
  borderRadius: 2,
  transition: "all 0.3s ease",
};

const backLinkWrapStyle = {
  marginTop: 10,
  padding: "10px 4px",
};

const backLinkStyle = {
  color: "#334155",
  fontWeight: 700,
  textDecoration: "none",
  borderBottom: "2px solid #cbd5e1",
  paddingBottom: 2,
};

function getPasswordStrengthLabel(strength) {
  switch (strength) {
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
}
