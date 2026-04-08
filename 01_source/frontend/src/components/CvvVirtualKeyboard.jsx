// 01_source/frontend/src/components/CvvVirtualKeyboard.jsx
import React, { useState, useEffect, useCallback } from "react";

const CvvVirtualKeyboard = ({ value, onChange, onClose, isOpen, cardBrand = null }) => {
  const [inputValue, setInputValue] = useState(value || "");
  const [displayValue, setDisplayValue] = useState("");
  
  const cvvLength = cardBrand?.cvvLength === 4 ? 4 : 3;

  useEffect(() => {
    if (isOpen) {
      setInputValue(value || "");
      updateDisplayValue(value || "");
    }
  }, [value, isOpen, cvvLength]);

  const updateDisplayValue = (rawValue) => {
    const len = rawValue.length;
    if (len === 0) {
      // Mostra placeholders vazios
      setDisplayValue("_".repeat(cvvLength));
    } else {
      // Mostra * para dígitos já digitados e _ para os que faltam
      const stars = "*".repeat(len);
      const underscores = "_".repeat(cvvLength - len);
      setDisplayValue(stars + underscores);
    }
  };

  const handleKeyPress = useCallback((key) => {
    let newValue = inputValue.replace(/\D/g, "");
    
    switch (key) {
      case "backspace":
        newValue = newValue.slice(0, -1);
        break;
      case "clear_all":
        newValue = "";
        break;
      default:
        if (newValue.length < cvvLength) {
          newValue += key;
        }
        break;
    }
    
    setInputValue(newValue);
    updateDisplayValue(newValue);
    onChange(newValue);
  }, [inputValue, cvvLength, onChange]);

  const keyboardRows = [
    ["1", "2", "3"],
    ["4", "5", "6"],
    ["7", "8", "9"],
    ["clear_all", "0", "backspace"]
  ];

  if (!isOpen) return null;

  return (
    <div style={keyboardOverlay}>
      <div style={keyboardContainer}>
        <div style={keyboardHeader}>
          <div>
            <span style={keyboardTitle}>
              🔐 Teclado Virtual - CVV
              {cardBrand && (
                <span style={cvvLengthBadge}>
                  {cvvLength} dígitos
                </span>
              )}
            </span>
          </div>
          <button onClick={onClose} style={closeButton}>
            Concluir ✓
          </button>
        </div>

        {/* Display do CVV com máscara */}
        <div style={cvvDisplayContainer}>
          <div style={cvvDisplayWrapper}>
            <div style={cvvLabel}>CVV / CVC</div>
            <div style={cvvDisplayBox}>
              <span style={cvvDisplayValue}>
                {displayValue.split('').map((char, idx) => (
                  <span key={idx} style={cvvCharStyle(char)}>
                    {char}
                  </span>
                ))}
              </span>
            </div>
            <div style={cvvHint}>
              {cardBrand?.cvvLength === 4 
                ? "Cartão American Express tem 4 dígitos no CVV" 
                : "Os 3 dígitos localizados no verso do cartão"}
            </div>
          </div>
        </div>

        {/* Keyboard */}
        <div style={keyboardLayout}>
          {keyboardRows.map((row, rowIndex) => (
            <div key={rowIndex} style={keyboardRow}>
              {row.map((key) => {
                let displayText = key;
                let buttonStyle = { ...keyButton };
                
                if (key === "clear_all") {
                  displayText = "Limpar Tudo";
                  buttonStyle = { ...keyButton, ...clearAllButton };
                } else if (key === "backspace") {
                  displayText = "⌫ Apagar";
                  buttonStyle = { ...keyButton, ...backspaceButton };
                }
                
                return (
                  <button
                    key={key}
                    onClick={() => handleKeyPress(key)}
                    style={buttonStyle}
                    onMouseDown={(e) => e.preventDefault()}
                  >
                    {displayText}
                  </button>
                );
              })}
            </div>
          ))}
        </div>

        {/* Dicas de segurança */}
        <div style={securityTipsContainer}>
          <div style={securityTipsTitle}>🔒 Dica de segurança:</div>
          <div style={securityTipsText}>
            O CVV é um código de segurança único. Nunca compartilhe com ninguém.
          </div>
        </div>

        <div style={keyboardFooter}>
          <button onClick={onClose} style={footerCloseButton}>
            Concluir ✓
          </button>
        </div>
      </div>
    </div>
  );
};

// Estilos
const keyboardOverlay = {
  position: "fixed",
  bottom: 0,
  left: 0,
  right: 0,
  backgroundColor: "rgba(0, 0, 0, 0.95)",
  zIndex: 20000,
  padding: "16px",
  animation: "slideUp 0.3s ease-out"
};

