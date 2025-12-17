'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Activity,
  Layout,
  Settings,
  Bell,
  Menu,
  LayoutDashboard,
  LineChart
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface HeaderProps {
  lastUpdate: string | null;
  onRefresh: () => void;
  isRefreshing: boolean;
  presentationMode: boolean;
  setPresentationMode: (mode: boolean) => void;
}

export function Header({
  lastUpdate,
  onRefresh,
  isRefreshing,
  presentationMode,
  setPresentationMode
}: HeaderProps) {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 w-full border-b border-sapphire-700/50 bg-sapphire-900/80 backdrop-blur-xl">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        {/* Logo Section */}
        <div className="flex items-center gap-3">
          <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-sapphire-600 to-sapphire-400 shadow-lg shadow-sapphire-500/20">
            <Activity className="h-6 w-6 text-white" />
            <div className="absolute -bottom-1 -right-1 h-3 w-3 rounded-full bg-success border-2 border-sapphire-900 animate-pulse"></div>
          </div>
          <div className="flex flex-col">
            <h1 className="text-xl font-bold tracking-tight text-white">
              Sapphire<span className="text-sapphire-400">Intelligence</span>
            </h1>
            <span className="text-xs font-medium text-sapphire-300 tracking-wide uppercase">
              Currency Operations
            </span>
          </div>
        </div>

        {/* Navigation - Desktop */}
        <nav className="hidden md:flex items-center gap-1">
          <Link
            href="/"
            className={cn(
              'flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all',
              pathname === '/'
                ? 'bg-sapphire-800/50 text-white shadow-sm ring-1 ring-sapphire-700/50'
                : 'text-sapphire-200 hover:bg-sapphire-800/30 hover:text-white',
            )}
          >
            <LayoutDashboard className="h-4 w-4" />
            Dashboard
          </Link>
          <Link
            href="/analysis"
            className={cn(
              'flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all',
              pathname === '/analysis'
                ? 'bg-sapphire-800/50 text-white shadow-sm ring-1 ring-sapphire-700/50'
                : 'text-sapphire-200 hover:bg-sapphire-800/30 hover:text-white',
            )}
          >
            <LineChart className="h-4 w-4" />
            Analysis
          </Link>
          <Link
            href="/risk"
            className={cn(
              'flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all',
              pathname === '/risk'
                ? 'bg-sapphire-800/50 text-white shadow-sm ring-1 ring-sapphire-700/50'
                : 'text-sapphire-200 hover:bg-sapphire-800/30 hover:text-white',
            )}
          >
            <Activity className="h-4 w-4" />
            Risk
          </Link>
          <Link
            href="/settings"
            className={cn(
              'flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all',
              pathname === '/settings'
                ? 'bg-sapphire-800/50 text-white shadow-sm ring-1 ring-sapphire-700/50'
                : 'text-sapphire-200 hover:bg-sapphire-800/30 hover:text-white',
            )}
          >
            <Settings className="h-4 w-4" />
            Settings
          </Link>
        </nav>

        {/* Actions */}
        <div className="flex items-center gap-4">
          <div className="hidden lg:flex flex-col items-end mr-2">
            <span className="text-xs text-sapphire-300">Last Updated</span>
            <span className="text-xs font-mono text-sapphire-100">
              {lastUpdate ? new Date(lastUpdate).toLocaleString() : 'Never'}
            </span>
          </div>

          <div className="h-8 w-px bg-sapphire-700/50 hidden lg:block"></div>

          <button
            onClick={() => setPresentationMode(!presentationMode)}
            className={cn(
              'relative p-2 rounded-lg transition-all duration-200',
              presentationMode
                ? 'bg-sapphire-500 text-white shadow-lg shadow-sapphire-500/25'
                : 'text-sapphire-300 hover:text-white hover:bg-sapphire-800/50'
            )}
            title="Toggle Presentation Mode"
          >
            <Layout className="h-5 w-5" />
            {presentationMode && (
              <span className="absolute -top-1 -right-1 flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-white"></span>
              </span>
            )}
          </button>

          <button className="p-2 text-sapphire-300 hover:text-white hover:bg-sapphire-800/50 rounded-lg transition-all relative">
            <Bell className="h-5 w-5" />
            <span className="absolute top-2 right-2 h-2 w-2 rounded-full bg-danger border border-sapphire-900"></span>
          </button>

          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all',
              isRefreshing
                ? 'bg-sapphire-800/50 text-sapphire-400 cursor-not-allowed'
                : 'bg-sapphire-500 text-white hover:bg-sapphire-400 shadow-lg shadow-sapphire-500/20 hover:shadow-sapphire-500/30'
            )}
          >
            <Activity className={cn('h-4 w-4', isRefreshing && 'animate-spin')} />
            {isRefreshing ? 'Syncing...' : 'Refresh Data'}
          </button>

          <button className="md:hidden p-2 text-sapphire-300 hover:text-white">
            <Menu className="h-6 w-6" />
          </button>
        </div>
      </div>
    </header>
  );
}
