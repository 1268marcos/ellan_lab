// 01_source/frontend/src/components/PickupCodeVirtualKeyboard.jsx
// 16/04/2026
// UX/CX melhorada: ação principal no rodapé, topo sem conflito, estado visual mais claro
// UX/CX melhorada: uso de toast ao fechar

import React, { useEffect, useMemo, useRef, useState } from "react";

const keyboardRows = [
  ["1", "2", "3"],
  ["4", "5", "6"],
  ["7", "8", "9"],
  ["clear", "0", "backspace"],
];

export default function PickupCodeVirtualKeyboard({
  isOpen,
  value,
  onChange,
  onClose,
  onDiscardIncompleteCode,
  codeLength = 6,
}) {
  const [internal, setInternal] = useState("");

  useEffect(() => {
    if (isOpen) {
      setInternal(String(value || ""));
    }
  }, [isOpen, value]);




  const digitsFilled = useMemo(() => internal.length, [internal]);
  const isComplete = digitsFilled === Number(codeLength || 0);

  //const [internal, setInternal] = useState("");
  const [toastMessage, setToastMessage] = useState("");
  const toastTimerRef = useRef(null);
  
  useEffect(() => {
    return () => {
        if (toastTimerRef.current) {
        clearTimeout(toastTimerRef.current);
        }
    };
  }, []);



  function showToast(message) {
    setToastMessage(message);

    if (toastTimerRef.current) {
        clearTimeout(toastTimerRef.current);
    }

    toastTimerRef.current = setTimeout(() => {
        setToastMessage("");
        toastTimerRef.current = null;
    }, 2200);
  }


  function updateValue(next) {
    setInternal(next);
    onChange(next);
  }

  function handleKey(key) {
    let next = internal;

    if (key === "backspace") {
      next = next.slice(0, -1);
    } else if (key === "clear") {
      next = "";
    } else {
      if (next.length >= codeLength) return;
      next = next + key;
    }

    updateValue(next);
  }


  function handleClose() {
    const expectedLength = Number(codeLength || 0);
    const currentLength = internal.length;
    const isComplete = currentLength === expectedLength;

    if (!isComplete) {
        if (currentLength > 0) {
        setInternal("");
        onChange("");

        if (onDiscardIncompleteCode) {
            onDiscardIncompleteCode({
            enteredLength: currentLength,
            expectedLength,
            message: "Código incompleto descartado.",
            });
        }
        }

        onClose();
        return;
    }

    onClose();
  }






  function handleConfirm() {
    if (!isComplete) return;
    onClose();
  }

  if (!isOpen) return null;






  return (
    <div style={overlay}>
      <div style={container}>
        <div style={header}>
          <div style={headerTextBlock}>
            <div style={title}>🔐 Código de Retirada</div>
            <div style={subtitle}>
              Digite os {codeLength} dígitos do código manual para liberar a retirada.
            </div>
          </div>

          <button onClick={handleClose} style={headerCloseBtn} type="button">
            ✕
          </button>
        </div>

        <div style={displayBox}>
          <input
            value={internal}
            readOnly
            style={displayInput}
            placeholder={"•".repeat(codeLength)}
            inputMode="none"
          />

          <div style={counterRow}>
            <div style={counter}>
              {digitsFilled} / {codeLength}
            </div>

            <div style={statusPill(isComplete)}>
              {isComplete ? "Código completo" : "Digite todos os dígitos"}
            </div>
          </div>

          <div style={progressTrack}>
            <div
              style={{
                ...progressFill,
                width: `${Math.min(100, (digitsFilled / codeLength) * 100)}%`,
              }}
            />
          </div>
        </div>


        {toastMessage ? (
        <div style={toastStyle}>
            {toastMessage}
        </div>
        ) : null}




        <div style={keyboard}>
          {keyboardRows.map((row, i) => (
            <div key={i} style={rowStyle}>
              {row.map((key) => (
                <button
                  key={key}
                  onClick={() => handleKey(key)}
                  style={getKeyStyle(key)}
                  type="button"
                >
                  {key === "backspace"
                    ? "⌫"
                    : key === "clear"
                    ? "Limpar"
                    : key}
                </button>
              ))}
            </div>
          ))}
        </div>

        <div style={footer}>
          <button onClick={handleClose} style={secondaryFooterBtn} type="button">
            Fechar
          </button>

          <button
            onClick={handleConfirm}
            disabled={!isComplete}
            style={{
              ...primaryFooterBtn,
              ...(isComplete ? {} : primaryFooterBtnDisabled),
            }}
            type="button"
          >
            {isComplete
              ? "Concluir e usar código ✓"
              : `Digite ${codeLength} dígitos`}
          </button>
        </div>
      </div>
    </div>
  );
}

/* estilos */
const overlay = {
  position: "fixed",
  inset: 0,
  background: "rgba(0,0,0,0.88)",
  zIndex: 9999,
  display: "flex",
  alignItems: "flex-end",
  justifyContent: "center",
  padding: 16,
  backdropFilter: "blur(4px)",
};

