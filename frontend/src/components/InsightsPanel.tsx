/**
 * Insights Panel Component
 * Displays AI-generated narrative insights
 */

import React from 'react';
import { Sparkles, TrendingUp, AlertCircle, Info } from 'lucide-react';
import { SkeletonBlock } from '@/components/SkeletonBlock';

interface InsightsPanelProps {
  currency: string;
  insights: string[];
  isLoading?: boolean;
}

export function InsightsPanel({ currency, insights, isLoading }: InsightsPanelProps) {
  if (isLoading) {
    return (
      <div className="glass-card rounded-2xl p-6 h-full">
        <div className="flex items-center gap-2 pb-6 border-b border-sapphire-700/30 mb-6">
          <Sparkles className="h-5 w-5 text-sapphire-400 animate-pulse-slow" />
          <h3 className="text-lg font-semibold text-white tracking-wide">
            AI Intelligence <span className="text-sapphire-400">· {currency}</span>
          </h3>
        </div>
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <SkeletonBlock key={i} className="h-20 bg-sapphire-800/50" />
          ))}
        </div>
      </div>
    );
  }

  if (!insights || insights.length === 0) {
    return (
      <div className="glass-card rounded-2xl p-6 h-full">
        <div className="flex items-center gap-2 pb-6 border-b border-sapphire-700/30 mb-6">
          <Sparkles className="h-5 w-5 text-sapphire-400" />
          <h3 className="text-lg font-semibold text-white tracking-wide">
            AI Intelligence <span className="text-sapphire-400">· {currency}</span>
          </h3>
        </div>
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <Info className="h-12 w-12 text-sapphire-600 mb-4" />
          <p className="text-sapphire-300">No insights available for this selection.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card rounded-2xl p-6 h-full">
      <div className="flex items-center gap-2 pb-6 border-b border-sapphire-700/30 mb-6">
        <div className="relative">
          <Sparkles className="h-5 w-5 text-sapphire-400" />
          <span className="absolute -top-1 -right-1 flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-sapphire-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-sapphire-500"></span>
          </span>
        </div>
        <h3 className="text-lg font-semibold text-white tracking-wide">
          AI Intelligence <span className="text-sapphire-400">· {currency}</span>
        </h3>
      </div>

      <div className="space-y-4">
        {insights.map((insight, index) => (
          <div
            key={index}
            className="group relative flex gap-4 rounded-xl bg-sapphire-900/40 border border-sapphire-700/30 p-4 hover:bg-sapphire-800/60 hover:border-sapphire-600/50 transition-all duration-300"
          >
            <div className="mt-1 flex-shrink-0">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sapphire-800/80 text-sapphire-300 border border-sapphire-700/50 group-hover:text-white group-hover:border-sapphire-500/50 transition-colors">
                <TrendingUp className="h-4 w-4" />
              </div>
            </div>
            <p className="text-sm leading-relaxed text-sapphire-100/90 font-light tracking-wide">
              {insight}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

