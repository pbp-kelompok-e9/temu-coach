/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
      './templates/**/*.html', 
      './**/templates/**/*.html', 
  ],
  theme: {
    extend: {
      colors: {
        'primary-blue': '#003E85',
        'primary-orange': '#DE3400',
        'primary-orange-dark': '#c42e00', 
      },
      fontFamily: { 
        sans: ['"Plus Jakarta Sans"', 'Arial', 'sans-serif'],
      },
    },
  },
  plugins: [],
}