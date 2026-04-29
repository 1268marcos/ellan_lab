import React from "react";

export default function FiscalPageLayout({ children }) {
  return (
    <div className="fiscal-theme-shell">
      <div className="fiscal-theme-content">{children}</div>
    </div>
  );
}
