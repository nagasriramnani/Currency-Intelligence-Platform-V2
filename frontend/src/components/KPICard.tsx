/**
 * KPICard
 * Enterprise-grade key performance indicator card with count-up animation.
 */

import React, { useEffect, useState, useRef } from 'react';
import { cn, formatCurrency, formatPercentage } from '@/lib/utils';
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';

interface KPICardProps {
  title: string;
  value: number;
  change: number | null;
  changeLabel: string;
  direction: 'Rising' | 'Falling' | 'Flat';
  currency?: string;
  periodStartRate?: number | null;
  className?: string;
}

// Custom hook for count-up animation
function useCountUp(end: number, duration: number = 1500) {
  const [count, setCount] = useState(0);
  const [hasAnimated, setHasAnimated] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !hasAnimated) {
          setHasAnimated(true);
          const startTime = performance.now();
          const startValue = 0;

          const animate = (currentTime: number) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Easing function for smooth animation
            const easeOutQuart = 1 - Math.pow(1 - progress, 4);
            const currentValue = startValue + (end - startValue) * easeOutQuart;

            setCount(currentValue);

            if (progress < 1) {
              requestAnimationFrame(animate);
            }
          };

          requestAnimationFrame(animate);
        }
      },
      { threshold: 0.1 }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => observer.disconnect();
  }, [end, duration, hasAnimated]);

  return { count, ref };
}

export function KPICard({
  title,
  value,
  change,
  changeLabel,
  direction,
  currency,
  periodStartRate,
  className,
}: KPICardProps) {
  const isPositive = change && change > 0;
  const isNegative = change && change < 0;

  // Count-up animation for the main value
  const { count: animatedValue, ref: valueRef } = useCountUp(value, 1200);

  // Count-up animation for the percentage change
  const { count: animatedChange, ref: changeRef } = useCountUp(
    change ? Math.abs(change) : 0,
    1000
  );

  return (
    <div
      ref={valueRef}
      className={cn(
        'glass-card relative overflow-hidden rounded-2xl p-6 group cursor-pointer',
        'transform transition-all duration-500 ease-out',
        'hover:scale-[1.02] hover:-translate-y-1 hover:shadow-2xl',
        className
      )}
    >
      {/* Animated Background Glow Effect - uses accent color */}
      <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full accent-bg-subtle blur-3xl transition-all duration-700 group-hover:scale-150" style={{ opacity: 0.15 }}></div>

      {/* Secondary glow on hover */}
      <div className="absolute -left-10 -bottom-10 h-24 w-24 rounded-full blur-2xl transition-all duration-700 accent-bg-subtle group-hover:opacity-30" style={{ opacity: 0 }}></div>

      <div className="relative z-10 flex justify-between items-start">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-sapphire-300 mb-1 transition-colors duration-300 group-hover:text-sapphire-200">
            {title}
          </p>
          <div className="flex items-baseline gap-2">
            <h3 className="text-3xl font-bold text-white tracking-tight tabular-nums transition-transform duration-300 group-hover:scale-105 origin-left">
              {formatCurrency(animatedValue)}
            </h3>
            {currency && (
              <span className="text-sm font-medium text-sapphire-400 bg-sapphire-900/50 px-2 py-0.5 rounded-md border border-sapphire-700/50 transition-all duration-300 group-hover:bg-sapphire-800/50 group-hover:border-sapphire-600/50">
                {currency}
              </span>
            )}
          </div>
        </div>

        {/* Animated Direction Icon with floating effect */}
        <div
          className={cn(
            "flex h-10 w-10 items-center justify-center rounded-xl border backdrop-blur-sm",
            "transition-all duration-500 ease-out",
            "group-hover:scale-110",
            isPositive
              ? "bg-success/10 border-success/20 text-success animate-bounce-subtle"
              : isNegative
                ? "bg-danger/10 border-danger/20 text-danger animate-bounce-subtle"
                : "bg-sapphire-700/30 border-sapphire-600/30 text-sapphire-300"
          )}
        >
          {isPositive ? (
            <ArrowUpRight className="h-5 w-5 transition-transform duration-300 group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
          ) : isNegative ? (
            <ArrowDownRight className="h-5 w-5 transition-transform duration-300 group-hover:translate-y-0.5 group-hover:translate-x-0.5" />
          ) : (
            <Minus className="h-5 w-5" />
          )}
        </div>
      </div>

      <div ref={changeRef} className="relative z-10 mt-4 flex items-center gap-3">
        {change !== null && (
          <div
            className={cn(
              "flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-sm font-medium border tabular-nums",
              "transition-all duration-300 animate-pop-in",
              "group-hover:scale-105",
              isPositive
                ? "bg-success/5 border-success/10 text-success group-hover:bg-success/10"
                : isNegative
                  ? "bg-danger/5 border-danger/10 text-danger group-hover:bg-danger/10"
                  : "bg-sapphire-700/20 border-sapphire-600/20 text-sapphire-300"
            )}
          >
            <span>
              {change > 0 ? '+' : change < 0 ? '-' : ''}
              {formatPercentage(animatedChange)}
            </span>
          </div>
        )}
        <span className="text-sm text-sapphire-300/80 font-medium transition-colors duration-300 group-hover:text-sapphire-200">
          {changeLabel}
        </span>
        {periodStartRate !== null && periodStartRate !== undefined && (
          <span className="text-xs text-sapphire-400/70 transition-colors duration-300 group-hover:text-sapphire-300/70">
            from {periodStartRate.toFixed(4)}
          </span>
        )}
      </div>

      {/* Animated Bottom accent line */}
      <div
        className={cn(
          "absolute bottom-0 left-0 h-1 w-full transition-all duration-500",
          "opacity-50 group-hover:opacity-100 group-hover:h-1.5",
          isPositive
            ? "bg-gradient-to-r from-success/0 via-success to-success/0"
            : isNegative
              ? "bg-gradient-to-r from-danger/0 via-danger to-danger/0"
              : "accent-gradient"
        )}
      ></div>

      {/* Shimmer effect on hover */}
      <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/5 to-transparent pointer-events-none"></div>
    </div>
  );
}
