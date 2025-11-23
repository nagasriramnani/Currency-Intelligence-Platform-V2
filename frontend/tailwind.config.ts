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
        sapphire: {
          950: '#020617', // Deepest background
          900: '#0B1120', // Deep background
          800: '#1e293b', // Card background
          700: '#334155', // Lighter card
          600: '#475569', // Borders
          500: '#3B82F6', // Primary Brand
          400: '#60A5FA', // Lighter Brand
          300: '#93C5FD', // Accent
          200: '#BFDBFE', // Highlight
          100: '#DBEAFE', // Text Light
          50: '#EFF6FF',  // Text White
        },
        brand: {
          navy: '#0B1120',
          primary: '#3B82F6',
          accent: '#60A5FA',
          sky: '#E0F2FE',
          soft: '#F8FAFC',
          slate: '#64748B',
          midnight: '#020617',
        },
        success: '#10B981',
        warning: '#F59E0B',
        danger: '#EF4444',
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


