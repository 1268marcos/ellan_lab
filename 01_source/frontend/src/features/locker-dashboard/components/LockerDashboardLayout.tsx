import React from "react";
import type { LockerDashboardLayoutProps } from "./lockerDashboardPanelProps";

export default function LockerDashboardLayout({ children }: LockerDashboardLayoutProps) {
  return (
    <main
      style={{
        minHeight: "100vh",
        background: "linear-gradient(135deg, #141927 0%, #1c2333 100%)",
        color: "white",
        padding: "20px 18px 32px",
      }}
    >
      <div
        style={{
          maxWidth: 1680,
          margin: "0 auto",
          display: "grid",
          gap: 20,
        }}
      >
        {children}
      </div>
    </main>
  );
}