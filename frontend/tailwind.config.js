/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // Studygram Color Palette
      colors: {
        // Backgrounds - Paper tones (Light)
        "paper-cream": "#FFF7EA",
        "paper-white": "#FFFAF3",
        "paper-warm": "#f9f0e5",
        "dot-grid": "#D7C2A8",

        // Dark mode backgrounds
        "dark-bg": "#1a1a2e",
        "dark-surface": "#16213e",
        "dark-card": "#0f3460",
        "dark-border": "#533483",

        // Ink & Text
        "ink-primary": "#1F2937",
        "ink-secondary": "#4B5563",
        "ink-dark": "#e2e8f0",
        "ink-dark-secondary": "#94a3b8",
        "accent-rose": "#BE123C",
        "accent-blue": "#0369A1",
        "accent-pink": "#f472b6",
        "accent-cyan": "#22d3ee",

        // Highlight Pastels
        "hl-yellow": "rgba(255, 245, 157, 0.9)",
        "hl-blue": "rgba(179, 229, 252, 0.9)",
        "hl-pink": "rgba(255, 205, 210, 0.9)",
        "hl-green": "rgba(200, 230, 201, 0.9)",

        // Sticky Note colors
        "sticky-yellow": "#fff9c4",
        "sticky-pink": "#fce4ec",
        "sticky-blue": "#e3f2fd",
        "sticky-green": "#e8f5e9",

        // Dark sticky notes
        "sticky-dark-yellow": "#3d3d1a",
        "sticky-dark-pink": "#3d1a2e",
        "sticky-dark-blue": "#1a2e3d",
        "sticky-dark-green": "#1a3d2e",

        // UI accents
        "washi-red": "rgba(255, 100, 100, 0.3)",
        "washi-blue": "rgba(100, 149, 237, 0.3)",
        "washi-green": "rgba(144, 238, 144, 0.3)",
      },

      // Studygram Typography
      fontFamily: {
        script: ["Pacifico", "cursive"],
        hand: ["Mali", "cursive"],
        note: ["Patrick Hand", "cursive"],
      },

      // Hand-drawn border radius
      borderRadius: {
        hand: "255px 15px 225px 15px / 15px 225px 15px 255px",
        "hand-sm": "125px 10px 115px 10px / 10px 115px 10px 125px",
      },

      // Animations
      animation: {
        float: "float 3s ease-in-out infinite",
        wiggle: "wiggle 0.5s ease-in-out",
        pop: "pop 0.3s ease-out",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-5px)" },
        },
        wiggle: {
          "0%, 100%": { transform: "rotate(-2deg)" },
          "50%": { transform: "rotate(2deg)" },
        },
        pop: {
          "0%": { transform: "scale(0.95)", opacity: "0" },
          "100%": { transform: "scale(1)", opacity: "1" },
        },
      },

      // Box shadows for hand-drawn feel
      boxShadow: {
        hand: "6px 6px 0px #1F2937",
        "hand-sm": "3px 3px 0px #1F2937",
        sticky: "3px 3px 10px rgba(0, 0, 0, 0.1)",
        "sticky-hover": "10px 10px 20px rgba(0, 0, 0, 0.15)",
      },
    },
  },
  plugins: [],
};
