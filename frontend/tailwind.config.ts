import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      colors: {
        trav: {
          bg: "#0C0E13",
          "bg-elevated": "#10131A",
          card: "#141720",
          "card-hover": "#181C28",
          hover: "#1A1E2A",
          active: "#1E2333",
          border: "#252A3A",
          "border-light": "#2E3448",
          "border-subtle": "#1E2230",
          gold: "#D4A853",
          "gold-dim": "#B8923D",
          "gold-bright": "#F0C864",
          "gold-muted": "#A68637",
          accent: "#D4A853",
        },
      },
      boxShadow: {
        'card': '0 1px 3px rgba(0, 0, 0, 0.3), 0 1px 2px rgba(0, 0, 0, 0.2)',
        'card-hover': '0 4px 12px rgba(0, 0, 0, 0.4), 0 2px 4px rgba(0, 0, 0, 0.3)',
        'gold-glow': '0 0 12px rgba(212, 168, 83, 0.15)',
        'inner-light': 'inset 0 1px 0 rgba(255, 255, 255, 0.03)',
      },
      borderRadius: {
        'xl': '12px',
        '2xl': '16px',
      },
    },
  },
  plugins: [],
};
export default config;
