export const pageStyle = {
  minHeight: "100vh",
  background: "linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)",
  padding: "24px 16px",
};

export const containerStyle = {
  maxWidth: 960,
  margin: "0 auto",
};

export const pageHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "flex-start",
  gap: 16,
  marginBottom: 20,
  flexWrap: "wrap",
};

export const titleStyle = {
  margin: "0 0 8px 0",
  fontSize: 32,
  fontWeight: 800,
  color: "#1a202c",
};

export const subtitleStyle = {
  margin: 0,
  fontSize: 16,
  color: "#4a5568",
  lineHeight: 1.5,
};

export const newOrderButtonStyle = {
  textDecoration: "none",
  padding: "12px 20px",
  borderRadius: 12,
  background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  color: "white",
  fontWeight: 700,
  fontSize: 14,
  boxShadow: "0 4px 6px -1px rgba(102, 126, 234, 0.4)",
  whiteSpace: "nowrap",
};

export const filterLeftStyle = {
  display: "flex",
  alignItems: "center",
  gap: 10,
  flexWrap: "wrap",
};

export const filterIconStyle = {
  fontSize: 18,
};

export const filterSelectStyle = {
  padding: "10px 14px",
  borderRadius: 10,
  border: "1px solid #e2e8f0",
  background: "#f7fafc",
  color: "#1a202c",
  fontSize: 14,
  fontWeight: 600,
  outline: "none",
};

export const chipsWrapStyle = {
  width: "100%",
  display: "flex",
  gap: 8,
  flexWrap: "wrap",
  marginTop: 6,
};

export const statusChipStyle = {
  padding: "8px 10px",
  borderRadius: 999,
  border: "1px solid #cbd5e1",
  background: "#f8fafc",
  color: "#334155",
  fontSize: 12,
  fontWeight: 600,
  cursor: "pointer",
};

export const statusChipActiveStyle = {
  border: "1px solid #4f46e5",
  background: "#e0e7ff",
  color: "#312e81",
};

export const emptyStateStyle = {
  textAlign: "center",
  padding: 48,
  background: "white",
  borderRadius: 16,
  border: "1px solid #e2e8f0",
};

export const emptyStateIconStyle = {
  fontSize: 56,
  marginBottom: 14,
};

export const emptyStateTitleStyle = {
  margin: "0 0 8px 0",
  fontSize: 20,
  fontWeight: 700,
  color: "#1a202c",
};

export const emptyStateTextStyle = {
  margin: "0 0 22px 0",
  fontSize: 14,
  color: "#718096",
};

export const emptyStateButtonStyle = {
  display: "inline-block",
  textDecoration: "none",
  padding: "12px 24px",
  borderRadius: 12,
  background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  color: "white",
  fontWeight: 700,
  fontSize: 14,
};

export const skeletonListStyle = {
  display: "grid",
  gap: 12,
};

export const skeletonCardStyle = {
  padding: 16,
  borderRadius: 16,
  border: "1px solid #e2e8f0",
  background: "white",
};

export const skeletonHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  marginBottom: 12,
  gap: 10,
};

export const skeletonBodyStyle = {
  display: "grid",
  gap: 10,
};

export const skeletonLineStyle = {
  height: 14,
  borderRadius: 8,
  background: "linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%)",
  backgroundSize: "200% 100%",
  animation: "shimmer 1.5s infinite",
};

export const skeletonLineShortStyle = {
  ...skeletonLineStyle,
  width: 180,
};

export const skeletonBadgeStyle = {
  ...skeletonLineStyle,
  width: 90,
};
