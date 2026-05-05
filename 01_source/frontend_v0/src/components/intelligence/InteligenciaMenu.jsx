
import React from "react";
import { Link } from "react-router-dom";
import { Brain, BarChart3, TrendingUp, Activity, Users, CircleDollarSign, LayoutGrid, ShieldAlert, MapPinned, Wallet, MessagesSquare } from "lucide-react";

const LINKS = [
  { to: "/intelligence/dashboard", label: "Dashboard de ML", Icon: Brain },
  { to: "/intelligence/models", label: "Monitor de Modelos", Icon: BarChart3 },
  { to: "/intelligence/at-risk", label: "Lockers em Risco", Icon: Activity },
  { to: "/intelligence/history", label: "Histórico de Predições", Icon: TrendingUp },
  { to: "/intelligence/dynamic-pricing", label: "Preços dinâmicos (ROI)", Icon: CircleDollarSign },
  { to: "/intelligence/occupancy-forecast", label: "Previsão de ocupação (slots)", Icon: LayoutGrid },
  { to: "/intelligence/route-optimize", label: "Roteirização ML (mapa)", Icon: MapPinned },
  { to: "/intelligence/pickup-fraud", label: "Fraude em pickups (ML)", Icon: ShieldAlert },
  { to: "/intelligence/partner-churn", label: "Churn parceiros logísticos", Icon: Users },
  { to: "/intelligence/ltv-scores", label: "LTV clientes (BG/NBD)", Icon: Wallet },
  { to: "/intelligence/feedback-nlp", label: "Feedback & NLP (NPS)", Icon: MessagesSquare },
];

export default function InteligenciaMenu({ isOpen, setOpen, atRiskCount, pathname, menuRef, buttonRef }) {
  return (
    <div ref={menuRef} className="nav-ops-dropdown" role="group" aria-label="Inteligência ML">
      <button
        ref={buttonRef}
        type="button"
        className="nav-link nav-link--intel nav-ops-toggle"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={isOpen}
      >
        <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
          <Brain size={16} aria-hidden />
          INTELIGÊNCIA
          {atRiskCount > 0 ? (
            <span className="nav-new-badge" title="Lockers em risco">
              {atRiskCount > 99 ? "99+" : atRiskCount}
            </span>
          ) : null}
        </span>
        {isOpen ? " ▲" : " ▼"}
      </button>
      {isOpen ? (
        <div className="nav-intelligence-panel" role="menu">
          {LINKS.map(({ to, label, Icon }) => {
            const active = pathname === to || pathname.startsWith(`${to}/`);
            return (
              <Link
                key={to}
                className={`nav-intelligence-item${active ? " nav-intelligence-item--active" : ""}`}
                to={to}
                onClick={() => setOpen(false)}
              >
                <Icon size={14} aria-hidden />
                <span>{label}</span>
              </Link>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}

