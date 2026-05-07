import type { CSSProperties } from 'react'

export const COOTheme = {
  colors: {
    primary: '#2C5282', // Azul operacional (confiança)
    secondary: '#4A5568', // Cinza neutro (equilíbrio)
    accent: '#DD6B20', // Laranja ação (urgência operacional)
    background: '#FFFFFF', // Branco puro (foco)
    warning: '#D69E2E', // Âmbar (alertas preventivos)

    status: {
      operational: '#10B981', // Verde sólido
      attention: '#F59E0B', // Âmbar pulsante
      critical: '#EF4444', // Vermelho com borda animada
      maintenance: '#6B7280', // Cinza com padrão diagonal
    },

    text: {
      primary: '#1A202C',
      secondary: '#4A5568',
      tertiary: '#718096',
    },
  },

  typography: {
    headings: {
      fontFamily: 'Inter',
      fontWeight: '700',
      sizes: {
        h1: '28px',
        h2: '24px',
        h3: '20px',
        h4: '18px',
      },
    },
    body: {
      fontFamily: 'Inter',
      fontWeight: '400',
      size: '15px',
    },
    status: {
      fontFamily: 'Inter',
      fontWeight: '500',
      size: '13px',
      textTransform: 'uppercase' as const,
    },
  },

  spacing: {
    layout: '24px',
    component: '16px',
    element: '8px',
  },

  animations: {
    pulse: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
    borderPulse: 'border-pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
  },
} as const

export type COOThemeType = typeof COOTheme

/** Variáveis CSS aplicadas em `.coo-layout` para estilos globais do portal. */
export function getCooThemeCssVariables(): CSSProperties {
  const { colors, typography, spacing, animations } = COOTheme
  return {
    '--coo-primary': colors.primary,
    '--coo-secondary': colors.secondary,
    '--coo-accent': colors.accent,
    '--coo-background': colors.background,
    '--coo-warning': colors.warning,
    '--coo-status-operational': colors.status.operational,
    '--coo-status-attention': colors.status.attention,
    '--coo-status-critical': colors.status.critical,
    '--coo-status-maintenance': colors.status.maintenance,
    '--coo-text-primary': colors.text.primary,
    '--coo-text-secondary': colors.text.secondary,
    '--coo-text-tertiary': colors.text.tertiary,
    '--coo-font-heading': typography.headings.fontFamily,
    '--coo-font-body': typography.body.fontFamily,
    '--coo-weight-heading': String(typography.headings.fontWeight),
    '--coo-size-h1': typography.headings.sizes.h1,
    '--coo-size-h2': typography.headings.sizes.h2,
    '--coo-size-h3': typography.headings.sizes.h3,
    '--coo-size-h4': typography.headings.sizes.h4,
    '--coo-size-body': typography.body.size,
    '--coo-weight-body': String(typography.body.fontWeight),
    '--coo-size-status': typography.status.size,
    '--coo-weight-status': String(typography.status.fontWeight),
    '--coo-space-layout': spacing.layout,
    '--coo-space-component': spacing.component,
    '--coo-space-element': spacing.element,
    '--coo-anim-pulse': animations.pulse,
    '--coo-anim-border-pulse': animations.borderPulse,
  } as CSSProperties
}