const keyboardContainer = {
  maxWidth: "500px",
  margin: "0 auto",
  backgroundColor: "#1a1f2a",
  borderRadius: "20px",
  padding: "20px",
  border: "1px solid rgba(255, 255, 255, 0.1)"
};

const keyboardHeader = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  marginBottom: "20px",
  paddingBottom: "12px",
  borderBottom: "1px solid rgba(255, 255, 255, 0.1)"
};

const keyboardTitle = {
  fontSize: "16px",
  fontWeight: 600,
  color: "#f5f7fa",
  display: "flex",
  alignItems: "center",
  gap: "10px"
};

const cvvLengthBadge = {
  padding: "4px 8px",
  backgroundColor: "rgba(255, 193, 7, 0.2)",
  borderRadius: "20px",
  fontSize: "11px",
  color: "#ffc107"
};

const closeButton = {
  padding: "8px 20px",
  backgroundColor: "#1f7a3f",
  color: "white",
  border: "none",
  borderRadius: "10px",
  cursor: "pointer",
  fontSize: "14px",
  fontWeight: 600
};

const cvvDisplayContainer = {
  marginBottom: "24px",
  padding: "20px",
  backgroundColor: "rgba(0, 0, 0, 0.3)",
  borderRadius: "16px",
  border: "1px solid rgba(255, 255, 255, 0.1)"
};

const cvvDisplayWrapper = {
  textAlign: "center"
};

const cvvLabel = {
  fontSize: "12px",
  color: "#8b95a5",
  marginBottom: "12px",
  textTransform: "uppercase",
  letterSpacing: "1px"
};

const cvvDisplayBox = {
  display: "inline-block",
  padding: "20px 30px",
  backgroundColor: "#0b0f14",
  borderRadius: "12px",
  border: "2px solid rgba(255, 255, 255, 0.15)",
  marginBottom: "12px"
};

const cvvDisplayValue = {
  fontSize: "32px",
  fontWeight: 700,
  fontFamily: "monospace",
  letterSpacing: "8px",
  display: "flex",
  gap: "8px",
  justifyContent: "center"
};

const cvvCharStyle = (char) => ({
  display: "inline-block",
  width: "40px",
  textAlign: "center",
  color: char === "*" ? "#10b981" : char === "_" ? "#6c757d" : "#f5f7fa",
  fontSize: char === "_" ? "28px" : "32px",
  fontWeight: 700
});

const cvvHint = {
  fontSize: "12px",
  color: "#8b95a5"
};

const keyboardLayout = {
  display: "flex",
  flexDirection: "column",
  gap: "10px",
  marginBottom: "16px"
};

const keyboardRow = {
  display: "flex",
  justifyContent: "center",
  gap: "12px"
};

const keyButton = {
  flex: 1,
  padding: "18px 12px",
  backgroundColor: "#2c3440",
  border: "1px solid rgba(255, 255, 255, 0.1)",
  borderRadius: "12px",
  color: "#f5f7fa",
  cursor: "pointer",
  fontSize: "22px",
  fontWeight: 600,
  maxWidth: "100px"
};

const clearAllButton = {
  backgroundColor: "#b87c2e",
  fontSize: "14px",
  fontWeight: 600
};

const backspaceButton = {
  backgroundColor: "#a54c3a",
  fontSize: "16px",
  fontWeight: 600
};

const securityTipsContainer = {
  marginBottom: "16px",
  padding: "12px",
  backgroundColor: "rgba(255, 193, 7, 0.1)",
  borderRadius: "10px",
  border: "1px solid rgba(255, 193, 7, 0.2)"
};

const securityTipsTitle = {
  fontSize: "12px",
  color: "#ffc107",
  marginBottom: "6px",
  fontWeight: 600
};

const securityTipsText = {
  fontSize: "11px",
  color: "#b0b8c5",
  lineHeight: 1.4
};

const keyboardFooter = {
  paddingTop: "12px",
  borderTop: "1px solid rgba(255, 255, 255, 0.1)",
  textAlign: "center"
};

const footerCloseButton = {
  padding: "12px 32px",
  backgroundColor: "#1f7a3f",
  color: "white",
  border: "none",
  borderRadius: "12px",
  cursor: "pointer",
  fontSize: "16px",
  fontWeight: 600,
  width: "100%"
};

// Adiciona animação CSS
if (typeof document !== "undefined") {
  const styleSheet = document.createElement("style");
  styleSheet.textContent = `
    @keyframes slideUp {
      from { transform: translateY(100%); }
      to { transform: translateY(0); }
    }
  `;
  if (!document.head.querySelector("#cvv-keyboard-styles")) {
    styleSheet.id = "cvv-keyboard-styles";
    document.head.appendChild(styleSheet);
  }
}

export default CvvVirtualKeyboard;