import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import RegisterForm from "../../components/public/RegisterForm";
import { useAuth } from "../../context/AuthContext";

export default function PublicRegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleRegister(payload) {
    setError("");
    setLoading(true);
    try {
      await register(payload);
      navigate("/meus-pedidos");
    } catch (err) {
      setError(err.message || "Falha ao criar conta");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 420, margin: "40px auto" }}>
      <h1>Criar conta</h1>
      {error ? <p style={{ color: "red" }}>{error}</p> : null}
      <RegisterForm onSubmit={handleRegister} loading={loading} />
    </div>
  );
}