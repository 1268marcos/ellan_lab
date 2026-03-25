// 01_source/frontend/src/components/EmailReceiptModal.jsx
import React, { useState } from "react";
import VirtualKeyboard from "./VirtualKeyboard";


const EmailReceiptModal = ({ isOpen, onClose, onSubmit, receiptCode, orderId, isLoading, successMessage, errorMessage, }) => {

  const [email, setEmail] = useState("");
  const [emailError, setEmailError] = useState("");
  const [showKeyboard, setShowKeyboard] = useState(false);

  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@([^\s@]+\.)+[^\s@]+$/;
    if (!email) {
      return "O email é obrigatório";
    }
    if (!emailRegex.test(email)) {
      return "Digite um email válido (ex: nome@dominio.com)";
    }
    return "";
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const error = validateEmail(email);
    if (error) {
      setEmailError(error);
      return;
    }
    setEmailError("");
    await onSubmit(email);
    setShowKeyboard(false);
  };

  const handleClose = () => {
    setEmail("");
    setEmailError("");
    setShowKeyboard(false);
    onClose();
  };

  const handleEmailChange = (newEmail) => {
    setEmail(newEmail);
    if (emailError) setEmailError("");
  };

  if (!isOpen) return null;

  return (
    <>
      <div style={modalOverlay} onClick={handleClose}>
        <div style={modalContainer} onClick={(e) => e.stopPropagation()}>
          <div style={modalHeader}>
            <h3 style={modalTitle}>Receber comprovante fiscal</h3>
            <button onClick={handleClose} style={printModalCloseButtonStyle}>
              {/* ✕ */}
              Fechar
            </button>
          </div>

          <div style={modalContent}>
            <div style={infoBox}>
              <div style={infoText}>
                <strong>Código do comprovante:</strong>
                <div style={receiptCodeDisplay}>{receiptCode || "---"}</div>
              </div>
              {orderId && (
                <div style={infoText}>
                  <strong>Pedido:</strong> {orderId}
                </div>
              )}
            </div>

            <p style={description}>
              Digite seu email para receber o código do comprovante fiscal.
            </p>

            <form onSubmit={handleSubmit}>
              <label style={labelStyle}>
                Email *
                <div style={emailInputWrapper}>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => handleEmailChange(e.target.value)}
                    placeholder="seu@email.com"
                    style={emailInput}
                    disabled={isLoading}
                  />
                  <button
                    type="button"
                    onClick={() => setShowKeyboard(true)}
                    style={keyboardButton}
                  >
                    ⌨️ Teclado
                  </button>
                </div>
              </label>
              {emailError && <div style={errorMessage}>{emailError}</div>}
              {errorMessage ? <div style={serverErrorMessage}>{errorMessage}</div> : null}
              {successMessage ? <div style={serverSuccessMessage}>{successMessage}</div> : null}

              <div style={buttonGroup}>
                <button
                  type="button"
                  onClick={handleClose}
                  style={cancelButton}
                  disabled={isLoading}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  style={submitButton}
                  disabled={isLoading}
                >
                  {isLoading ? "Enviando..." : "Enviar email"}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      <VirtualKeyboard
        value={email}
        onChange={handleEmailChange}
        onClose={() => setShowKeyboard(false)}
        isOpen={showKeyboard}
      />
    </>
  );
};

// Estilos
const modalOverlay = {
  position: "fixed",
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  backgroundColor: "rgba(0, 0, 0, 0.8)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  zIndex: 10000,
  padding: "20px"
};

const modalContainer = {
  backgroundColor: "#11161c",
  borderRadius: "20px",
  width: "100%",
  maxWidth: "480px",
  border: "1px solid rgba(255, 255, 255, 0.15)",
  animation: "slideIn 0.2s ease-out"
};

const modalHeader = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  padding: "20px 24px",
  borderBottom: "1px solid rgba(255, 255, 255, 0.1)"
};

const modalTitle = {
  margin: 0,
  fontSize: "20px",
  fontWeight: 600,
  color: "#f5f7fa"
};

