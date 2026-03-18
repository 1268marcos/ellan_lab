import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import LoginForm from "../../components/public/LoginForm";
import { useAuth } from "../../context/AuthContext";

export default function PublicLoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleLogin(payload) {
    setError("");
    setLoading(true);
    try {
      await login(payload);
      navigate("/meus-pedidos");
    } catch (err) {
      setError(err.message || "Falha no login");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 420, margin: "40px auto" }}>
      <h1>Entrar</h1>
      {error ? <p style={{ color: "red" }}>{error}</p> : null}
      <LoginForm onSubmit={handleLogin} loading={loading} />
    </div>
  );
}