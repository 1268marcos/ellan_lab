/** Estilos compartilhados das paginas OPS CRUD (shell escuro alinhado a OpsLockerCreatePage). */

export const pageStyle = {
  width: "100%",
  maxWidth: "none",
  padding: 24,
  boxSizing: "border-box",
  color: "#f5f7fa",
  fontFamily: "system-ui, sans-serif",
};

export const cardStyle = {
  width: "100%",
  background: "#11161c",
  border: "1px solid rgba(255,255,255,0.10)",
  borderRadius: 16,
  padding: 16,
  boxSizing: "border-box",
};

export const crossShortcutLinkStyle = {
  padding: "8px 12px",
  borderRadius: 10,
  border: "1px solid rgba(96,165,250,0.55)",
  background: "rgba(96,165,250,0.15)",
  color: "#bfdbfe",
  textDecoration: "none",
  fontWeight: 700,
  fontSize: 13,
};

export const mutedTextStyle = {
  color: "rgba(245, 247, 250, 0.8)",
  marginTop: 8,
  marginBottom: 0,
};

export const healthLocalFilterRowStyle = {
  marginTop: 10,
  marginBottom: 8,
  display: "grid",
  gap: 8,
  gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
  alignItems: "end",
};

export const healthLocalFilterFieldStyle = {
  display: "grid",
  gap: 4,
  fontSize: 12,
  color: "#cbd5e1",
};

export const healthLocalFilterInputStyle = {
  width: "100%",
  padding: "8px 10px",
  borderRadius: 10,
  border: "1px solid rgba(148,163,184,0.5)",
  background: "#0b0f14",
  color: "#f5f7fa",
  boxSizing: "border-box",
};

export const toolbarStyle = {
  display: "flex",
  gap: 10,
  alignItems: "flex-end",
  flexWrap: "wrap",
};

export const buttonGhostStyle = {
  padding: "8px 12px",
  cursor: "pointer",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.16)",
  background: "transparent",
  color: "#e2e8f0",
  fontWeight: 600,
};

export const buttonPrimaryStyle = {
  ...buttonGhostStyle,
  border: "1px solid rgba(34,197,94,0.55)",
  background: "rgba(22,101,52,0.35)",
  color: "#bbf7d0",
};

export const opsSanityCardStyle = {
  marginTop: 6,
  borderRadius: 12,
  border: "1px solid rgba(59,130,246,0.45)",
  background: "rgba(30,58,138,0.2)",
  padding: 12,
  display: "grid",
  gap: 10,
};

export const summary24hHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 8,
  flexWrap: "wrap",
};

export const summary24hHintStyle = {
  color: "rgba(191,219,254,0.95)",
  fontSize: 11,
};

export const criticalBannerStyle = {
  borderRadius: 10,
  border: "1px solid rgba(248,113,113,0.72)",
  background: "linear-gradient(180deg, rgba(127,29,29,0.58) 0%, rgba(127,29,29,0.3) 100%)",
  color: "#fecaca",
  padding: "10px 12px",
  fontWeight: 700,
  fontSize: 13,
};

export const okBannerStyle = {
  ...summary24hHintStyle,
  color: "#86efac",
  fontWeight: 600,
  marginTop: 8,
};

export const apiKeyBannerStyle = {
  ...summary24hHintStyle,
  wordBreak: "break-all",
  padding: 8,
  borderRadius: 8,
  border: "1px solid rgba(251,191,36,0.5)",
  background: "rgba(120,53,15,0.25)",
};

export const tableStyle = { width: "100%", borderCollapse: "collapse", minWidth: 520, fontSize: 12 };
export const thStyle = { textAlign: "left", borderBottom: "1px solid #444", padding: 8, color: "#cbd5e1" };
export const tdStyle = { padding: 8, borderTop: "1px solid #333", color: "#e2e8f0", verticalAlign: "top" };

export const tabButtonStyle = (active) => ({
  padding: "8px 14px",
  borderRadius: 10,
  border: active ? "1px solid rgba(96,165,250,0.7)" : "1px solid rgba(255,255,255,0.14)",
  background: active ? "rgba(30,58,138,0.45)" : "transparent",
  color: active ? "#bfdbfe" : "#94a3b8",
  fontWeight: 600,
  cursor: "pointer",
});