const container = {
  width: "100%",
  maxWidth: 440,
  background: "#1a1f2a",
  borderRadius: 20,
  padding: 16,
  border: "1px solid rgba(255, 255, 255, 0.1)",
  boxShadow: "0 20px 50px rgba(0,0,0,0.35)",
};

const header = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "flex-start",
  gap: 12,
  marginBottom: 14,
};

const headerTextBlock = {
  display: "grid",
  gap: 6,
  flex: 1,
};

const title = {
  fontSize: 18,
  fontWeight: 700,
  color: "#f5f7fa",
};

const subtitle = {
  fontSize: 13,
  color: "#b0b8c5",
  lineHeight: 1.4,
};

const headerCloseBtn = {
  minWidth: 40,
  height: 40,
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.12)",
  background: "rgba(255,255,255,0.06)",
  color: "#fff",
  fontSize: 18,
  cursor: "pointer",
};

const displayBox = {
  marginBottom: 14,
  display: "grid",
  gap: 10,
};

const displayInput = {
  width: "100%",
  padding: "16px 14px",
  fontSize: 28,
  backgroundColor: "#0b0f14",
  border: "2px solid rgba(255, 255, 255, 0.15)",
  borderRadius: "14px",
  color: "#f5f7fa",
  outline: "none",
  textAlign: "center",
  fontFamily: "monospace",
  letterSpacing: "6px",
  fontWeight: 700,
};

const counterRow = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 10,
};

const counter = {
  fontSize: 12,
  color: "#b0b8c5",
};

const statusPill = (complete) => ({
  fontSize: 12,
  fontWeight: 700,
  padding: "6px 10px",
  borderRadius: 999,
  color: complete ? "#d1fae5" : "#fde68a",
  background: complete ? "rgba(16, 185, 129, 0.18)" : "rgba(245, 158, 11, 0.16)",
  border: complete
    ? "1px solid rgba(16, 185, 129, 0.35)"
    : "1px solid rgba(245, 158, 11, 0.35)",
});

const progressTrack = {
  width: "100%",
  height: 8,
  borderRadius: 999,
  background: "rgba(255,255,255,0.08)",
  overflow: "hidden",
};

const progressFill = {
  height: "100%",
  borderRadius: 999,
  background: "linear-gradient(90deg, #1f7a3f, #32b768)",
  transition: "width 0.18s ease",
};

const keyboard = {
  display: "flex",
  flexDirection: "column",
  gap: 10,
  marginBottom: 16,
};

const rowStyle = {
  display: "flex",
  justifyContent: "center",
  gap: 10,
};

function getKeyStyle(key) {
  let bg = "#2c3440";
  let fontSize = 24;

  if (key === "clear") {
    bg = "#8c6b2b";
    fontSize = 15;
  }

  if (key === "backspace") {
    bg = "#8a3f34";
    fontSize = 20;
  }

  return {
    flex: 1,
    minHeight: 64,
    padding: "16px 12px",
    backgroundColor: bg,
    border: "1px solid rgba(255, 255, 255, 0.1)",
    borderRadius: "14px",
    color: "#f5f7fa",
    cursor: "pointer",
    fontSize,
    fontWeight: 700,
    maxWidth: "120px",
    boxShadow: "inset 0 -2px 0 rgba(0,0,0,0.18)",
  };
}

const footer = {
  display: "grid",
  gridTemplateColumns: "120px 1fr",
  gap: 10,
  paddingTop: 12,
  borderTop: "1px solid rgba(255,255,255,0.08)",
};

const secondaryFooterBtn = {
  minHeight: 52,
  padding: "12px 14px",
  backgroundColor: "rgba(255,255,255,0.06)",
  color: "#fff",
  border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: "12px",
  cursor: "pointer",
  fontSize: "15px",
  fontWeight: 600,
};

const primaryFooterBtn = {
  minHeight: 52,
  padding: "12px 18px",
  backgroundColor: "#1f7a3f",
  color: "white",
  border: "none",
  borderRadius: "12px",
  cursor: "pointer",
  fontSize: "16px",
  fontWeight: 700,
  width: "100%",
  boxShadow: "0 8px 18px rgba(31,122,63,0.28)",
};

const primaryFooterBtnDisabled = {
  backgroundColor: "rgba(255,255,255,0.10)",
  color: "rgba(255,255,255,0.5)",
  cursor: "not-allowed",
  boxShadow: "none",
};


const toastStyle = {
  marginBottom: 12,
  padding: "10px 12px",
  borderRadius: 12,
  background: "rgba(245, 158, 11, 0.16)",
  border: "1px solid rgba(245, 158, 11, 0.35)",
  color: "#fde68a",
  fontSize: 13,
  fontWeight: 600,
  textAlign: "center",
};

