// Tailwind Configuration
tailwind.config = {
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                primary: '#f97316', // Orange 500
                secondary: '#ec4899', // Pink 500
                dark: '#0f172a', // Slate 900
            },
            fontFamily: {
                sans: ['Raleway', 'sans-serif'],
                script: ['Dancing Script', 'cursive'],
                interactive: ['Outfit', 'sans-serif'],
            },
            animation: {
                'float': 'float 6s ease-in-out infinite',
            },
            keyframes: {
                float: {
                    '0%, 100%': { transform: 'translateY(0)' },
                    '50%': { transform: 'translateY(-20px)' },
                }
            }
        }
    }
}
