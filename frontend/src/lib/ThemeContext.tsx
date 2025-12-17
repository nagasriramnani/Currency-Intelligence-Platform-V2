'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

export type AccentColor = 'sapphire' | 'emerald' | 'violet' | 'rose';

interface ThemeContextType {
    accentColor: AccentColor;
    setAccentColor: (color: AccentColor) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const accentColors: Record<AccentColor, { primary: string; light: string }> = {
    sapphire: { primary: '59 130 246', light: '96 165 250' },   // Blue
    emerald: { primary: '16 185 129', light: '52 211 153' },    // Green
    violet: { primary: '139 92 246', light: '167 139 250' },    // Purple
    rose: { primary: '244 63 94', light: '251 113 133' },       // Red/Pink
};

export function ThemeProvider({ children }: { children: React.ReactNode }) {
    const [accentColor, setAccentColor] = useState<AccentColor>('sapphire');

    // Load saved theme from localStorage
    useEffect(() => {
        const saved = localStorage.getItem('theme-accent') as AccentColor;
        if (saved && accentColors[saved]) {
            setAccentColor(saved);
        }
    }, []);

    // Apply CSS variables when accent changes
    useEffect(() => {
        const colors = accentColors[accentColor];
        document.documentElement.style.setProperty('--accent-primary', colors.primary);
        document.documentElement.style.setProperty('--accent-light', colors.light);
        localStorage.setItem('theme-accent', accentColor);
    }, [accentColor]);

    return (
        <ThemeContext.Provider value={{ accentColor, setAccentColor }}>
            {children}
        </ThemeContext.Provider>
    );
}

export function useTheme() {
    const context = useContext(ThemeContext);
    if (!context) {
        throw new Error('useTheme must be used within a ThemeProvider');
    }
    return context;
}
