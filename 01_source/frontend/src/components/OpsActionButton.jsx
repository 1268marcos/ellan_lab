import React from "react";

const BASE_STYLE = {
  padding: "10px 14px",
  borderRadius: 10,
  fontWeight: 700,
  cursor: "pointer",
};

const VARIANT_STYLE = {
  primary: {
    border: "none",
    background: "#1D4ED8",
    color: "#F8FAFC",
  },
  secondary: {
    border: "1px solid #334155",
    background: "#0B1220",
    color: "#E2E8F0",
  },
  warn: {
    border: "1px solid rgba(217,119,6,0.45)",
    background: "rgba(217,119,6,0.2)",
    color: "#FDE68A",
  },
  copy: {
    border: "1px solid rgba(59,130,246,0.55)",
    background: "rgba(59,130,246,0.2)",
    color: "#93C5FD",
  },
};

/**
 * Botão padrão da camada OPS para manter consistência visual e semântica.
 *
 * Variantes disponíveis:
 * - `primary`: ação principal (execução/mutação positiva)
 * - `secondary`: ação de suporte/consulta
 * - `warn`: ação sensível (retry/aprovação com atenção)
 * - `copy`: ação de cópia/evidência
 *
 * Exemplos rápidos:
 * `<OpsActionButton variant="primary">POST generate</OpsActionButton>`
 * `<OpsActionButton variant="secondary">GET list</OpsActionButton>`
 * `<OpsActionButton variant="warn">PATCH approve</OpsActionButton>`
 * `<OpsActionButton variant="copy">Copiar evidência</OpsActionButton>`
 *
 * Dicas de uso:
 * - Prefira `variant` em vez de estilos inline duplicados.
 * - Use `style` apenas para ajustes pontuais (ex.: largura/margem).
 */
export default function OpsActionButton({ variant = "secondary", style, ...props }) {
  const variantStyle = VARIANT_STYLE[variant] || VARIANT_STYLE.secondary;
  return <button {...props} style={{ ...BASE_STYLE, ...variantStyle, ...style }} />;
}
