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
        
        // Risk colors (functional)
        'risk-low': 'var(--color-low)',
        'risk-medium': 'var(--color-medium)',
        'risk-high': 'var(--color-high)',
        'risk-severe': 'var(--color-severe)',
      },
      
      // BRUTALIST: Override all border radius to 0
      borderRadius: {
        'none': '0',
        'DEFAULT': '0',
        'sm': '0',
        'md': '0',
        'lg': '0',
        'xl': '0',
        '2xl': '0',
        '3xl': '0',
        'full': '0', // Even 'full' becomes 0
      },
      
      // BRUTALIST: Add hard shadows (no blur)
      boxShadow: {
        'none': 'none',
        'sm': '2px 2px 0 var(--border)',
        'DEFAULT': '4px 4px 0 var(--border)',
        'md': '4px 4px 0 var(--border)',
        'lg': '6px 6px 0 var(--border)',
        'xl': '8px 8px 0 var(--border)',
        '2xl': '10px 10px 0 var(--border)',
        'inner': 'inset 2px 2px 0 var(--border)',
      },
      
      // BRUTALIST: Monospace fonts
      fontFamily: {
        sans: ['"Courier New"', '"IBM Plex Mono"', 'monospace'],
        mono: ['"Courier New"', '"IBM Plex Mono"', 'monospace'],
      },
      
      // BRUTALIST: Thick borders
      borderWidth: {
        'DEFAULT': '2px',
        '0': '0',
        '2': '2px',
        '3': '3px',
        '4': '4px',
      },
      
      // BRUTALIST: No transitions (instant state changes)
      transitionDuration: {
        'DEFAULT': '0ms',
        '0': '0ms',
      },
      
      transitionTimingFunction: {
        'DEFAULT': 'linear',
      },
    },
  },
  plugins: [],
  
  // BRUTALIST: Global overrides
  corePlugins: {
    // Keep border radius at 0
    borderRadius: true,
  },
}
