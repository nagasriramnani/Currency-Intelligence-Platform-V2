import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Enterprise-grade color palette - Bloomberg calm + Stripe clarity
        sapphire: {
          950: '#020617', // Deepest background
          900: '#0A0F1F', // Deep navy - calmer than before
          800: '#141B2D', // Card background - slightly warmer
          700: '#1E293B', // Lighter card
          600: '#334155', // Borders - muted
          500: '#2563EB', // Primary steel blue - less saturated
          400: '#3B82F6', // Lighter steel
          300: '#60A5FA', // Accent - softer
          200: '#93C5FD', // Highlight
          100: '#C7D2E4', // Text secondary
          50: '#E2E8F0',  // Text primary
        },
        brand: {
          navy: '#0A0F1F',
          primary: '#2563EB',
          accent: '#3B82F6',
          sky: '#DBEAFE',
          soft: '#F1F5F9',
          slate: '#64748B',
          midnight: '#020617',
        },
        // Enterprise signal colors - muted, authoritative
        success: '#059669',    // Deep emerald (was #10B981)
        warning: '#D97706',    // Soft amber (was #F59E0B)
        danger: '#DC2626',     // Dark crimson (was #EF4444)
        // Additional enterprise colors
        emerald: {
          500: '#059669',
          400: '#10B981',
          300: '#34D399',
        },
        amber: {
          500: '#D97706',
          400: '#F59E0B',
          300: '#FBBF24',
        },
        crimson: {
          500: '#DC2626',
          400: '#EF4444',
          300: '#F87171',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out forwards',
        'slide-up': 'slideUp 0.5s ease-out forwards',
        'slide-up-delay': 'slideUp 0.5s ease-out 0.1s forwards',
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'hero-glow': 'conic-gradient(from 180deg at 50% 50%, #1e293b 0deg, #0f172a 180deg, #1e293b 360deg)',
      },
    },
  },
  plugins: [],
}
export default config


