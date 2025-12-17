/**
 * Forecast vs Actual Chart
 * Visualization #4: Shows ML forecast with confidence intervals
 */

import React, { useMemo } from 'react';
import {
  LineChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts';
import { Sparkles } from 'lucide-react';
import { formatDateShort, getCurrencyColor } from '@/lib/utils';
import type { ForecastData } from '@/lib/api';
import { ForecastScenario, adjustForecastForScenario } from '@/lib/insights';

interface ForecastChartProps {
  forecastData?: ForecastData;
  currency: string;
  scenario: ForecastScenario;
}

export function ForecastChart({ forecastData, currency, scenario }: ForecastChartProps) {
  const adjustedSeries = useMemo(() => adjustForecastForScenario(forecastData, scenario), [forecastData, scenario]);

  const chartData = useMemo(() => {
    if (!forecastData) return [];

    const confidenceMap = new Map(adjustedSeries.confidence.map((band) => [band.date, band]));

    const historical = (forecastData.historical ?? [])
      .map((point) => ({
        date: point.date,
        actual: point.value,
        forecast: null,
        lower: null,
        upper: null,
        type: 'historical' as const,
      }))
      .slice(-36);

    const forecastSeries = adjustedSeries.forecast.map((point) => {
      const band = confidenceMap.get(point.date);
      return {
        date: point.date,
        actual: null,
        forecast: point.value,
        lower: band?.lower ?? null,
        upper: band?.upper ?? null,
        type: 'forecast' as const,
      };
    });

    if (!historical.length) {
      return forecastSeries;
    }

    if (!forecastSeries.length) {
      return historical;
    }

    // Get the last actual point for anchoring
    // Use API's last_actual if available, otherwise use last historical point
    const lastActual = forecastData.last_actual || {
      date: historical[historical.length - 1].date,
      value: historical[historical.length - 1].actual
    };

    // Create bridge point at the last actual date with the last actual value
    // This ensures the forecast line starts from where the actual line ends
    const bridgePoint = {
      date: lastActual.date,
      actual: lastActual.value,  // Connect to actual line
      forecast: lastActual.value, // Start forecast from same point
      lower: forecastSeries[0]?.lower ?? null,
      upper: forecastSeries[0]?.upper ?? null,
      type: 'transition' as const,
    };

    return [...historical, bridgePoint, ...forecastSeries];
  }, [forecastData, adjustedSeries]);

  // Error state: Model not trained
  if (forecastData?.error) {
    return (
      <div className="space-y-4">
        <div className="rounded-lg border border-red-500/50 bg-red-500/10 p-6">
          <div className="flex items-start gap-3">
            <span className="text-2xl">🚫</span>
            <div>
              <h4 className="text-lg font-bold text-red-400">
                Model Not Trained
              </h4>
              <p className="mt-1 text-sm text-red-300">
                {forecastData.error.message}
              </p>
              {forecastData.error.hint && (
                <p className="mt-2 text-xs text-sapphire-400">
                  💡 {forecastData.error.hint}
                </p>
              )}
              {forecastData.error.action && (
                <div className="mt-3 rounded bg-sapphire-900/50 p-3">
                  <p className="text-xs font-mono text-sapphire-300">
                    {forecastData.error.action}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
        <p className="text-sm text-sapphire-400">
          Train a model via the terminal training menu before viewing forecasts.
        </p>
      </div>
    );
  }

  if (!forecastData || chartData.length === 0) {
    return (
      <div className="flex h-96 items-center justify-center text-sapphire-400">
        No data available
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Model Provenance Badge - Full Metadata Display */}
      {forecastData.model && (
        <div className="flex items-center gap-3 flex-wrap">
          {/* Model Type Badge */}
          <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border ${forecastData.model.is_fallback
            ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
            : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
            }`}>
            <span className="uppercase tracking-wider font-bold">
              {forecastData.model.model_type}
            </span>
          </div>

          {/* Model ID */}
          {forecastData.model.model_version && (
            <span className="text-[10px] text-sapphire-400 font-mono">
              {forecastData.model.model_version.substring(0, 30)}
            </span>
          )}

          {/* Training Date */}
          {forecastData.model.trained_at && (
            <span className="text-[10px] text-sapphire-400 border border-sapphire-700 px-2 py-0.5 rounded">
              📅 {new Date(forecastData.model.trained_at).toLocaleDateString()}
            </span>
          )}

          {/* Validation MAPE */}
          {forecastData.model.metrics?.mape !== undefined && (
            <span className="text-[10px] text-sapphire-400 border border-sapphire-700 px-2 py-0.5 rounded">
              MAPE: {forecastData.model.metrics.mape.toFixed(2)}%
            </span>
          )}

          {/* Training Samples */}
          {forecastData.model.metrics?.train_samples !== undefined && (
            <span className="text-[10px] text-sapphire-400 border border-sapphire-700 px-2 py-0.5 rounded">
              🎯 {forecastData.model.metrics.train_samples} samples
            </span>
          )}

          {/* Forecast Strategy */}
          {forecastData.model.metrics?.forecast_strategy && (
            <span className="text-[10px] text-purple-400 border border-purple-500/30 px-2 py-0.5 rounded bg-purple-500/10">
              {forecastData.model.metrics.forecast_strategy}
            </span>
          )}

          {/* Status Badge */}
          {forecastData.model.is_fallback ? (
            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-[10px] font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
              ⚠️ Fallback
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-[10px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              ✓ Trained
            </span>
          )}
        </div>
      )}


      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={chartData} margin={{ top: 10, right: 24, left: 10, bottom: 5 }}>
          {/* Softer gridlines for enterprise look */}
          <CartesianGrid strokeDasharray="4 4" stroke="#1E293B" strokeOpacity={0.6} vertical={false} />
          <XAxis
            dataKey="date"
            tickFormatter={(date) => formatDateShort(date)}
            stroke="#64748B"
            style={{ fontSize: '11px' }}
            tick={{ fill: '#64748B' }}
            axisLine={{ stroke: '#334155' }}
            tickLine={{ stroke: '#334155' }}
          />
          <YAxis
            stroke="#94A3B8"
            style={{ fontSize: '12px' }}
            domain={['auto', 'auto']}
            tick={{ fill: '#94A3B8' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '8px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
              color: '#f8fafc'
            }}
            itemStyle={{ color: '#f8fafc' }}
            labelFormatter={(date) => formatDateShort(date)}
            formatter={(value: any, name: string) => {
              if (value === null || value === undefined) return null;
              const label = name === 'actual' ? 'Actual' : name === 'forecast' ? 'Forecast' : name;
              return [Number(value).toFixed(4), label];
            }}
          />
          <Legend
            verticalAlign="top"
            align="left"
            wrapperStyle={{ paddingBottom: 20 }}
            payload={[
              { value: 'Actual', type: 'line', color: '#2563EB', id: 'actual' },
              { value: 'Forecast', type: 'line', color: '#D97706', id: 'forecast' },
              { value: 'Confidence Band', type: 'rect', color: '#D97706', id: 'band' },
            ]}
          />

          {forecastData.forecast_start && (
            <ReferenceLine
              x={forecastData.forecast_start}
              stroke="#64748B"
              strokeDasharray="3 3"
              label={{
                position: 'top',
                value: 'Forecast starts',
                fill: '#94A3B8',
                fontSize: 11,
              }}
            />
          )}

          {/* Confidence band - soft gradient with fading edges */}
          <Area
            type="monotone"
            dataKey="upper"
            stroke="none"
            fill="url(#confidenceGradient)"
            fillOpacity={0.15}
            name="Upper band"
            isAnimationActive={true}
            animationDuration={1500}
            animationEasing="ease-out"
          />
          <defs>
            <linearGradient id="confidenceGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#D97706" stopOpacity={0.3} />
              <stop offset="100%" stopColor="#D97706" stopOpacity={0.05} />
            </linearGradient>
          </defs>
          <Area
            type="monotone"
            dataKey="lower"
            stroke="none"
            fill="#0A0F1F" // Match background
            fillOpacity={1}
            name="Lower band"
            isAnimationActive={false}
          />

          {/* Actual line - Steel blue */}
          <Line
            type="monotone"
            dataKey="actual"
            name="Actual Rate"
            stroke="#2563EB"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: '#2563EB', stroke: '#0A0F1F', strokeWidth: 2 }}
            connectNulls
            isAnimationActive={true}
            animationDuration={1200}
            animationEasing="ease-out"
          />

          {/* Forecast line - Soft amber */}
          <Line
            type="monotone"
            dataKey="forecast"
            name="Forecast"
            stroke="#D97706"
            strokeWidth={2}
            strokeDasharray="6 4"
            dot={{ r: 2.5, fill: '#D97706', stroke: '#0A0F1F', strokeWidth: 1 }}
            activeDot={{ r: 4, fill: '#D97706', stroke: '#0A0F1F', strokeWidth: 2 }}
            connectNulls
            isAnimationActive={true}
            animationDuration={1500}
            animationEasing="ease-out"
          />
        </LineChart>
      </ResponsiveContainer>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="rounded-xl bg-sapphire-900/50 border border-sapphire-800/50 p-4">
          <h5 className="mb-2 text-xs font-semibold uppercase tracking-wider text-sapphire-400">Forecast Horizon</h5>
          <p className="text-lg font-bold text-white">
            {forecastData.forecast.length || 0} periods
          </p>
          <p className="mt-1 text-xs text-sapphire-300">
            {forecastData.forecast[0]?.date ?? 'n/a'} to{' '}
            {forecastData.forecast[forecastData.forecast.length - 1]?.date ?? 'n/a'}
          </p>
        </div>

        <div className="rounded-xl bg-sapphire-900/50 border border-sapphire-800/50 p-4">
          <h5 className="mb-2 text-xs font-semibold uppercase tracking-wider text-sapphire-400">Direction</h5>
          <p className="text-lg font-bold text-white">
            {(() => {
              const first = adjustedSeries.forecast[0]?.value;
              const last = adjustedSeries.forecast[adjustedSeries.forecast.length - 1]?.value;
              if (first === undefined || last === undefined) return 'Stable →';
              if (last > first * 1.01) return 'Rising ↑';
              if (last < first * 0.99) return 'Declining ↓';
              return 'Stable →';
            })()}
          </p>
          <p className="mt-1 text-xs text-sapphire-300">
            From {adjustedSeries.forecast[0]?.value?.toFixed(4) ?? 'n/a'} to{' '}
            {adjustedSeries.forecast[adjustedSeries.forecast.length - 1]?.value?.toFixed(4) ?? 'n/a'}
          </p>
        </div>

        <div className="rounded-xl bg-sapphire-900/50 border border-sapphire-800/50 p-4">
          <h5 className="mb-2 text-xs font-semibold uppercase tracking-wider text-sapphire-400">Confidence</h5>
          {adjustedSeries.confidence.length > 0 ? (
            <>
              <p className="text-lg font-bold text-white">
                {adjustedSeries.confidence[0].lower.toFixed(4)} -{' '}
                {adjustedSeries.confidence[adjustedSeries.confidence.length - 1].upper.toFixed(4)}
              </p>
              <p className="mt-1 text-xs text-sapphire-300">
                80% interval range
              </p>
            </>
          ) : (
            <p className="text-sm text-sapphire-300">Confidence band not available.</p>
          )}
        </div>
      </div>

      <div className="rounded-lg bg-sapphire-800/30 p-4 border border-sapphire-700/30">
        <p className="text-sm leading-relaxed text-sapphire-200">
          The solid line tracks realised USD/{currency} rates. The yellow dashed line shows the
          scenario-adjusted forward view and the shaded band marks the forecast uncertainty. A steeper
          slope or widening band indicates higher risk ahead.
        </p>
      </div>

      {forecastData.insight && (
        <div className="flex gap-3 rounded-lg border border-sapphire-700/50 bg-sapphire-900/30 p-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-sapphire-500/10 text-sapphire-400 border border-sapphire-500/20">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-sapphire-400">
              AI Forecast Insight
            </p>
            <p className="mt-1 text-sm leading-relaxed text-sapphire-100">
              {forecastData.insight}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

