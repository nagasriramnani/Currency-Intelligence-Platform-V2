import React from 'react';
import { DateRangePreset, DateRangeState } from '@/types/dateRange';
import { Calendar, RotateCcw } from 'lucide-react';

interface DateRangeSelectorProps {
  value: DateRangeState;
  onSelectPreset: (preset: DateRangePreset) => void;
  onCustomChange: (range: { startDate?: string | null; endDate?: string | null }) => void;
  onReset?: () => void;
  minDate?: string;
  maxDate?: string;
}

const PRESETS: { label: string; value: DateRangePreset }[] = [
  { label: '1Y', value: '1Y' },
  { label: '3Y', value: '3Y' },
  { label: '5Y', value: '5Y' },
  { label: 'Max', value: 'MAX' },
];

export function DateRangeSelector({
  value,
  onSelectPreset,
  onCustomChange,
  onReset,
  minDate,
  maxDate,
}: DateRangeSelectorProps) {
  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 bg-sapphire-900/40 p-2 rounded-xl border border-sapphire-800/50 backdrop-blur-sm">
      <div className="flex items-center gap-2">
        <span className="text-[10px] uppercase tracking-wider text-sapphire-400 font-semibold px-2">
          Range
        </span>
        <div className="flex bg-sapphire-950/50 rounded-lg p-1 border border-sapphire-800/50">
          {PRESETS.map((preset) => (
            <button
              key={preset.value}
              onClick={() => onSelectPreset(preset.value)}
              type="button"
              className={`rounded-md px-3 py-1 text-xs font-medium transition-all duration-200 ${value.preset === preset.value
                  ? 'bg-sapphire-500 text-white shadow-sm'
                  : 'text-sapphire-400 hover:text-white hover:bg-sapphire-800'
                }`}
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      <div className="h-8 w-px bg-sapphire-800/50 hidden sm:block"></div>

      <div className="flex flex-wrap items-center gap-3 text-xs">
        <label className="flex items-center gap-2 text-sapphire-300">
          <span>From</span>
          <div className="relative">
            <input
              type="date"
              value={value.startDate ?? ''}
              min={minDate}
              max={value.endDate ?? maxDate}
              onChange={(event) =>
                onCustomChange({ startDate: event.target.value || null })
              }
              className="pl-8 pr-2 py-1.5 rounded-lg border border-sapphire-700 bg-sapphire-950/50 text-sapphire-100 focus:border-sapphire-500 focus:outline-none focus:ring-1 focus:ring-sapphire-500/50 w-32 transition-colors"
            />
            <Calendar className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-sapphire-500 pointer-events-none" />
          </div>
        </label>

        <label className="flex items-center gap-2 text-sapphire-300">
          <span>To</span>
          <div className="relative">
            <input
              type="date"
              value={value.endDate ?? ''}
              min={value.startDate ?? minDate}
              max={maxDate}
              onChange={(event) =>
                onCustomChange({ endDate: event.target.value || null })
              }
              className="pl-8 pr-2 py-1.5 rounded-lg border border-sapphire-700 bg-sapphire-950/50 text-sapphire-100 focus:border-sapphire-500 focus:outline-none focus:ring-1 focus:ring-sapphire-500/50 w-32 transition-colors"
            />
            <Calendar className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-sapphire-500 pointer-events-none" />
          </div>
        </label>

        {value.preset === 'CUSTOM' && (
          <span className="rounded-full bg-sapphire-500/10 border border-sapphire-500/20 px-2 py-0.5 text-[10px] uppercase tracking-wide text-sapphire-300">
            Custom
          </span>
        )}

        {onReset && (
          <button
            type="button"
            onClick={onReset}
            className="ml-auto flex items-center gap-1.5 rounded-lg border border-sapphire-700/50 px-3 py-1.5 text-sapphire-400 transition hover:bg-sapphire-800 hover:text-white"
          >
            <RotateCcw className="h-3 w-3" />
            Reset
          </button>
        )}
      </div>
    </div>
  );
}
