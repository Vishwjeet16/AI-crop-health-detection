import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#F3F6EE",
        "bg-alt": "#EAF0E0",
        paper: "#FFFFFF",
        ink: "#16241C",
        "ink-soft": "#3D4F41",
        line: "#DAE2CD",
        forest: {
          DEFAULT: "#1B4332",
          light: "#2D5F45",
          dark: "#0F2C21",
        },
        growth: {
          DEFAULT: "#4C7A3F",
          light: "#8FBF7B",
          dark: "#365A2C",
        },
        marigold: {
          DEFAULT: "#DFA23C",
          light: "#F2C879",
          dark: "#B57F26",
        },
        rust: {
          DEFAULT: "#B4432E",
          light: "#E2A093",
          dark: "#832F20",
        },
      },
      fontFamily: {
        display: ["var(--font-fraunces)", "Georgia", "serif"],
        sans: ["var(--font-plex-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-plex-mono)", "ui-monospace", "monospace"],
      },
      borderRadius: {
        sm: "6px",
        md: "10px",
        lg: "16px",
        xl: "22px",
      },
      keyframes: {
        "bracket-in": {
          "0%": { opacity: "0", transform: "scale(1.08)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        "scan-sweep": {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100%)" },
        },
      },
      animation: {
        "bracket-in": "bracket-in 0.5s ease-out",
        "scan-sweep": "scan-sweep 1.8s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
export default config;
