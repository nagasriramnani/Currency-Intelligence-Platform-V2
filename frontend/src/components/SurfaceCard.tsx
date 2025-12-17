/**
 * SurfaceCard
 * Shared container with consistent padding, border, and hover styles.
 */

import React from 'react';
import { cn } from '@/lib/utils';

interface SurfaceCardProps {
  children: React.ReactNode;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

const paddingMap: Record<NonNullable<SurfaceCardProps['padding']>, string> = {
  none: '',
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
};

export function SurfaceCard({
  children,
  className,
  padding = 'md',
}: SurfaceCardProps) {
  return (
    <div
      className={cn(
        // Enterprise dark glass styling - matches other dashboard cards
        'rounded-xl border border-sapphire-700/30 bg-sapphire-800/40 backdrop-blur-md',
        'shadow-lg shadow-sapphire-950/20',
        // Enhanced hover animations - lift, scale, and glow
        'transition-all duration-500 ease-out',
        'hover:bg-sapphire-800/50 hover:border-sapphire-600/40',
        'hover:-translate-y-1 hover:shadow-xl hover:shadow-sapphire-500/10',
        // Relative for shimmer effect
        'relative overflow-hidden group',
        paddingMap[padding],
        className,
      )}
    >
      {children}
      {/* Shimmer effect on hover */}
      <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/[0.03] to-transparent pointer-events-none"></div>
    </div>
  );
}


