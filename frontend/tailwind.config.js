/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'gritsee-orange': '#F27405',
        'gritsee-dark': '#1A1A1A',
      },
      fontFamily:{
        sans: ['Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
}