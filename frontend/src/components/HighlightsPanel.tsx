import React from 'react';
import { Sparkles } from 'lucide-react';
import type { HighlightItem } from '@/lib/api';
import { SurfaceCard } from '@/components/SurfaceCard';
import { SkeletonBlock } from '@/components/SkeletonBlock';

interface HighlightsPanelProps {
  highlights?: HighlightItem[];
  isLoading?: boolean;
}

export function HighlightsPanel({ highlights, isLoading }: HighlightsPanelProps) {
  return (
    <SurfaceCard className="h-full space-y-4">
      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((item) => (
            <SkeletonBlock key={item} className="h-20" />
          ))}
        </div>
      ) : !highlights || highlights.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-200 bg-brand-soft px-4 py-6 text-center text-sm text-brand-slate">
          No notable insights for the selected range.
        </div>
      ) : (
        <ul className="space-y-3">
          {highlights.map((highlight, index) => (
            <li
              key={`${highlight.title}-${index}`}
              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm"
            >
              <div className="flex items-center gap-2 text-brand-primary">
                <Sparkles className="h-4 w-4" />
                <p className="text-xs font-semibold uppercase tracking-wide">
                  {highlight.title}
                </p>
              </div>
              <p className="mt-1 text-sm leading-relaxed text-brand-midnight">
                {highlight.body}
              </p>
            </li>
          ))}
        </ul>
      )}
    </SurfaceCard>
  );
}

