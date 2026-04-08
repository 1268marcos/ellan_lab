// 01_source/frontend/src/components/CardVirtualKeyboard.jsx
// 07/04/2026

import React, { useState, useEffect, useCallback, useRef } from "react";

const CARD_BRANDS = [
  // América do Norte
  { name: "VISA", pattern: /^4/, binRange: "4", length: [16, 19], cvvLength: 3, country: "Global", format: "4-4-4-4"  },
  { name: "MASTERCARD", pattern: /^5[1-5]/, binRange: "51-55", length: [16], cvvLength: 3, country: "Global", format: "4-4-4-4"  },
  { name: "MASTERCARD", pattern: /^2[2-7]/, binRange: "22-27", length: [16], cvvLength: 3, country: "Global", format: "4-4-4-4"  },
  { name: "AMEX", pattern: /^3[47]/, binRange: "34, 37", length: [15], cvvLength: 4, country: "Global", format: "4-6-5"  },
  { name: "DISCOVER", pattern: /^6(011|5|4[4-9]|22[1-9])/, binRange: "6011, 622, 64, 65", length: [16, 19], cvvLength: 3, country: "EUA", format: "4-4-4-4"  },
  { name: "DINERS", pattern: /^3(0[0-5]|[68])/, binRange: "30, 36, 38", length: [14], cvvLength: 3, country: "Global", format: "4-6-4"  },
  
  // Brasil
  { name: "ELO", pattern: /^(4011|4312|4389|4514|4576|5041|5067|5090|6277|6362|6363|6504|6505|6506|6507|6508|6509|6516|6550)/, binRange: "vários", length: [16], cvvLength: 3, country: "Brasil", format: "4-4-4-4"  },
  { name: "HIPERCARD", pattern: /^(3841|6062|6370|6372|6376|6388|6390|6399)/, binRange: "vários", length: [16], cvvLength: 3, country: "Brasil", format: "4-4-4-4"  },
  { name: "AURA", pattern: /^50[0-9]/, binRange: "500-509", length: [16], cvvLength: 3, country: "Brasil", format: "4-4-4-4"  },
  
  // China
  { name: "UNIONPAY", pattern: /^62/, binRange: "62", length: [16, 19], cvvLength: 3, country: "China", format: "4-4-4-4"  },
  { name: "UNIONPAY", pattern: /^81/, binRange: "81", length: [16, 19], cvvLength: 3, country: "China", format: "4-4-4-4"  },
  
  // Japão
  { name: "JCB", pattern: /^35(2[8-9]|[3-8][0-9])/, binRange: "3528-3589", length: [16], cvvLength: 3, country: "Japão", format: "4-4-4-4"  },
  
  // Europa
  { name: "MAESTRO", pattern: /^(50|56|57|58|6[0-9])/, binRange: "50, 56-58, 6", length: [16, 19], cvvLength: 3, country: "Europa", format: "4-4-4-4"  },
  
  // Índia
  { name: "RUPAY", pattern: /^(60|65|81|82|508|509)/, binRange: "60, 65, 81, 82, 508-509", length: [16], cvvLength: 3, country: "Índia", format: "4-4-4-4"  },
  
  // França
  { name: "CB", pattern: /^([1-9][0-9]{3})/, binRange: "variável", length: [16], cvvLength: 3, country: "França", format: "4-4-4-4"  },
  
  // Alemanha
  { name: "GIROCARD", pattern: /^6799/, binRange: "6799", length: [16, 18, 19], cvvLength: 3, country: "Alemanha", format: "4-4-4-4"  },
  
  // Austrália
  { name: "EFTPOS", pattern: /^(60|61|62|63|64|65)/, binRange: "60-65", length: [16], cvvLength: 3, country: "Austrália", format: "4-4-4-4"  },
  
  // Canadá
  { name: "INTERAC", pattern: /^45/, binRange: "45", length: [16], cvvLength: 3, country: "Canadá", format: "4-4-4-4"  },
  
  // Outros
  { name: "UATP", pattern: /^1/, binRange: "1", length: [15], cvvLength: 4, country: "Global", format: "4-6-5"  },
];


