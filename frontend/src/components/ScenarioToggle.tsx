/**
 * ScenarioToggle
 * Allows switching between base / optimistic / stress forecast scenarios.
 */

import React from 'react';
import { ForecastScenario, SCENARIO_OPTIONS } from '@/lib/insights';
import { cn } from '@/lib/utils';

interface ScenarioToggleProps {
  value: ForecastScenario;
  onChange: (value: ForecastScenario) => void;
}

export function ScenarioToggle({ value, onChange }: ScenarioToggleProps) {
  return (
    <div className="flex flex-wrap items-center gap-1 rounded-full border border-slate-200 bg-white/70 px-1 py-1 text-xs font-semibold text-brand-slate shadow-sm">
      {SCENARIO_OPTIONS.map((option) => (
        <button
          key={option.value}
          type="button"
          onClick={() => onChange(option.value)}
          className={cn(
            'rounded-full px-3 py-1 capitalize transition',
            value === option.value
              ? 'bg-brand-primary text-white shadow-sm'
              : 'text-brand-slate hover:text-brand-midnight',
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}


