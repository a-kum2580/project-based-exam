/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        gold: {
          DEFAULT: "#d4a853",
          light: "#e8c874",
          dim: "#a07c3a",
          dark: "#7a5a2a",
        },
        accent: {
          DEFAULT: "#e04040",
          hover: "#f05050",
        },
        surface: {
          0: "#06060b",
          1: "#0c0c14",
          2: "#13131e",
          3: "#1a1a28",
          4: "#222233",
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "Georgia", "serif"],
        body: ["var(--font-body)", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
