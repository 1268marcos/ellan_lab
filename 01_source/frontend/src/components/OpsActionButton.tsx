import React, { type CSSProperties, type ComponentPropsWithoutRef } from "react";

const BASE_STYLE: CSSProperties = {
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
} as const;

export type OpsActionButtonVariant = keyof typeof VARIANT_STYLE;

export type OpsActionButtonProps = Omit<ComponentPropsWithoutRef<"button">, "style"> & {
  variant?: OpsActionButtonVariant;
  style?: CSSProperties;
};

/**
 * Botão padrão da camada OPS para manter consistência visual e semântica.
 */
export default function OpsActionButton({
  variant = "secondary",
  style,
  ...props
}: OpsActionButtonProps) {
  const variantStyle = VARIANT_STYLE[variant] ?? VARIANT_STYLE.secondary;
  return <button {...props} style={{ ...BASE_STYLE, ...variantStyle, ...style }} />;
}
