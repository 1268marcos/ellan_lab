// 01_source/frontend/src/features/locker-dashboard/components/Carousel.jsx

import React from "react";

const btnSmall = {
  padding: "7px 10px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.2)",
  background: "rgba(255,255,255,0.08)",
  color: "white",
  cursor: "pointer",
};

export default function Carousel({ pages, activeIndex, onPrev, onNext, onGo }) {
  return (
    <div style={{ display: "grid", gap: 8 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <button onClick={onPrev} style={btnSmall}>
          ◀
        </button>
        <div style={{ fontWeight: 700 }}>
          Grupo {activeIndex + 1} / {pages}
        </div>
        <button onClick={onNext} style={btnSmall}>
          ▶
        </button>
      </div>

      <div style={{ display: "flex", gap: 6, justifyContent: "center" }}>
        {Array.from({ length: pages }).map((_, index) => (
          <button
            key={index}
            onClick={() => onGo(index)}
            style={{
              width: 10,
              height: 10,
              borderRadius: 999,
              border: "none",
              cursor: "pointer",
              background: index === activeIndex ? "white" : "rgba(255,255,255,0.35)",
            }}
            aria-label={`Ir para grupo ${index + 1}`}
          />
        ))}
      </div>
    </div>
  );
}