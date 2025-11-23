/**
 * SectionHeader
 * Provides a consistent title/subtitle block with optional action slot.
 */

import React from 'react';
import { cn } from '@/lib/utils';
import { LucideIcon } from 'lucide-react';

interface SectionHeaderProps {
  title: string;
  description?: string;
  subtitle?: string; // Keeping for backward compatibility
  icon?: LucideIcon;
  action?: React.ReactNode;
  className?: string;
}

export function SectionHeader({
  title,
  description,
  subtitle,
  icon: Icon,
  action,
  className,
}: SectionHeaderProps) {
  return (
    <div
      className={cn(
        'flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between',
        className,
      )}
    >
      <div className="flex items-start gap-3">
        {Icon && (
          <div className="p-2 rounded-lg bg-sapphire-800/50 border border-sapphire-700/50 text-sapphire-400">
            <Icon className="h-5 w-5" />
          </div>
        )}
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">{title}</h2>
          {(description || subtitle) && (
            <p className="text-sm text-sapphire-200 mt-1">{description || subtitle}</p>
          )}
        </div>
      </div>
      {action && <div className="flex-shrink-0">{action}</div>}
    </div>
  );
}


