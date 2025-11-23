/**
 * SkeletonBlock
 * Simple animated placeholder used while cards/charts load.
 */

import React from 'react';
import { cn } from '@/lib/utils';

interface SkeletonBlockProps {
  className?: string;
}

export function SkeletonBlock({ className }: SkeletonBlockProps) {
  return (
    <div
      className={cn(
        'animate-pulse rounded-2xl bg-slate-200/70',
        className,
      )}
    />
  );
}


