/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./web/**/*.{html,js,py}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        }
      },
      borderRadius: {
        'DEFAULT': '0.75rem',
      },
      boxShadow: {
        'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        'DEFAULT': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'md': '0 6px 12px -2px rgba(0, 0, 0, 0.12), 0 3px 7px -3px rgba(0, 0, 0, 0.1)',
        'lg': '0 10px 25px -3px rgba(0, 0, 0, 0.15), 0 4px 10px -2px rgba(0, 0, 0, 0.08)',
      }
    }
  },
  plugins: [],
}
