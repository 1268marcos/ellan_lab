// 01_source/frontend/src/components/EmailReceiptModal.jsx
import React, { useEffect, useState } from "react";
import VirtualKeyboard from "./VirtualKeyboard";

const EmailReceiptModal = ({
  isOpen,
  onClose,
  onSubmit,
  receiptCode,
  orderId,
  isLoading,
  successMessage,
  errorMessage,
}) => {
  const [email, setEmail] = useState("");
  const [emailError, setEmailError] = useState("");
  const [showKeyboard, setShowKeyboard] = useState(false);

  const isSuccess = Boolean(successMessage);

  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@([^\s@]+\.)+[^\s@]+$/;
    if (!email) return "O email é obrigatório";
    if (!emailRegex.test(email)) return "Digite um email válido (ex: nome@dominio.com)";
    return "";
  };

  // 🔒 BOTÃO SÓ HABILITA COM EMAIL VÁLIDO
  const isEmailValid = email && !validateEmail(email);

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

  // ✅ AUTO-CLOSE CONFIÁVEL
  useEffect(() => {
    if (!isSuccess) return;

    const timer = setTimeout(() => {
      handleClose(); // ← IMPORTANTE: usar handleClose e não onClose direto
    }, 2000);

    return () => clearTimeout(timer);
  }, [isSuccess]);

  useEffect(() => {
    if (!isOpen) return;

    const handleEscape = (event) => {
      if (event.key === "Escape") {
        handleClose();
      }
    };

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <>
      <div style={modalOverlayStyle} onClick={handleClose}>
        <div
          style={modalCardStyle}
          onClick={(e) => e.stopPropagation()}
          role="dialog"
          aria-modal="true"
          aria-labelledby="email-receipt-modal-title"
          aria-describedby="email-receipt-modal-description"
        >
          <div style={modalHeaderStyle}>
            <h3 id="email-receipt-modal-title" style={modalTitleStyle}>Receber comprovante fiscal</h3>
            <button type="button" onClick={handleClose} style={printModalCloseButtonStyle}>
              Fechar
            </button>
          </div>

          <div style={modalContentStyle}>
            <div style={infoBoxStyle}>
              <div style={infoTextStyle}>
                <strong>Código do comprovante:</strong>
                <div style={receiptCodeStyle}>{receiptCode || "---"}</div>
              </div>
              {orderId && (
                <div style={infoTextStyle}>
                  <strong>Pedido:</strong> {orderId}
                </div>
              )}
            </div>

            <p id="email-receipt-modal-description" style={descriptionStyle}>
              Digite seu email para receber o código do comprovante fiscal. 
              Você poderá consultar e imprimir o comprovante posteriormente.
            </p>

            <form onSubmit={handleSubmit}>
              <label htmlFor="email-receipt-input" style={labelStyle}>
                Email *
                <div style={emailInputWrapperStyle}>
                  <input
                    id="email-receipt-input"
                    type="email"
                    value={email}
                    onChange={(e) => handleEmailChange(e.target.value)}
                    placeholder="seu@email.com"
                    style={inputStyle}
                    disabled={isLoading || isSuccess}
                    autoFocus
                  />
                  <button
                    type="button"
                    onClick={() => setShowKeyboard(true)}
                    style={keyboardButtonStyle}
                    disabled={isSuccess}
                  >
                    ⌨️ Teclado
                  </button>
                </div>
              </label>

              {emailError && <div style={errorTextStyle} role="alert">{emailError}</div>}
              {errorMessage && <div style={serverErrorTextStyle} role="alert">{errorMessage}</div>}
              {successMessage && <div style={serverSuccessTextStyle} role="status" aria-live="polite">{successMessage}</div>}

              <div style={buttonGroupStyle}>
                {!isSuccess && (
                  <button
                    type="submit"
                    style={{
                      ...submitButtonStyle,
                      opacity: isEmailValid ? 1 : 0.5,
                      cursor: isEmailValid ? "pointer" : "not-allowed",
                    }}
                    disabled={!isEmailValid || isLoading}
                  >
                    {isLoading ? "Enviando..." : "Enviar email"}
                  </button>
                )}

                <button
                  type="button"
                  onClick={handleClose}
                  style={cancelButtonStyle}
                  disabled={isLoading && !isSuccess}
                >
                  {isSuccess ? "Fechar" : "Cancelar"}
                </button>
              </div>
            </form>

            <div style={helperTextStyle}>
              <small>
                O código será enviado para o email informado. 
                Você também pode consultar o comprovante no nosso site.
              </small>
            </div>
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

// Styles (padrão antigo)
const modalOverlayStyle = {
  position: "fixed",
  inset: 0,
  background: "rgba(0, 0, 0, 0.8)",
  display: "grid",
  placeItems: "center",
  zIndex: 10000,
  padding: "20px",
  backdropFilter: "blur(4px)",
};

const modalCardStyle = {
  background: "#11161c",
  border: "1px solid rgba(255, 255, 255, 0.15)",
  borderRadius: "20px",
  width: "100%",
  maxWidth: "480px",
  boxShadow: "0 20px 48px rgba(0, 0, 0, 0.5)",
  animation: "slideIn 0.2s ease-out",
};

const modalHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  padding: "20px 24px",
  borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
};

const modalTitleStyle = {
  margin: 0,
  fontSize: "20px",
  fontWeight: 600,
  color: "#f5f7fa",
};

const printModalCloseButtonStyle = {
  padding: "8px 10px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "#1b5883",
  color: "#ffffff",
  cursor: "pointer",
  fontWeight: 600,
};

const modalContentStyle = {
  padding: "24px",
};

const infoBoxStyle = {
  background: "rgba(27, 88, 131, 0.15)",
  border: "1px solid rgba(27, 88, 131, 0.35)",
  borderRadius: "12px",
  padding: "16px",
  marginBottom: "20px",
};

const infoTextStyle = {
  fontSize: "14px",
  color: "#f5f7fa",
  marginBottom: "8px",
};

const receiptCodeStyle = {
  fontFamily: "monospace",
  fontSize: "18px",
  fontWeight: "bold",
  marginTop: "6px",
  padding: "8px",
  background: "rgba(0, 0, 0, 0.3)",
  borderRadius: "8px",
  textAlign: "center",
  letterSpacing: "1px",
};

const descriptionStyle = {
  fontSize: "14px",
  color: "#b0b8c5",
  marginBottom: "20px",
  lineHeight: "1.5",
};

const labelStyle = {
  display: "block",
  marginBottom: "16px",
  fontSize: "14px",
  fontWeight: 500,
  color: "#f5f7fa",
};

const emailInputWrapperStyle = {
  display: "flex",
  gap: "8px",
  marginTop: "8px",
};

const inputStyle = {
  flex: 1,
  padding: "12px 14px",
  borderRadius: "10px",
  border: "1px solid rgba(255, 255, 255, 0.15)",
  background: "#0b0f14",
  color: "#f5f7fa",
  fontSize: "14px",
  outline: "none",
  transition: "border-color 0.2s",
};

const keyboardButtonStyle = {
  padding: "12px 14px",
  borderRadius: "10px",
  border: "1px solid rgba(255, 255, 255, 0.15)",
  background: "#0b0f14",
  color: "#f5f7fa",
  cursor: "pointer",
  fontSize: "14px",
  transition: "background 0.2s",
};

const errorTextStyle = {
  color: "#ffb4b4",
  fontSize: "12px",
  marginTop: "-12px",
  marginBottom: "12px",
};

const serverErrorTextStyle = {
  color: "#ffb4b4",
  fontSize: "12px",
  marginBottom: "12px",
  padding: "8px",
  background: "rgba(255, 180, 180, 0.1)",
  borderRadius: "8px",
};

const serverSuccessTextStyle = {
  color: "#8bcb8f",
  fontSize: "12px",
  marginBottom: "12px",
  padding: "8px",
  background: "rgba(139, 203, 143, 0.1)",
  borderRadius: "8px",
};

const buttonGroupStyle = {
  display: "flex",
  gap: "12px",
  marginTop: "24px",
};

const cancelButtonStyle = {
  flex: 1,
  padding: "12px",
  borderRadius: "10px",
  border: "1px solid rgba(255, 255, 255, 0.2)",
  background: "transparent",
  color: "#f5f7fa",
  cursor: "pointer",
  fontSize: "14px",
  fontWeight: 500,
  transition: "background 0.2s",
};

const submitButtonStyle = {
  flex: 1,
  padding: "12px",
  borderRadius: "10px",
  border: "none",
  background: "#1f7a3f",
  color: "white",
  cursor: "pointer",
  fontSize: "14px",
  fontWeight: 600,
  transition: "background 0.2s",
};

const helperTextStyle = {
  marginTop: "16px",
  textAlign: "center",
  fontSize: "12px",
  color: "#8b95a5",
};

// Adicione esta animação ao seu arquivo CSS global ou crie um componente de estilo
const styleSheet = document.createElement("style");
styleSheet.textContent = `
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
document.head.appendChild(styleSheet);

export default EmailReceiptModal;