const modalCloseButton = {
  background: "rgba(255, 255, 255, 0.1)",
  border: "none",
  borderRadius: "8px",
  width: "32px",
  height: "32px",
  cursor: "pointer",
  fontSize: "18px",
  color: "#f5f7fa",
  display: "flex",
  alignItems: "center",
  justifyContent: "center"
};

const printModalCloseButtonStyle = {
  padding: "8px 10px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#1b5883",
  color: "#fff",
  cursor: "pointer",
  fontWeight: 600,
};

const modalContent = {
  padding: "24px"
};

const infoBox = {
  backgroundColor: "rgba(27, 88, 131, 0.15)",
  border: "1px solid rgba(27, 88, 131, 0.35)",
  borderRadius: "12px",
  padding: "16px",
  marginBottom: "20px"
};

const infoText = {
  fontSize: "14px",
  color: "#f5f7fa",
  marginBottom: "8px"
};

const receiptCodeDisplay = {
  fontFamily: "monospace",
  fontSize: "18px",
  fontWeight: "bold",
  marginTop: "6px",
  padding: "8px",
  backgroundColor: "rgba(0, 0, 0, 0.3)",
  borderRadius: "8px",
  textAlign: "center",
  letterSpacing: "1px"
};

const description = {
  fontSize: "14px",
  color: "#b0b8c5",
  marginBottom: "20px",
  lineHeight: "1.5"
};

const labelStyle = {
  display: "block",
  marginBottom: "16px",
  fontSize: "14px",
  fontWeight: 500,
  color: "#f5f7fa"
};

const emailInputWrapper = {
  display: "flex",
  gap: "8px",
  marginTop: "8px"
};

const emailInput = {
  flex: 1,
  padding: "12px 14px",
  borderRadius: "10px",
  border: "1px solid rgba(255, 255, 255, 0.15)",
  backgroundColor: "#0b0f14",
  color: "#f5f7fa",
  fontSize: "14px",
  outline: "none"
};

const keyboardButton = {
  padding: "12px 16px",
  borderRadius: "10px",
  border: "1px solid rgba(255, 255, 255, 0.15)",
  backgroundColor: "#1b5883",
  color: "white",
  cursor: "pointer",
  fontSize: "14px",
  fontWeight: 500
};

const errorMessage = {
  color: "#ffb4b4",
  fontSize: "12px",
  marginTop: "-12px",
  marginBottom: "12px"
};

const buttonGroup = {
  display: "flex",
  gap: "12px",
  marginTop: "24px"
};

const cancelButton = {
  flex: 1,
  padding: "12px",
  borderRadius: "10px",
  border: "1px solid rgba(255, 255, 255, 0.2)",
  backgroundColor: "transparent",
  color: "#f5f7fa",
  cursor: "pointer",
  fontSize: "14px",
  fontWeight: 500
};

const submitButton = {
  flex: 1,
  padding: "12px",
  borderRadius: "10px",
  border: "none",
  backgroundColor: "#1f7a3f",
  color: "white",
  cursor: "pointer",
  fontSize: "14px",
  fontWeight: 600
};

const serverErrorMessage = {
  color: "#ffb4b4",
  fontSize: "13px",
  marginTop: "8px",
  marginBottom: "12px",
  padding: "10px 12px",
  borderRadius: "10px",
  backgroundColor: "rgba(179, 38, 30, 0.15)",
  border: "1px solid rgba(179, 38, 30, 0.35)",
  lineHeight: "1.4",
};

const serverSuccessMessage = {
  color: "#d7ffe1",
  fontSize: "13px",
  marginTop: "8px",
  marginBottom: "12px",
  padding: "10px 12px",
  borderRadius: "10px",
  backgroundColor: "rgba(31, 122, 63, 0.18)",
  border: "1px solid rgba(31, 122, 63, 0.35)",
  lineHeight: "1.4",
};

// Adiciona animação CSS
const modalStyles = document.createElement("style");
modalStyles.textContent = `
  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(-20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
`;
if (!document.head.querySelector("#email-modal-styles")) {
  modalStyles.id = "email-modal-styles";
  document.head.appendChild(modalStyles);
}

export default EmailReceiptModal;