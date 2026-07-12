/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f4f5fa',
          100: '#eaecf4',
          200: '#d0d5e6',
          300: '#a6b1cf',
          400: '#7587b3',
          500: '#526497',
          600: '#3f4d7a',
          700: '#333e62',
          800: '#2b334f',
          900: '#282d43',
          950: '#1b1d2a',
        },
        forest: {
          50: '#f3f8f6',
          100: '#e6f2ed',
          200: '#cce6db',
          300: '#a3d1bf',
          400: '#70b39c',
          500: '#4c9980',
          600: '#3b7a66',
          700: '#306253',
          800: '#264f43',
          900: '#0f2a21', // Dark pine green sidebar
          950: '#071510',
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        outfit: ['Outfit', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
