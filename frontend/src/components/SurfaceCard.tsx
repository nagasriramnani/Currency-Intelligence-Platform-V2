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
        'rounded-2xl border border-slate-200 bg-white shadow-sm transition-shadow duration-200 hover:shadow-md',
        paddingMap[padding],
        className,
      )}
    >
      {children}
    </div>
  );
}


