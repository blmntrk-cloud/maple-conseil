/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        schmidt: {
          dark: '#333333',
          grey: '#666666',
          light: '#F5F5F5',
          orange: '#E86A1E',
          'orange-light': '#F5B06B',
        },
      },
    },
  },
  plugins: [],
};
