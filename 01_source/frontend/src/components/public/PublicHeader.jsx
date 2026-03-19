import React from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export default function PublicHeader() {
  const { user, isAuthenticated, logout, loading } = useAuth();

  return (
    <header
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        gap: 12,
        padding: 16,
        borderBottom: "1px solid #ddd",
      }}
    >
      <div>
        <strong>ELLAN Lab Locker</strong>
      </div>

      <nav style={{ display: "flex", gap: 12 }}>
        <Link to="/meus-pedidos">Meus pedidos</Link>
      </nav>

      <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
        {loading ? (
          <span>Carregando...</span>
        ) : isAuthenticated ? (
          <>
            <span>Logado como {user?.full_name || user?.email}</span>
            <button onClick={logout}>Sair</button>
          </>
        ) : (
          <>
            <Link to="/login">Entrar</Link>
            <Link to="/cadastro">Criar conta</Link>
          </>
        )}
      </div>
    </header>
  );
}