const formatCardNumber = (value, brand = null) => {
  const cleaned = value.replace(/\D/g, "");
  if (!cleaned) return "";
  
  // Determina o formato baseado na bandeira
  let format = "4-4-4-4";
  let maxLength = 16;
  
  if (brand) {
    format = brand.format;
    maxLength = Math.max(...brand.length);
  } else {
    // Detecta bandeira pelo padrão
    for (const b of CARD_BRANDS) {
      if (b.pattern.test(cleaned)) {
        format = b.format;
        maxLength = Math.max(...b.length);
        break;
      }
    }
  }
  
  // Aplica o formato específico
  if (format === "4-6-5") {
    // AMEX: 4-6-5
    const parts = [];
    if (cleaned.length >= 4) parts.push(cleaned.substring(0, 4));
    if (cleaned.length >= 10) parts.push(cleaned.substring(4, 10));
    if (cleaned.length >= 15) parts.push(cleaned.substring(10, 15));
    else if (cleaned.length > 4) parts.push(cleaned.substring(4));
    return parts.join(" ");
  } else if (format === "4-6-4") {
    // DINERS: 4-6-4
    const parts = [];
    if (cleaned.length >= 4) parts.push(cleaned.substring(0, 4));
    if (cleaned.length >= 10) parts.push(cleaned.substring(4, 10));
    if (cleaned.length >= 14) parts.push(cleaned.substring(10, 14));
    else if (cleaned.length > 4) parts.push(cleaned.substring(4));
    return parts.join(" ");
  } else {
    // Padrão 4-4-4-4
    const groups = [];
    for (let i = 0; i < cleaned.length && i < maxLength; i += 4) {
      groups.push(cleaned.slice(i, i + 4));
    }
    // Se tiver mais de 16 dígitos (ex: 19), adiciona o restante
    if (cleaned.length > 16 && maxLength > 16) {
      groups.push(cleaned.slice(16, maxLength));
    }
    return groups.join(" ");
  }
};


const detectCardBrand = (cardNumber) => {
  const cleaned = cardNumber.replace(/\D/g, "");
  if (!cleaned) return null;
  
  for (const brand of CARD_BRANDS) {
    if (brand.pattern.test(cleaned)) {
      return brand;
    }
  }
  return null;
};


const getCardBrandColor = (brand) => {
  const colors = {
    VISA: "#1a73e8", MASTERCARD: "#eb001b", AMEX: "#006fcf",
    DISCOVER: "#ff6000", DINERS: "#0079c1", ELO: "#ff6600",
    HIPERCARD: "#b31b1b", AURA: "#f39c12", UNIONPAY: "#e60012",
    JCB: "#1d9a3a", MAESTRO: "#0099cc", RUPAY: "#6f42c1",
    CB: "#0055a5", GIROCARD: "#ffcc00", EFTPOS: "#00a3ad",
    INTERAC: "#8a2be2", UATP: "#8b572a"
  };
  return colors[brand] || "#6c757d";
};


const CardVirtualKeyboard = ({ value, onChange, onClose, isOpen }) => {
  const [inputValue, setInputValue] = useState("");
  const [cardBrand, setCardBrand] = useState(null);
  const previousValueRef = useRef(value);

  useEffect(() => {
    if (isOpen) {
      // Quando abre, formata o valor existente
      const brand = detectCardBrand(value);
      setCardBrand(brand);
      const formatted = formatCardNumber(value, brand);
      setInputValue(formatted);
      previousValueRef.current = value;
    }
  }, [value, isOpen]);

  const handleKeyPress = useCallback((key) => {
    // Obtém o número puro atual
    const currentClean = inputValue.replace(/\D/g, "");
    let newClean = currentClean;
    
    switch (key) {
      case "backspace":
        newClean = newClean.slice(0, -1);
        break;
      case "clear_all":
        newClean = "";
        break;
      default:
        // Verifica o limite máximo baseado na bandeira
        const maxLength = cardBrand ? Math.max(...cardBrand.length) : 19;
        if (newClean.length < maxLength) {
          newClean += key;
        }
        break;
    }
    
    // Detecta a bandeira com o novo número
    const newBrand = detectCardBrand(newClean);
    setCardBrand(newBrand);
    
    // Formata o número com a bandeira correta
    const formatted = formatCardNumber(newClean, newBrand);
    setInputValue(formatted);
    
    // Chama o onChange com o número limpo (sem formatação)
    onChange(formatted);
  }, [inputValue, cardBrand, onChange]);

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
            <span style={keyboardTitle}>💳 Teclado Virtual - Número do Cartão</span>
            {cardBrand && (
              <span style={cardBrandBadge(getCardBrandColor(cardBrand.name))}>
                {cardBrand.name}
                <span style={countryFlag}>{cardBrand.country}</span>
              </span>
            )}
          </div>
          <button onClick={onClose} style={closeButton}>Concluir ✓</button>
        </div>

        <div style={inputContainer}>
          <div style={inputWrapper}>
            <input
              type="text"
              value={inputValue}
              placeholder="0000 0000 0000 0000"
              style={inputField}
              readOnly
              inputMode="none"
            />
            {cardBrand && (
              <div style={cardBrandIcon(getCardBrandColor(cardBrand.name))}>
                {cardBrand.name}
              </div>
            )}
          </div>
        </div>

        {cardBrand && (
          <div style={cardInfoContainer}>
            <span style={cardInfoText}>
              💳 Bandeira: {cardBrand.name} ({cardBrand.country})
              {cardBrand.cvvLength === 4 && " • CVV de 4 dígitos"}
              {cardBrand.format && ` • Formato: ${cardBrand.format}`}
              {cardBrand.length && ` • Máximo: ${Math.max(...cardBrand.length)} dígitos`}
            </span>
          </div>
        )}

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

        <div style={keyboardFooter}>
          <button onClick={onClose} style={footerCloseButton}>Concluir ✓</button>
        </div>
      </div>
    </div>
  );
};

