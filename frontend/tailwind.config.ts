import type { Config } from "tailwindcss";
import rtl from "tailwindcss-rtl";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        nps: {
          bg: {
            DEFAULT: "var(--nps-bg)",
            card: "var(--nps-bg-card)",
            input: "var(--nps-bg-input)",
            hover: "var(--nps-bg-hover)",
            sidebar: "var(--nps-bg-sidebar)",
            button: "#1f6feb",
            danger: "#da3633",
            success: "#238636",
          },
          border: "var(--nps-border)",
          text: {
            DEFAULT: "var(--nps-text)",
            dim: "var(--nps-text-dim)",
            bright: "var(--nps-text-bright)",
          },
          accent: {
            DEFAULT: "var(--nps-accent)",
            hover: "var(--nps-accent-hover)",
            dim: "var(--nps-accent-dim)",
          },
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
        },
      },
      fontFamily: {
        sans: ["Inter", "Segoe UI", "Helvetica", "sans-serif"],
        mono: ["JetBrains Mono", "Consolas", "Courier", "monospace"],
      },
      ringColor: {
        focus: "var(--nps-accent)",
      },
      boxShadow: {
        nps: "var(--nps-shadow)",
      },
      animation: {
        "fade-in-up": "fadeInUp 0.4s ease-out forwards",
        "slide-in-right": "slideInRight 0.3s ease-out",
        "slide-in-left": "slideInLeft 0.3s ease-out",
        shimmer: "shimmer 1.5s ease-in-out infinite",
      },
      keyframes: {
        fadeInUp: {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideInRight: {
          "0%": { transform: "translateX(100%)", opacity: "0" },
          "100%": { transform: "translateX(0)", opacity: "1" },
        },
        slideInLeft: {
          "0%": { transform: "translateX(-100%)", opacity: "0" },
          "100%": { transform: "translateX(0)", opacity: "1" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
    },
  },
  plugins: [rtl],
} satisfies Config;
