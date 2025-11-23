/**
 * ForecastExplanation
 * Provides context bullets describing why the forecast looks the way it does.
 */

import React, { useMemo } from 'react';
import { Lightbulb } from 'lucide-react';
import { SurfaceCard } from '@/components/SurfaceCard';
import { ForecastScenario, generateForecastBullets } from '@/lib/insights';
import type { ForecastData, TimeSeriesDataPoint } from '@/lib/api';

interface ForecastExplanationProps {
  currency: string;
  scenario: ForecastScenario;
  forecastData?: ForecastData;
  timeSeries?: TimeSeriesDataPoint[];
  bullets?: string[];
}

export function ForecastExplanation({
  currency,
  scenario,
  forecastData,
  timeSeries,
  bullets,
}: ForecastExplanationProps) {
  const derivedBullets = useMemo(
    () =>
      bullets ??
      generateForecastBullets({
        currency,
        scenario,
        forecastData,
        timeSeries,
      }),
    [bullets, currency, scenario, forecastData, timeSeries],
  );

  if (!derivedBullets.length) {
    return null;
  }

  return (
    <SurfaceCard className="space-y-4">
      <div className="flex items-center gap-2">
        <Lightbulb className="h-5 w-5 text-brand-primary" />
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-brand-slate">
            Why this forecast?
          </p>
          <h3 className="text-lg font-semibold text-brand-navy">
            Signals driving the USD/{currency} outlook
          </h3>
        </div>
      </div>
      <ul className="space-y-2 text-sm text-brand-midnight">
        {derivedBullets.map((bullet, index) => (
          <li key={`${bullet}-${index}`} className="leading-relaxed">
            • {bullet}
          </li>
        ))}
      </ul>
    </SurfaceCard>
  );
}


