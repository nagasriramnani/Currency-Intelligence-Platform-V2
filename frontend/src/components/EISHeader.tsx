'use client';

/**
 * EIS Header Component
 * Navigation header for EIS pages with AI Daily News access
 * Matches the main dashboard header styling
 */

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
    Activity,
    Layout,
    Settings,
    LayoutDashboard,
    LineChart,
    Newspaper,
    Sparkles
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';

export function EISHeader() {
    const pathname = usePathname();

    const navItems = [
        { href: '/', label: 'Dashboard', icon: LayoutDashboard },
        { href: '/analysis', label: 'Analysis', icon: LineChart },
        { href: '/risk', label: 'Risk', icon: Activity },
        { href: '/eis', label: 'EIS', icon: Layout },
        { href: '/settings', label: 'Settings', icon: Settings },
    ];

    return (
        <motion.header
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.4, ease: 'easeOut' }}
            className="sticky top-0 z-50 w-full border-b border-sapphire-700/50 bg-sapphire-900/80 backdrop-blur-xl"
        >
            <div className="container mx-auto px-4 h-16 flex items-center justify-between">
                {/* Logo Section */}
                <Link href="/" className="flex items-center gap-3 group">
                    <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-sapphire-600 to-sapphire-400 shadow-lg shadow-sapphire-500/20 group-hover:shadow-sapphire-500/40 transition-all duration-300">
                        <Activity className="h-6 w-6 text-white" />
                        <div className="absolute -bottom-1 -right-1 h-3 w-3 rounded-full bg-success border-2 border-sapphire-900 animate-pulse"></div>
                    </div>
                    <div className="flex flex-col">
                        <h1 className="text-xl font-bold tracking-tight text-white">
                            Sapphire<span className="text-sapphire-400">Intelligence</span>
                        </h1>
                        <span className="text-xs font-medium text-sapphire-300 tracking-wide uppercase">
                            EIS Investment Scanner
                        </span>
                    </div>
                </Link>

                {/* Navigation - Desktop */}
                <nav className="hidden md:flex items-center gap-1">
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = pathname === item.href || (item.href === '/eis' && pathname?.startsWith('/eis'));

                        return (
                            <Link
                                key={item.href}
                                href={item.href}
                                className={cn(
                                    'flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200',
                                    isActive
                                        ? 'bg-sapphire-800/50 text-white shadow-sm ring-1 ring-sapphire-700/50'
                                        : 'text-sapphire-200 hover:bg-sapphire-800/30 hover:text-white',
                                )}
                            >
                                <Icon className="h-4 w-4" />
                                {item.label}
                            </Link>
                        );
                    })}
                </nav>

                {/* Actions */}
                <div className="flex items-center gap-3">
                    {/* Company Research Agent Button */}
                    <Link href="/research">
                        <motion.button
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            className={cn(
                                'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300',
                                pathname === '/research'
                                    ? 'bg-gradient-to-r from-indigo-600 to-violet-500 text-white shadow-lg shadow-indigo-500/30'
                                    : 'bg-gradient-to-r from-indigo-600/80 to-violet-500/80 text-white hover:from-indigo-500 hover:to-violet-400 shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/40'
                            )}
                        >
                            <Newspaper className="h-4 w-4" />
                            <span className="hidden sm:inline">Research Agent</span>
                            <span className="sm:hidden">Research</span>
                        </motion.button>
                    </Link>

                    {/* AI Daily News Button */}
                    <Link href="/eis/news">
                        <motion.button
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            className={cn(
                                'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300',
                                pathname === '/eis/news'
                                    ? 'bg-gradient-to-r from-purple-600 to-sapphire-500 text-white shadow-lg shadow-purple-500/30'
                                    : 'bg-gradient-to-r from-purple-600/80 to-sapphire-500/80 text-white hover:from-purple-500 hover:to-sapphire-400 shadow-lg shadow-purple-500/20 hover:shadow-purple-500/40'
                            )}
                        >
                            <Sparkles className="h-4 w-4" />
                            <span className="hidden sm:inline">AI Daily News</span>
                            <span className="sm:hidden">News</span>
                        </motion.button>
                    </Link>

                    {/* Current Date */}
                    <div className="hidden lg:flex flex-col items-end">
                        <span className="text-xs text-sapphire-300">Today</span>
                        <span className="text-xs font-mono text-sapphire-100">
                            {new Date().toLocaleDateString('en-GB', {
                                day: 'numeric',
                                month: 'short',
                                year: 'numeric'
                            })}
                        </span>
                    </div>
                </div>
            </div>
        </motion.header>
    );
}
