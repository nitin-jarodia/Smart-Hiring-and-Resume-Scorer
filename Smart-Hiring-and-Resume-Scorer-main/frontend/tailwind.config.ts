import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      colors: {
        brand: {
          DEFAULT: "#2F5BEA",
          hover: "#2448C9",
          soft: "#E8EEFF",
          "dark-soft": "#16203A",
        },
        sage: {
          DEFAULT: "#4F7A65",
          dark: "#7FA68F",
        },
        surface: {
          primary: "#F7F8FA",
          card: "#FFFFFF",
          "dark-primary": "#0B1220",
          "dark-card": "#111827",
          "dark-sidebar": "#0F172A",
        },
        success: { DEFAULT: "#1F8A5B", dark: "#34D399" },
        warning: { DEFAULT: "#C58A12", dark: "#FBBF24" },
        danger: { DEFAULT: "#C94B4B", dark: "#F87171" },
        info: { DEFAULT: "#3B82F6", dark: "#60A5FA" },
      },
      borderRadius: {
        card: "14px",
      },
      boxShadow: {
        card: "0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
        "card-hover": "0 4px 12px rgba(0,0,0,0.08)",
      },
    },
  },
  plugins: [],
};

export default config;
