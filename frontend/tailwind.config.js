/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'primary': '#8B5CF6',
        'secondary': '#10B981',
        'background': '#111827',
        'surface': '#1F2937',
        'text-primary': '#F9FAFB',
        'text-secondary': '#9CA3AF',
        'accent': '#3B82F6',
      },
    },
  },
  plugins: [],
}
