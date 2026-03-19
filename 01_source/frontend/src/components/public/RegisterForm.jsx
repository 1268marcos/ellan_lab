import React, { useMemo, useState } from "react";

export default function RegisterForm({ onSubmit, loading = false }) {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [localError, setLocalError] = useState("");

  const normalizedPayload = useMemo(() => {
    return {
      full_name: fullName.trim(),
      email: email.trim(),
      phone: phone.trim() || null,
      password,
    };
  }, [fullName, email, phone, password]);

  function validate() {
    if (!normalizedPayload.full_name) {
      return "Informe seu nome completo.";
    }

    if (normalizedPayload.full_name.length < 3) {
      return "Informe um nome completo válido.";
    }

    if (!normalizedPayload.email) {
      return "Informe seu email.";
    }

    if (!normalizedPayload.password) {
      return "Informe sua senha.";
    }

    if (normalizedPayload.password.length < 6) {
      return "A senha deve ter pelo menos 6 caracteres.";
    }

    return "";
  }

  function handleSubmit(event) {
    event.preventDefault();

    if (loading) {
      return;
    }

    const validationError = validate();
    if (validationError) {
      setLocalError(validationError);
      return;
    }

    setLocalError("");

    onSubmit?.(normalizedPayload);
  }

  return (
    <form onSubmit={handleSubmit} style={formStyle}>
      <div style={fieldBlockStyle}>
        <label htmlFor="register-full-name" style={labelStyle}>
          Nome completo
        </label>
        <input
          id="register-full-name"
          type="text"
          placeholder="Digite seu nome completo"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          required
          autoComplete="name"
          style={inputStyle}
        />
      </div>

      <div style={fieldBlockStyle}>
        <label htmlFor="register-email" style={labelStyle}>
          Email
        </label>
        <input
          id="register-email"
          type="email"
          placeholder="seuemail@exemplo.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          autoComplete="email"
          style={inputStyle}
        />
      </div>

      <div style={fieldBlockStyle}>
        <label htmlFor="register-phone" style={labelStyle}>
          Telefone
        </label>
        <input
          id="register-phone"
          type="text"
          placeholder="Opcional"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          autoComplete="tel"
          style={inputStyle}
        />
      </div>

      <div style={fieldBlockStyle}>
        <label htmlFor="register-password" style={labelStyle}>
          Senha
        </label>
        <input
          id="register-password"
          type="password"
          placeholder="Crie uma senha"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          autoComplete="new-password"
          style={inputStyle}
        />
        <span style={helpTextStyle}>Use pelo menos 6 caracteres.</span>
      </div>

      {localError ? (
        <div style={errorBoxStyle}>
          <strong>Revise os dados do cadastro.</strong>
          <p style={errorTextStyle}>{localError}</p>
        </div>
      ) : null}

      <button
        type="submit"
        disabled={loading}
        style={{
          ...buttonStyle,
          opacity: loading ? 0.7 : 1,
          cursor: loading ? "not-allowed" : "pointer",
        }}
      >
        {loading ? "Criando conta..." : "Criar conta"}
      </button>
    </form>
  );
}

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

const helpTextStyle = {
  fontSize: 12,
  color: "#666",
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

const buttonStyle = {
  padding: "12px 14px",
  borderRadius: 10,
  border: "1px solid #d1d5db",
  background: "#111827",
  color: "white",
  fontWeight: 700,
};