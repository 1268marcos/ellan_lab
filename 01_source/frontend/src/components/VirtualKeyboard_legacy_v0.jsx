// 01_source/frontend/src/components/VirtualKeyboard.jsx
import React, { useState, useEffect, useCallback } from "react";

const POPULAR_DOMAINS = [
  { domain: "@gmail.com", country: "Brasil" },
  { domain: "@yahoo.com", country: "Brasil" },
  { domain: "@hotmail.com", country: "Brasil" },
  { domain: "@outlook.com", country: "Brasil" },
  { domain: "@uol.com.br", country: "Brasil" },
  { domain: "@bol.com.br", country: "Brasil" },
  { domain: "@globo.com", country: "Brasil" },
  { domain: "@sapo.pt", country: "Portugal" },
  { domain: "@outlook.pt", country: "Portugal" },
  { domain: "@clix.pt", country: "Portugal" },
  { domain: "@mail.pt", country: "Portugal" }
];

// Caracteres permitidos em email (RFC 5322 simplificado)
const ALLOWED_EMAIL_CHARS = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-@]$/;

const VirtualKeyboard = ({ value, onChange, onClose, isOpen }) => {
  const [inputValue, setInputValue] = useState(value);
  const [showDomainSuggestions, setShowDomainSuggestions] = useState(false);
  const [filteredDomains, setFilteredDomains] = useState(POPULAR_DOMAINS);
  const [cursorPosition, setCursorPosition] = useState(value.length);

  useEffect(() => {
    setInputValue(value);
    setCursorPosition(value.length);
  }, [value]);

  // Valida se o caractere é permitido em email
  const isValidEmailChar = (char) => {
    // Não permite espaços
    if (char === " ") return false;
    // Permite apenas caracteres válidos para email
    return ALLOWED_EMAIL_CHARS.test(char);
  };

  const handleKeyPress = useCallback((key) => {
    let newValue = inputValue;
    let newCursorPos = cursorPosition;

    switch (key) {
      case "backspace":
        if (cursorPosition > 0) {
          newValue = inputValue.slice(0, cursorPosition - 1) + inputValue.slice(cursorPosition);
          newCursorPos = cursorPosition - 1;
        }
        break;
      
      case "delete":
        if (cursorPosition < inputValue.length) {
          newValue = inputValue.slice(0, cursorPosition) + inputValue.slice(cursorPosition + 1);
          newCursorPos = cursorPosition;
        }
        break;
      
      case "clear":
        newValue = "";
        newCursorPos = 0;
        setShowDomainSuggestions(false);
        break;
      
      case "clear_all":
        newValue = "";
        newCursorPos = 0;
        setShowDomainSuggestions(false);
        break;
      
      case "space":
        // Espaço não é permitido em email - ignorar
        return;
      
      case "left":
        if (cursorPosition > 0) {
          newCursorPos = cursorPosition - 1;
        }
        return;
      
      case "right":
        if (cursorPosition < inputValue.length) {
          newCursorPos = cursorPosition + 1;
        }
        return;
      
      default:
        // Verifica se o caractere é permitido
        if (isValidEmailChar(key)) {
          newValue = inputValue.slice(0, cursorPosition) + key + inputValue.slice(cursorPosition);
          newCursorPos = cursorPosition + 1;
        } else {
          // Caractere inválido - não faz nada
          return;
        }
    }

    // Atualiza sugestões de domínio
    if (newValue.includes("@")) {
      const [, domainPart = ""] = newValue.split("@");
      if (domainPart) {
        const filtered = POPULAR_DOMAINS.filter(domain => 
          domain.domain.toLowerCase().startsWith(`@${domainPart.toLowerCase()}`)
        );
        setFilteredDomains(filtered);
        setShowDomainSuggestions(true);
      } else {
        setShowDomainSuggestions(true);
      }
    } else {
      setShowDomainSuggestions(false);
    }

    setInputValue(newValue);
    setCursorPosition(newCursorPos);
    onChange(newValue);
  }, [inputValue, cursorPosition, onChange]);

  const handleDomainSelect = useCallback((domain) => {
    let newValue;
    let newCursorPos;
    
    if (inputValue.includes("@")) {
      // Substitui o domínio atual
      const localPart = inputValue.split("@")[0];
      newValue = localPart + domain;
      newCursorPos = newValue.length;
    } else {
      // Adiciona domínio no final
      newValue = inputValue + domain;
      newCursorPos = newValue.length;
    }
    
    setInputValue(newValue);
    setCursorPosition(newCursorPos);
    setShowDomainSuggestions(false);
    onChange(newValue);
  }, [inputValue, onChange]);

  const handleInputChange = (e) => {
    const newValue = e.target.value;
    // Remove espaços automaticamente
    const cleanedValue = newValue.replace(/\s/g, "");
    setInputValue(cleanedValue);
    setCursorPosition(cleanedValue.length);
    onChange(cleanedValue);
    
    // Atualiza sugestões
    if (cleanedValue.includes("@")) {
      setShowDomainSuggestions(true);
    } else {
      setShowDomainSuggestions(false);
    }
  };

  const handleKeyDown = (e) => {
    // Previne espaços no input físico também
    if (e.key === " " || e.key === "Space") {
      e.preventDefault();
      return;
    }
  };

  const keyboardLayout = [
    ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
    ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
    ["a", "s", "d", "f", "g", "h", "j", "k", "l"],
    ["z", "x", "c", "v", "b", "n", "m"],
    ["@", ".", "-", "_", "left", "right", "delete", "clear_all", "backspace"]
  ];

  if (!isOpen) return null;

  return (
    <>
      <div style={keyboardOverlayStyle}>
        <div style={keyboardContainerStyle}>
          <div style={keyboardHeaderStyle}>
            <div style={keyboardTitleStyle}>
              Teclado Virtual
              <span style={helperTextStyle}> (espaço não permitido em email)</span>
            </div>
            <button onClick={onClose} style={keyboardCloseButtonStyle}>
              ✓ Concluir
            </button>
          </div>

          <div style={inputPreviewStyle}>
            <input
              type="text"
              value={inputValue}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              style={inputPreviewFieldStyle}
              placeholder="exemplo@email.com"
              autoFocus={false}
              ref={(input) => {
                if (input && document.activeElement !== input) {
                  // Mantém foco no teclado virtual, não no input
                  input.blur();
                }
              }}
            />
          </div>

          {showDomainSuggestions && filteredDomains.length > 0 && (
            <div style={domainsContainerStyle}>
              <div style={domainsTitleStyle}>
                📧 Sugestões de domínio (clique para completar):
              </div>
              <div style={domainsGridStyle}>
                {filteredDomains.slice(0, 8).map((domain, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleDomainSelect(domain.domain)}
                    style={domainButtonStyle}
                  >
                    {domain.domain}
                    <span style={countryBadgeStyle}>{domain.country}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          <div style={keyboardStyle}>
            {keyboardLayout.map((row, rowIndex) => (
              <div key={rowIndex} style={keyboardRowStyle}>
                {row.map((key) => {
                  let displayText = key;
                  let buttonStyle = keyButtonStyle;
                  
                  if (key === "left") displayText = "◀";
                  if (key === "right") displayText = "▶";
                  if (key === "delete") displayText = "Del";
                  if (key === "clear_all") displayText = "Limpar Tudo";
                  if (key === "backspace") displayText = "⌫";
                  if (key === "space") displayText = "Espaço";
                  
                  if (key === "clear_all") buttonStyle = { ...keyButtonStyle, ...clearAllKeyStyle };
                  else if (key === "backspace") buttonStyle = { ...keyButtonStyle, ...backspaceKeyStyle };
                  else if (key === "delete") buttonStyle = { ...keyButtonStyle, ...deleteKeyStyle };
                  else if (key === "left" || key === "right") buttonStyle = { ...keyButtonStyle, ...navKeyStyle };
                  
                  return (
                    <button
                      key={key}
                      onClick={() => handleKeyPress(key)}
                      style={buttonStyle}
                    >
                      {displayText}
                    </button>
                  );
                })}
              </div>
            ))}
          </div>

          <div style={keyboardFooterStyle}>
            <div style={footerInfoStyle}>
              💡 Dica: Espaço não é permitido em emails • Use @ para domínios
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

// Estilos inline
const keyboardOverlayStyle = {
  position: "fixed",
  bottom: 0,
  left: 0,
  right: 0,
  background: "rgba(0, 0, 0, 0.95)",
  zIndex: 20000,
  animation: "slideUp 0.3s ease-out",
};

const keyboardContainerStyle = {
  background: "#1a1f2a",
  borderTop: "1px solid rgba(255, 255, 255, 0.15)",
  padding: "20px",
  maxWidth: "900px",
  margin: "0 auto",
};

const keyboardHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  marginBottom: "16px",
  paddingBottom: "12px",
  borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
};

const keyboardTitleStyle = {
  fontSize: "18px",
  fontWeight: 600,
  color: "#f5f7fa",
};

const helperTextStyle = {
  fontSize: "12px",
  color: "#b87c2e",
  marginLeft: "8px",
  fontWeight: "normal",
};

const keyboardCloseButtonStyle = {
  padding: "10px 20px",
  borderRadius: "10px",
  border: "none",
  background: "#1f7a3f",
  color: "white",
  cursor: "pointer",
  fontSize: "14px",
  fontWeight: 600,
  transition: "all 0.2s",
};

const inputPreviewStyle = {
  marginBottom: "16px",
};

const inputPreviewFieldStyle = {
  width: "100%",
  padding: "14px 16px",
  borderRadius: "12px",
  border: "2px solid rgba(255, 255, 255, 0.2)",
  background: "#0b0f14",
  color: "#f5f7fa",
  fontSize: "18px",
  outline: "none",
  textAlign: "center",
  fontFamily: "monospace",
  letterSpacing: "0.5px",
};

const domainsContainerStyle = {
  marginBottom: "16px",
  padding: "12px",
  background: "rgba(27, 88, 131, 0.2)",
  borderRadius: "12px",
  border: "1px solid rgba(27, 88, 131, 0.4)",
};

const domainsTitleStyle = {
  fontSize: "13px",
  color: "#b0b8c5",
  marginBottom: "10px",
  fontWeight: 500,
};

const domainsGridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fill, minmax(130px, 1fr))",
  gap: "8px",
};

const domainButtonStyle = {
  padding: "10px 12px",
  background: "rgba(255, 255, 255, 0.08)",
  border: "1px solid rgba(255, 255, 255, 0.15)",
  borderRadius: "10px",
  color: "#f5f7fa",
  cursor: "pointer",
  fontSize: "13px",
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  transition: "all 0.2s",
};

const countryBadgeStyle = {
  fontSize: "10px",
  padding: "2px 6px",
  borderRadius: "12px",
  background: "rgba(255, 255, 255, 0.15)",
  color: "#b0b8c5",
};

const keyboardStyle = {
  display: "flex",
  flexDirection: "column",
  gap: "8px",
};

const keyboardRowStyle = {
  display: "flex",
  justifyContent: "center",
  gap: "8px",
  flexWrap: "wrap",
};

const keyButtonStyle = {
  padding: "16px 14px",
  minWidth: "56px",
  background: "#2c3440",
  border: "1px solid rgba(255, 255, 255, 0.1)",
  borderRadius: "10px",
  color: "#f5f7fa",
  cursor: "pointer",
  fontSize: "16px",
  fontWeight: 500,
  transition: "all 0.1s",
  userSelect: "none",
};

const backspaceKeyStyle = {
  background: "#a54c3a",
  minWidth: "70px",
};

const deleteKeyStyle = {
  background: "#8b5a2b",
  minWidth: "60px",
};

const clearAllKeyStyle = {
  background: "#b87c2e",
  minWidth: "100px",
  fontWeight: 600,
};

const navKeyStyle = {
  background: "#3a4454",
  minWidth: "60px",
};

const keyboardFooterStyle = {
  marginTop: "16px",
  paddingTop: "12px",
  borderTop: "1px solid rgba(255, 255, 255, 0.1)",
  textAlign: "center",
};

const footerInfoStyle = {
  fontSize: "12px",
  color: "#8b95a5",
};

// Adicionar animação ao documento
if (!document.querySelector("#virtual-keyboard-styles")) {
  const styleSheet = document.createElement("style");
  styleSheet.id = "virtual-keyboard-styles";
  styleSheet.textContent = `
    @keyframes slideUp {
      from {
        transform: translateY(100%);
      }
      to {
        transform: translateY(0);
      }
    }
  `;
  document.head.appendChild(styleSheet);
}

export default VirtualKeyboard;