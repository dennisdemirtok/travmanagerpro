import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        trav: {
          bg: "#0C0E13",
          card: "#141720",
          hover: "#1A1E2A",
          active: "#1E2333",
          border: "#252A3A",
          "border-light": "#2E3448",
          gold: "#D4A853",
          "gold-dim": "#B8923D",
          "gold-bright": "#F0C864",
        },
      },
    },
  },
  plugins: [],
};
export default config;
