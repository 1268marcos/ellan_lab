import React from "react";
import { Routes, Route, Navigate, Link, useLocation } from "react-router-dom";
import LockerDashboard from "./pages/LockerDashboard.jsx";

export default function App() {
  const location = useLocation();
  
  // Define a cor de fundo baseada na rota atual
  const navBackground = location.pathname === '/pt' ? '#222324' : '#0b0d10';



  // Define gradientes baseados na rota atual
  const getNavBackground = () => {
    if (location.pathname === '/pt') {
      // Gradiente para Portugal - cores da bandeira (verde e vermelho)
      // return 'linear-gradient(135deg, #006600 0%, #CE1126 70%)';
      // Com opacidade para manter legibilidade:
      return 'linear-gradient(135deg, rgba(0,102,0,0.9) 0%, rgba(206,17,38,0.9) 70%)';
      // Gradiente com mais nuances das bandeiras:
      // return 'linear-gradient(90deg, #006600 0%, #CE1126 50%, #FFD700 100%)';
    } else if (location.pathname === '/sp') {
      // Gradiente para Brasil - cores da bandeira (verde, amarelo, azul)
      // return 'linear-gradient(135deg, #009B3A 0%, #FEDD00 50%, #002776 100%)';
      // Com opacidade para manter legibilidade:
      return 'linear-gradient(135deg, rgba(0,155,58,0.9) 0%, rgba(254,221,0,0.9) 50%, rgba(0,39,118,0.9) 100%)';
      // Gradiente com mais nuances das bandeiras:
      // return 'linear-gradient(90deg, #009B3A 0%, #FEDD00 40%, #002776 80%, #FFFFFF 100%)';
    }
    // Gradiente padrão
    return 'linear-gradient(135deg, #222324, #0b0d10)';
    // Gradiente com mais nuances das bandeiras:
    // return 'linear-gradient(90deg, #222324, #0b0d10)';
  };



  // Componente para renderizar a bandeira apropriada
  // Usando emojis de bandeira (funciona em todos os navegadores)
  const getFlagEmoji = () => {
    if (location.pathname === '/pt') {
      return '🇵🇹'; // Bandeira de Portugal
    } else if (location.pathname === '/sp') {
      return '🇧🇷'; // Bandeira do Brasil
    }
    return '';
  };

  return (
    <div>
      <nav
        style={{
          padding: 12,
          display: "flex",
          gap: 12,
          alignItems: "center",
          background:  getNavBackground(), // Usa o gradiente dinâmico// navBackground, // Usa a cor dinâmica // anterior fixa em "#0b0d10",
          borderBottom: "1px solid rgba(255,255,255,0.10)",
          transition: 'background-color 0.3s ease', // Transição suave opcional
        }}
      >
        <Link style={linkStyle} to="/sp">
          /sp
        </Link>
        <Link style={linkStyle} to="/pt">
          /pt
        </Link>

        <span style={{ marginLeft: 10, opacity: 0.65, color: "white", fontSize: 12 }}>
          {getFlagEmoji()} Dashboard (gavetas 1–24 + carrossel 6×4)
        </span>
      </nav>

      <Routes>
        <Route path="/" element={<Navigate to="/sp" replace />} />
        <Route path="/sp" element={<LockerDashboard region="SP" />} />
        <Route path="/pt" element={<LockerDashboard region="PT" />} />
        <Route path="*" element={<div style={{ padding: 24 }}>404</div>} />
      </Routes>
    </div>
  );
}

const linkStyle = {
  color: "white",
  textDecoration: "none",
  padding: "8px 10px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.18)",
  background: "rgba(255,255,255,0.06)",
};