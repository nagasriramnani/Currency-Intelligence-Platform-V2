'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
    Activity,
    LayoutDashboard,
    LineChart,
    Shield,
    Settings
} from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Navigation bar component with dynamic accent color support.
 * The active state uses the theme accent color.
 */
export function NavBar() {
    const pathname = usePathname();

    const navLinks = [
        { href: '/', label: 'Dashboard', icon: LayoutDashboard },
        { href: '/analysis', label: 'Analysis', icon: LineChart },
        { href: '/risk', label: 'Risk', icon: Shield },
        { href: '/settings', label: 'Settings', icon: Settings },
    ];

    return (
        <header className="sticky top-0 z-50 w-full border-b border-sapphire-700/50 bg-sapphire-900/80 backdrop-blur-xl">
            <div className="container mx-auto px-4 h-16 flex items-center justify-between">
                {/* Logo Section */}
                <Link href="/" className="flex items-center gap-3 hover:opacity-90 transition-opacity">
                    <div className="relative flex h-10 w-10 items-center justify-center rounded-xl accent-gradient shadow-lg">
                        <Activity className="h-6 w-6 text-white" />
                        <div className="absolute -bottom-1 -right-1 h-3 w-3 rounded-full bg-success border-2 border-sapphire-900 animate-pulse"></div>
                    </div>
                    <div className="flex flex-col">
                        <h1 className="text-xl font-bold tracking-tight text-white">
                            Sapphire<span className="accent-text-light">Intelligence</span>
                        </h1>
                        <span className="text-xs font-medium text-sapphire-300 tracking-wide uppercase">
                            Currency Operations
                        </span>
                    </div>
                </Link>

                {/* Navigation */}
                <nav className="flex items-center gap-1">
                    {navLinks.map((link) => {
                        const isActive = pathname === link.href;
                        const Icon = link.icon;

                        return (
                            <Link
                                key={link.href}
                                href={link.href}
                                className={cn(
                                    'flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all',
                                    isActive
                                        ? 'accent-bg-subtle text-white shadow-sm accent-border-light border'
                                        : 'text-sapphire-200 hover:bg-sapphire-800/30 hover:text-white',
                                )}
                            >
                                <Icon className={cn("h-4 w-4", isActive && "accent-text-light")} />
                                {link.label}
                            </Link>
                        );
                    })}
                </nav>
            </div>
        </header>
    );
}
