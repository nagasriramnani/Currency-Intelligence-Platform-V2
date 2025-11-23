/**
 * KPI Card Component
 * Displays key metrics with direction indicators
 */

import React from 'react';
import { cn, formatCurrency, formatPercentage, getDirectionIcon, getChangeColor } from '@/lib/utils';
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';

interface KPICardProps {
  title: string;
  value: number;
  change: number | null;
  changeLabel: string;
  direction: 'Rising' | 'Falling' | 'Flat';
  currency?: string;
  className?: string;
}

export function KPICard({
  title,
  value,
  change,
  changeLabel,
  direction,
  currency,
  className,
}: KPICardProps) {
  // Custom direction logic for more granular control
  const isPositive = change && change > 0;
  const isNegative = change && change < 0;

  return (
    <div
      className={cn(
        'glass-card relative overflow-hidden rounded-2xl p-6 group',
        className
      )}
    >
      {/* Background Glow Effect */}
      <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-sapphire-500/10 blur-3xl group-hover:bg-sapphire-500/20 transition-all duration-500"></div>

      <div className="relative z-10 flex justify-between items-start">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-sapphire-300 mb-1">
            {title}
          </p>
          <div className="flex items-baseline gap-2">
            <h3 className="text-3xl font-bold text-white tracking-tight">
              {formatCurrency(value)}
            </h3>
            {currency && (
              <span className="text-sm font-medium text-sapphire-400 bg-sapphire-900/50 px-2 py-0.5 rounded-md border border-sapphire-700/50">
                {currency}
              </span>
            )}
          </div>
        </div>

        <div className={cn(
          "flex h-10 w-10 items-center justify-center rounded-xl border backdrop-blur-sm transition-all duration-300",
          isPositive ? "bg-success/10 border-success/20 text-success" :
            isNegative ? "bg-danger/10 border-danger/20 text-danger" :
              "bg-sapphire-700/30 border-sapphire-600/30 text-sapphire-300"
        )}>
          {isPositive ? <ArrowUpRight className="h-5 w-5" /> :
            isNegative ? <ArrowDownRight className="h-5 w-5" /> :
              <Minus className="h-5 w-5" />}
        </div>
      </div>

      <div className="relative z-10 mt-4 flex items-center gap-3">
        {change !== null && (
          <div className={cn(
            "flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-sm font-medium border",
            isPositive ? "bg-success/5 border-success/10 text-success" :
              isNegative ? "bg-danger/5 border-danger/10 text-danger" :
                "bg-sapphire-700/20 border-sapphire-600/20 text-sapphire-300"
          )}>
            <span>{change > 0 ? '+' : ''}{formatPercentage(change)}</span>
          </div>
        )}
        <span className="text-sm text-sapphire-300/80 font-medium">
          {changeLabel}
        </span>
      </div>

      {/* Bottom accent line */}
      <div className={cn(
        "absolute bottom-0 left-0 h-1 w-full transition-all duration-500 opacity-50 group-hover:opacity-100",
        isPositive ? "bg-gradient-to-r from-success/0 via-success to-success/0" :
          isNegative ? "bg-gradient-to-r from-danger/0 via-danger to-danger/0" :
            "bg-gradient-to-r from-sapphire-400/0 via-sapphire-400 to-sapphire-400/0"
      )}></div>
    </div>
  );
}