// Estilos
const keyboardOverlay = {
  position: "fixed", bottom: 0, left: 0, right: 0,
  backgroundColor: "rgba(0, 0, 0, 0.95)", zIndex: 20000,
  padding: "16px", animation: "slideUp 0.3s ease-out"
};

const keyboardContainer = {
  maxWidth: "500px", margin: "0 auto", backgroundColor: "#1a1f2a",
  borderRadius: "20px", padding: "20px", border: "1px solid rgba(255, 255, 255, 0.1)"
};

const keyboardHeader = {
  display: "flex", justifyContent: "space-between", alignItems: "center",
  marginBottom: "16px", paddingBottom: "12px", borderBottom: "1px solid rgba(255, 255, 255, 0.1)"
};

const keyboardTitle = { fontSize: "16px", fontWeight: 600, color: "#f5f7fa" };

const cardBrandBadge = (color) => ({
  marginLeft: "12px", padding: "4px 10px", backgroundColor: color,
  borderRadius: "20px", fontSize: "11px", fontWeight: 700, color: "#fff",
  display: "inline-flex", alignItems: "center", gap: "6px"
});

const countryFlag = { fontSize: "9px", opacity: 0.9, marginLeft: "4px" };
const closeButton = { padding: "8px 20px", backgroundColor: "#1f7a3f", color: "white", border: "none", borderRadius: "10px", cursor: "pointer", fontSize: "14px", fontWeight: 600 };
const inputContainer = { marginBottom: "16px" };
const inputWrapper = { position: "relative", display: "flex", alignItems: "center" };
const inputField = { width: "100%", padding: "16px", fontSize: "20px", backgroundColor: "#0b0f14", border: "2px solid rgba(255, 255, 255, 0.15)", borderRadius: "12px", color: "#f5f7fa", outline: "none", textAlign: "center", fontFamily: "monospace", letterSpacing: "2px", fontWeight: 600 };
const cardBrandIcon = (color) => ({ position: "absolute", right: "12px", padding: "4px 8px", backgroundColor: color, borderRadius: "8px", fontSize: "11px", fontWeight: 700, color: "#fff" });
const cardInfoContainer = { marginBottom: "16px", padding: "8px", backgroundColor: "rgba(27, 88, 131, 0.2)", borderRadius: "8px", textAlign: "center" };
const cardInfoText = { fontSize: "12px", color: "#b0b8c5" };
const keyboardLayout = { display: "flex", flexDirection: "column", gap: "10px", marginBottom: "16px" };
const keyboardRow = { display: "flex", justifyContent: "center", gap: "12px" };
const keyButton = { flex: 1, padding: "18px 12px", backgroundColor: "#2c3440", border: "1px solid rgba(255, 255, 255, 0.1)", borderRadius: "12px", color: "#f5f7fa", cursor: "pointer", fontSize: "22px", fontWeight: 600, maxWidth: "100px" };
const clearAllButton = { backgroundColor: "#b87c2e", fontSize: "14px", fontWeight: 600 };
const backspaceButton = { backgroundColor: "#a54c3a", fontSize: "16px", fontWeight: 600 };
const keyboardFooter = { paddingTop: "12px", borderTop: "1px solid rgba(255, 255, 255, 0.1)", textAlign: "center" };
const footerCloseButton = { padding: "12px 32px", backgroundColor: "#1f7a3f", color: "white", border: "none", borderRadius: "12px", cursor: "pointer", fontSize: "16px", fontWeight: 600, width: "100%" };

if (typeof document !== "undefined") {
  const styleSheet = document.createElement("style");
  styleSheet.textContent = `@keyframes slideUp { from { transform: translateY(100%); } to { transform: translateY(0); } }`;
  if (!document.head.querySelector("#card-keyboard-styles")) {
    styleSheet.id = "card-keyboard-styles";
    document.head.appendChild(styleSheet);
  }
}

export default CardVirtualKeyboard;


