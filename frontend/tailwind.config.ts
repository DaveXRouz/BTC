import type { Config } from "tailwindcss";

// Colors extracted from V3 gui/theme.py
const npsColors = {
  bg: {
    DEFAULT: "#0d1117",
    card: "#161b22",
    input: "#21262d",
    hover: "#1c2128",
    button: "#1f6feb",
    danger: "#da3633",
    success: "#238636",
  },
  border: "#30363d",
  text: {
    DEFAULT: "#c9d1d9",
    dim: "#8b949e",
    bright: "#f0f6fc",
  },
  gold: {
    DEFAULT: "#d4a017",
    dim: "#a67c00",
  },
  accent: "#58a6ff",
  success: "#3fb950",
  warning: "#d29922",
  error: "#f85149",
  purple: "#a371f7",
  score: {
    low: "#f85149",
    mid: "#d29922",
    high: "#238636",
    peak: "#d4a017",
  },
  ai: {
    bg: "#1a1033",
    border: "#7c3aed",
    text: "#c4b5fd",
    accent: "#a78bfa",
  },
  oracle: {
    bg: "#0f1a2e",
    border: "#1e3a5f",
    accent: "#4fc3f7",
  },
};

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        nps: npsColors,
      },
      fontFamily: {
        sans: ["Inter", "Segoe UI", "Helvetica", "sans-serif"],
        mono: ["JetBrains Mono", "Consolas", "Courier", "monospace"],
      },
    },
  },
  plugins: [],
} satisfies Config;
