/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        base: {
          950: "#0A0E14",
          900: "#0F141B",
          800: "#161C26",
          700: "#1F2733",
          600: "#2B3542",
        },
        signal: {
          ok: "#3FB68B",
          warn: "#E0A526",
          crit: "#E2574C",
          info: "#4C8BF5",
        },
        accent: {
          DEFAULT: "#5EEAD4",
          muted: "#2DD4BF",
        },
        ink: {
          primary: "#E7ECF3",
          secondary: "#9AA7B8",
          muted: "#5B6778",
        },
      },
      fontFamily: {
        display: ["'JetBrains Mono'", "monospace"],
        body: ["'Inter'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      borderRadius: {
        sm: "4px",
        DEFAULT: "6px",
        lg: "10px",
      },
    },
  },
  plugins: [],
};
