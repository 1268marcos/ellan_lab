// 01_source/frontend/src/components/VirtualKeyboard.jsx
import React, { useState, useEffect } from "react";

const POPULAR_DOMAINS = [
  { domain: "@gmail.com", country: "Brasil" },
  { domain: "@yahoo.com", country: "Brasil" },
  { domain: "@ymail.com", country: "Brasil" },
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

// Constante para os atalhos (definir antes do return)
const QUICK_ADDITIONS = [
  { label: ".com", value: ".com", tooltip: "Adiciona .com" },
  { label: ".com.br", value: ".com.br", tooltip: "Adiciona .com.br" },
  { label: ".pt", value: ".pt", tooltip: "Adiciona .pt" },
  { label: "@gmail.com", value: "@gmail.com", tooltip: "Adiciona @gmail.com" },
  { label: "@hotmail.com", value: "@hotmail.com", tooltip: "Adiciona @hotmail.com" },
  { label: "@outlook.com", value: "@outlook.com", tooltip: "Adiciona @outlook.com" },
  { label: "@uol.com.br", value: "@uol.com.br", tooltip: "Adiciona @uol.com.br" },
];

// Nova função para lidar com os atalhos (adicionar junto com as outras)
const handleQuickAdd = (addition) => {
  let newValue = inputValue;
  
  // Evita duplicar '@' se o input já terminar com ele
  if (inputValue.endsWith('@') && addition.startsWith('@')) {
    newValue = inputValue.slice(0, -1) + addition;
  } 
  else {
    newValue = inputValue + addition;
  }
  
  const cleanedValue = cleanEmailInput(newValue);
  setInputValue(cleanedValue);
  onChange(cleanedValue);
};

const VirtualKeyboard = ({ value, onChange, onClose, isOpen }) => {
  const [inputValue, setInputValue] = useState(value);

  useEffect(() => {
    setInputValue(value);
  }, [value]);

  // Limpa espaços e caracteres inválidos
  const cleanEmailInput = (text) => {
    // Remove espaços
    let cleaned = text.replace(/\s/g, "");
    // Permite apenas caracteres válidos para email (simplificado)
    cleaned = cleaned.replace(/[^a-zA-Z0-9@._\-]/g, "");
    return cleaned;
  };

  const handleKeyPress = (key) => {
    let newValue = inputValue;

    switch (key) {
      case "backspace":
        newValue = inputValue.slice(0, -1);
        break;
      
      case "clear_all":
        newValue = "";
        break;
      
      case "space":
        // Ignora espaço
        return;
      
      default:
        // Adiciona o caractere
        newValue = inputValue + key;
        // Limpa após adicionar
        newValue = cleanEmailInput(newValue);
    }

    setInputValue(newValue);
    onChange(newValue);
  };

  const handleDomainSelect = (domain) => {
    let newValue;
    if (inputValue.includes("@")) {
      const localPart = inputValue.split("@")[0];
      newValue = localPart + domain;
    } else {
      newValue = inputValue + domain;
    }
    
    setInputValue(newValue);
    onChange(newValue);
  };

  const handleInputChange = (e) => {
    const newValue = cleanEmailInput(e.target.value);
    setInputValue(newValue);
    onChange(newValue);
  };

  // Layout do teclado
  const keyboardRows = [
    ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
    ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
    ["a", "s", "d", "f", "g", "h", "j", "k", "l"],
    ["z", "x", "c", "v", "b", "n", "m"],
    ["@", ".", "-", "_", "clear_all", "backspace"]
  ];

  // Verifica se deve mostrar sugestões de domínio
  const showSuggestions = inputValue.includes("@") && !inputValue.endsWith("@");
  
  // Filtra domínios baseado no que foi digitado
  let filteredDomains = POPULAR_DOMAINS;
  if (inputValue.includes("@")) {
    const typedDomain = inputValue.split("@")[1];
    if (typedDomain) {
      filteredDomains = POPULAR_DOMAINS.filter(domain => 
        domain.domain.toLowerCase().includes(typedDomain.toLowerCase())
      );
    }
  }

  if (!isOpen) return null;

  return (
    <div style={keyboardOverlay}>
      <div style={keyboardContainer}>
        {/* Header */}
        <div style={keyboardHeader}>
          <div>
            <span style={keyboardTitle}>Teclado Virtual</span>
            <span style={keyboardHint}> (espaço não permitido)</span>
          </div>
          <button onClick={onClose} style={closeButton}>
            Concluir ✓
          </button>
        </div>

        {/* Input Preview */}
        <div style={inputContainer}>
          <input
            type="text"
            value={inputValue}
            onChange={handleInputChange}
            placeholder="exemplo@email.com"
            style={inputField}
          />
        </div>

        {/* NOVA SEÇÃO: Atalhos Rápidos */}
        <div style={quickAddContainer}>
          <div style={quickAddTitle}>⚡ Adicionar rapidamente:</div>
          <div style={quickAddGrid}>
            {QUICK_ADDITIONS.map((item, idx) => (
              <button
                key={idx}
                onClick={() => handleQuickAdd(item.value)}
                style={quickAddButton}
                title={item.tooltip}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>

        {/* Domain Suggestions */}
        {showSuggestions && filteredDomains.length > 0 && (
          <div style={suggestionsContainer}>
            <div style={suggestionsTitle}>Domínios populares:</div>
            <div style={suggestionsGrid}>
              {filteredDomains.slice(0, 6).map((domain, idx) => (
                <button
                  key={idx}
                  onClick={() => handleDomainSelect(domain.domain)}
                  style={suggestionButton}
                >
                  {domain.domain}
                  <span style={countryBadge}>{domain.country}</span>
                </button>
              ))}
            </div>
          </div>
        )}

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
                  >
                    {displayText}
                  </button>
                );
              })}
            </div>
          ))}
        </div>

        {/* Footer */}
        <div style={keyboardFooter}>
          <div style={footerButtonsRow}>
            <span style={footerText}>💡 Dica: Use os botões rápidos acima para agilizar</span>
            <button onClick={onClose} style={footerCloseButton}>
              Concluir ✓
            </button>
          </div>
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
  backgroundColor: "rgba(0, 0, 0, 0.9)",
  zIndex: 20000,
  padding: "16px",
  animation: "slideUp 0.3s ease-out"
};

