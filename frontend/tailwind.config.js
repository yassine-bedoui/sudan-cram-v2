/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        background: 'var(--background)',
        foreground: 'var(--foreground)',
        surface: 'var(--surface)',
        border: 'var(--border)',

        // Brand colors - UPDATED
        'brand-orange': '#F37420',  // Conflict Risk / Primary brand
        'brand-teal': '#049787',    // Climate Risk / Secondary brand

        // Risk colors - UPDATED to use brand colors
        'conflict': '#F37420',
        'climate': '#049787',
        'risk-low': '#22c55e',
        'risk-medium': '#fbbf24',
        'risk-high': '#F37420',
        'risk-severe': '#dc2626',
      },

      // Use Inter font - UPDATED
      fontFamily: {
        sans: ['var(--font-inter)', 'Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['"Courier New"', 'monospace'],
      },

      // Keep sharp borders (no changes)
      borderRadius: {
        'none': '0',
        'DEFAULT': '0',
        'sm': '0',
        'md': '0',
        'lg': '0',
        'xl': '0',
        '2xl': '0',
        '3xl': '0',
        'full': '0',
      },

      // Standard borders (no changes)
      borderWidth: {
        'DEFAULT': '1px',
        '0': '0',
        '2': '2px',
        '3': '3px',
        '4': '4px',
      },

      // Letter spacing for uppercase text (no changes)
      letterSpacing: {
        tighter: '-0.05em',
        tight: '-0.025em',
        normal: '0',
        wide: '0.025em',
        wider: '0.05em',
        widest: '0.1em',
      },
    },
  },
  plugins: [],
}
