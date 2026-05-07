/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'Segoe UI', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      colors: {
        ceo: {
          primary: '#1A365D',
          secondary: '#2D3748',
          accent: '#38A169',
          bg: '#F7FAFC',
          alert: '#E53E3E',
        },
      },
      boxShadow: {
        'ceo-card': '0 1px 3px rgba(26, 54, 93, 0.08), 0 8px 24px rgba(26, 54, 93, 0.06)',
        'ceo-card-hover': '0 4px 12px rgba(26, 54, 93, 0.12), 0 12px 40px rgba(26, 54, 93, 0.08)',
      },
      keyframes: {
        'ceo-shimmer': {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        'ceo-check': {
          '0%': { transform: 'scale(0.6)', opacity: '0' },
          '50%': { transform: 'scale(1.08)', opacity: '1' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        'ceo-toast-in': {
          '0%': { transform: 'translateY(12px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
      animation: {
        'ceo-shimmer': 'ceo-shimmer 1.35s ease-in-out infinite',
        'ceo-check': 'ceo-check 0.45s ease-out forwards',
        'ceo-toast-in': 'ceo-toast-in 0.35s ease-out forwards',
      },
    },
  },
  plugins: [],
}
