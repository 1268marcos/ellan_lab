
/** Estilos alinhados a páginas OPS (ex.: OpsIntegrationOrdersPartnerLookupPage). */

export const pageStyle = {
  width: "100%",
  padding: 24,
  boxSizing: "border-box",
  color: "#E2E8F0",
  fontFamily: "system-ui, sans-serif",
  display: "grid",
  gap: 12,
};

export const cardStyle = {
  background: "#111827",
  border: "1px solid #334155",
  borderRadius: 16,
  padding: 16,
};

export const mutedStyle = { color: "#94A3B8", fontSize: 14, lineHeight: 1.45, marginBottom: 4 };

export const filtersStyle = {
  display: "grid",
  gap: 10,
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  marginBottom: 10,
};

export const labelStyle = { display: "grid", gap: 4, fontSize: 12, color: "#CBD5E1" };

export const inputStyle = {
  padding: "8px 10px",
  borderRadius: 8,
  border: "1px solid #475569",
  background: "#020617",
  color: "#E2E8F0",
};

export const actionsStyle = { display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 };

export const errorStyle = { color: "#f87171", fontSize: 14, marginTop: 8 };

export const metaLineStyle = { fontSize: 13, color: "#94A3B8", marginTop: 6 };

export const navRowStyle = {
  display: "flex",
  flexWrap: "wrap",
  gap: 8,
  marginBottom: 12,
  alignItems: "center",
};

export const navLinkStyle = {
  padding: "6px 10px",
  borderRadius: 8,
  border: "1px solid rgba(96,165,250,0.45)",
  background: "rgba(96,165,250,0.12)",
  color: "#93C5FD",
  textDecoration: "none",
  fontWeight: 600,
  fontSize: 12,
};

export const navLinkMutedStyle = {
  ...navLinkStyle,
  borderColor: "rgba(148,163,184,0.35)",
  background: "rgba(15,23,42,0.6)",
  color: "#CBD5E1",
};

export const tableWrapStyle = {
  overflow: "auto",
  maxHeight: "65vh",
  marginTop: 12,
  border: "1px solid #1E293B",
  borderRadius: 10,
  background: "#020617",
};

export const tableStyle = { width: "100%", borderCollapse: "collapse", fontSize: 12 };

export const thStyle = {
  textAlign: "left",
  borderBottom: "1px solid #334155",
  padding: "8px 10px",
  color: "#94A3B8",
  fontWeight: 700,
};

export const tdStyle = { padding: "8px 10px", borderTop: "1px solid #1E293B", verticalAlign: "top" };

export const monoTdStyle = {
  ...tdStyle,
  fontFamily: "ui-monospace, monospace",
  fontSize: 11,
};

export const preJsonStyle = {
  marginTop: 12,
  background: "#020617",
  border: "1px solid #1E293B",
  borderRadius: 10,
  padding: 12,
  overflow: "auto",
  fontSize: 12,
  whiteSpace: "pre-wrap",
};

