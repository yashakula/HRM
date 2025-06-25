/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Override gray colors to be darker by default for better contrast
        gray: {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#6b7280', // Originally #9ca3af - now darker
          500: '#374151', // Originally #6b7280 - now darker  
          600: '#1f2937', // Originally #4b5563 - now darker
          700: '#111827', // Originally #374151 - now darker
          800: '#111827', // Originally #1f2937 - keeping dark
          900: '#111827', // Originally #111827 - keeping darkest
        },
      },
    },
  },
  plugins: [],
}