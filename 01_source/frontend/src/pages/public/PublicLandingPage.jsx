import React from "react";
import { Link } from "react-router-dom";

export default function PublicLandingPage() {
  return (
    <div style={{ maxWidth: 960, margin: "40px auto" }}>
      <h1>ELLAN Lab Locker</h1>
      <p>Canal público oficial de compra online.</p>

      <div style={{ display: "flex", gap: 12 }}>
        <Link to="/login">Entrar</Link>
        <Link to="/cadastro">Criar conta</Link>
        <Link to="/comprar">Comprar</Link>
      </div>
    </div>
  );
}