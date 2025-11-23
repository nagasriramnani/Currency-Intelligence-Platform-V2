import { ForecastData, ForecastPoint, ConfidenceBandPoint, TimeSeriesDataPoint, LatestRate } from '@/lib/api';
import { formatPercentage } from '@/lib/utils';

export type ForecastScenario = 'base' | 'optimistic' | 'stress';

export const SCENARIO_OPTIONS: { label: string; value: ForecastScenario; description: string }[] = [
  { label: 'Base', value: 'base', description: 'Default model output' },
  { label: 'Optimistic', value: 'optimistic', description: 'USD strengthens 5%' },
  { label: 'Stress', value: 'stress', description: 'USD weakens 5%' },
];

const SCENARIO_MULTIPLIERS: Record<ForecastScenario, number> = {
  base: 1,
  optimistic: 1.05,
  stress: 0.95,
};

export function getScenarioMultiplier(scenario: ForecastScenario) {
  return SCENARIO_MULTIPLIERS[scenario];
}

export function describeScenario(scenario: ForecastScenario) {
  switch (scenario) {
    case 'optimistic':
      return 'Optimistic scenario assumes a 5% stronger USD versus the base forecast.';
    case 'stress':
      return 'Stress scenario applies a 5% weaker USD compared with the base forecast.';
    default:
      return 'Base scenario reflects the core model output.';
  }
}

export function adjustForecastForScenario(
  forecastData: ForecastData | undefined,
  scenario: ForecastScenario,
): { forecast: ForecastPoint[]; confidence: ConfidenceBandPoint[]; insight?: string | null } {
  if (!forecastData) {
    return { forecast: [], confidence: [], insight: undefined };
  }

  const multiplier = getScenarioMultiplier(scenario);
  const adjustedForecast = (forecastData.forecast ?? []).map((point) => ({
    ...point,
    value: point.value * multiplier,
  }));

  const adjustedConfidence = (forecastData.confidence ?? []).map((band) => ({
    ...band,
    lower: band.lower * multiplier,
    upper: band.upper * multiplier,
  }));

  return {
    forecast: adjustedForecast,
    confidence: adjustedConfidence,
    insight: forecastData.insight,
  };
}

interface ExplanationParams {
  currency: string;
  scenario: ForecastScenario;
  forecastData?: ForecastData;
  timeSeries?: TimeSeriesDataPoint[];
}

export function generateForecastBullets({
  currency,
  scenario,
  forecastData,
  timeSeries,
}: ExplanationParams): string[] {
  const bullets: string[] = [];
  const currencySeries = (timeSeries ?? [])
    .filter((point) => point.currency === currency)
    .sort((a, b) => new Date(a.record_date).getTime() - new Date(b.record_date).getTime());

  if (currencySeries.length > 3) {
    const lastTwelve = currencySeries.slice(-12);
    const firstValue = lastTwelve[0]?.exchange_rate;
    const lastValue = lastTwelve[lastTwelve.length - 1]?.exchange_rate;
    if (firstValue && lastValue) {
      const changePct = ((lastValue - firstValue) / firstValue) * 100;
      const direction = changePct > 0 ? 'risen' : 'fallen';
      bullets.push(
        `Recent trend: USD/${currency} has ${direction} ${formatPercentage(Math.abs(changePct))} over the last year.`,
      );
    }
  }

  const volValues = currencySeries
    .map((point) => point.rolling_volatility)
    .filter((value): value is number => value !== null && value !== undefined);

  if (volValues.length > 3) {
    const recent = average(volValues.slice(-12));
    const overall = average(volValues);
    if (recent && overall) {
      if (recent > overall * 1.1) {
        bullets.push('Volatility is slightly above its long-run average, implying a wider uncertainty band.');
      } else if (recent < overall * 0.9) {
        bullets.push('Volatility is running below average, so the confidence range is relatively tight.');
      } else {
        bullets.push('Volatility is close to its long-run average, keeping the confidence range steady.');
      }
    }
  }

  if (forecastData?.insight) {
    bullets.push(`Model insight: ${forecastData.insight}`);
  }

  bullets.push(describeScenario(scenario));

  return bullets.slice(0, 4);
}

export function buildBoardSummary({
  latestRates,
  scenario,
  forecastInsight,
  volatilityBullet,
}: {
  latestRates?: LatestRate[];
  scenario: ForecastScenario;
  forecastInsight?: string;
  volatilityBullet?: string;
}): string {
  const yoyParts =
    latestRates?.map((rate) => {
      const pct = rate.yoy_change !== null ? formatPercentage(rate.yoy_change) : 'n/a';
      return `${rate.pair} YoY ${pct}`;
    }) ?? [];

  const scenarioText =
    scenario === 'base'
      ? 'Base scenario selected.'
      : scenario === 'optimistic'
      ? 'Optimistic scenario (+5% tilt) selected.'
      : 'Stress scenario (-5% tilt) selected.';

  const pieces = [
    `YoY snapshot: ${yoyParts.join(', ')}`,
    forecastInsight ? `Forecast: ${forecastInsight}` : '',
    volatilityBullet ? `Volatility: ${volatilityBullet}` : '',
    scenarioText,
  ].filter(Boolean);

  return pieces.join(' | ');
}

function average(values: number[]) {
  if (!values.length) return null;
  const sum = values.reduce((acc, value) => acc + value, 0);
  return sum / values.length;
}