const keyboardContainer = {
  maxWidth: "900px",
  margin: "0 auto",
  backgroundColor: "#1a1f2a",
  borderRadius: "16px",
  padding: "20px",
  border: "1px solid rgba(255, 255, 255, 0.1)"
};

const keyboardHeader = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  marginBottom: "16px",
  paddingBottom: "12px",
  borderBottom: "1px solid rgba(255, 255, 255, 0.1)"
};

const keyboardTitle = {
  fontSize: "18px",
  fontWeight: 600,
  color: "#f5f7fa"
};

const keyboardHint = {
  fontSize: "12px",
  color: "#f39c12",
  marginLeft: "8px"
};

const closeButton = {
  padding: "8px 20px",
  backgroundColor: "#1f7a3f",
  color: "white",
  border: "none",
  borderRadius: "8px",
  cursor: "pointer",
  fontSize: "14px",
  fontWeight: 600
};

const inputContainer = {
  marginBottom: "16px"
};

const inputField = {
  width: "100%",
  padding: "14px",
  fontSize: "18px",
  backgroundColor: "#0b0f14",
  border: "1px solid rgba(255, 255, 255, 0.2)",
  borderRadius: "10px",
  color: "#f5f7fa",
  outline: "none",
  textAlign: "center",
  fontFamily: "monospace"
};

const suggestionsContainer = {
  marginBottom: "16px",
  padding: "12px",
  backgroundColor: "rgba(27, 88, 131, 0.2)",
  borderRadius: "12px",
  border: "1px solid rgba(27, 88, 131, 0.4)"
};

const suggestionsTitle = {
  fontSize: "13px",
  color: "#b0b8c5",
  marginBottom: "10px"
};

const suggestionsGrid = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fill, minmax(130px, 1fr))",
  gap: "8px"
};

const suggestionButton = {
  padding: "10px",
  backgroundColor: "rgba(255, 255, 255, 0.08)",
  border: "1px solid rgba(255, 255, 255, 0.15)",
  borderRadius: "8px",
  color: "#f5f7fa",
  cursor: "pointer",
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  fontSize: "13px"
};

const countryBadge = {
  fontSize: "10px",
  padding: "2px 6px",
  backgroundColor: "rgba(255, 255, 255, 0.15)",
  borderRadius: "12px",
  color: "#b0b8c5"
};

const keyboardLayout = {
  display: "flex",
  flexDirection: "column",
  gap: "8px"
};

const keyboardRow = {
  display: "flex",
  justifyContent: "center",
  gap: "8px",
  flexWrap: "wrap"
};

const keyButton = {
  padding: "14px 12px",
  minWidth: "55px",
  backgroundColor: "#2c3440",
  border: "1px solid rgba(255, 255, 255, 0.1)",
  borderRadius: "10px",
  color: "#f5f7fa",
  cursor: "pointer",
  fontSize: "16px",
  fontWeight: 500,
  transition: "all 0.1s"
};

const clearAllButton = {
  backgroundColor: "#b87c2e",
  minWidth: "100px"
};

const backspaceButton = {
  backgroundColor: "#a54c3a",
  minWidth: "80px"
};

const keyboardFooter = {
  marginTop: "16px",
  paddingTop: "12px",
  borderTop: "1px solid rgba(255, 255, 255, 0.1)",
  textAlign: "center"
};

const footerText = {
  fontSize: "12px",
  color: "#8b95a5"
};

// ... novos estilos para a seção de atalhos e rodapé ...

const quickAddContainer = {
  marginBottom: "16px",
  padding: "12px",
  backgroundColor: "rgba(31, 122, 63, 0.15)",
  borderRadius: "12px",
  border: "1px solid rgba(31, 122, 63, 0.3)"
};

const quickAddTitle = {
  fontSize: "13px",
  color: "#b0b8c5",
  marginBottom: "10px"
};

const quickAddGrid = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fill, minmax(100px, 1fr))",
  gap: "8px"
};

const quickAddButton = {
  padding: "12px 8px",
  backgroundColor: "rgba(31, 122, 63, 0.9)",
  border: "none",
  borderRadius: "8px",
  color: "#f5f7fa",
  cursor: "pointer",
  fontSize: "14px",
  fontWeight: 600,
  transition: "all 0.1s",
  textAlign: "center"
};

const footerButtonsRow = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: "16px"
};

const footerCloseButton = {
  padding: "10px 24px",
  backgroundColor: "#1f7a3f",
  color: "white",
  border: "none",
  borderRadius: "8px",
  cursor: "pointer",
  fontSize: "16px",
  fontWeight: 600,
  minWidth: "120px"
};

// ... adicionar também um efeito hover/active via CSS (você pode manter no styleSheet)



// Adiciona animação CSS
const styleSheet = document.createElement("style");
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
if (!document.head.querySelector("#virtual-keyboard-styles")) {
  styleSheet.id = "virtual-keyboard-styles";
  document.head.appendChild(styleSheet);
}

export default VirtualKeyboard;