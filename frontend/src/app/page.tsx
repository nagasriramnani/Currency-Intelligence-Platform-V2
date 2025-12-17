'use client';

/**
 * Main Dashboard Page
 * Currency Intelligence Platform for Sapphire Capital Partners
 */

import React, { useMemo, useState, useEffect } from 'react';
import { Header } from '@/components/Header';
import { KPICard } from '@/components/KPICard';
import { MultiCurrencyTrendChart } from '@/components/MultiCurrencyTrendChart';
import { YoYComparisonChart } from '@/components/YoYComparisonChart';
import { VolatilityChart } from '@/components/VolatilityChart';
import { ForecastChart } from '@/components/ForecastChart';
import { ReturnDistributionChart } from '@/components/ReturnDistributionChart';
import { InsightsPanel } from '@/components/InsightsPanel';
import { HighlightsPanel } from '@/components/HighlightsPanel';
import { IntelligentAlertsPanel } from '@/components/IntelligentAlertsPanel';
import { ScenarioToggle } from '@/components/ScenarioToggle';
import { ForecastExplanation } from '@/components/ForecastExplanation';
import { ForecastScenario, generateForecastBullets, buildBoardSummary } from '@/lib/insights';
import type { TimeSeriesDataPoint } from '@/lib/api';
import { Info, Download, ClipboardCopy, Check, TrendingUp, Activity, BarChart3 } from 'lucide-react';
import { SectionHeader } from '@/components/SectionHeader';
import { SurfaceCard } from '@/components/SurfaceCard';
import { SkeletonBlock } from '@/components/SkeletonBlock';
import { CampingLoader } from '@/components/CampingLoader';
import {
  useLatestRates,
  useTimeSeriesData,
  useYoYComparison,
  useForecast,
  useInsights,
  useAlertHistory,
  useTestAlert,
  useRefreshData,
  useHighlights,
  useSlackSummary,
} from '@/hooks/useCurrencyData';
import { DateRangePreset, DateRangeState } from '@/types/dateRange';
import { DateRangeSelector } from '@/components/DateRangeSelector';
import { cn } from '@/lib/utils';

const formatISODate = (date: Date) => date.toISOString().split('T')[0];
const MAX_AVAILABLE_DATE = formatISODate(new Date());
const MIN_AVAILABLE_DATE = '2001-01-01';

const subtractYears = (anchor: string, years: number) => {
  const base = new Date(anchor);
  base.setFullYear(base.getFullYear() - years);
  return formatISODate(base);
};

const PRESET_YEAR_LOOKUP: Record<DateRangePreset, number | null> = {
  '1Y': 1,
  '3Y': 3,
  '5Y': 5,
  'MAX': null,
  'CUSTOM': null,
};

function DashboardContent() {
  const [showMovingAverage, setShowMovingAverage] = useState(true);
  const [selectedCurrency, setSelectedCurrency] = useState<'EUR' | 'GBP' | 'CAD'>('EUR');
  const [presentationMode, setPresentationMode] = useState(false);
  const [activeTab, setActiveTab] = useState<'forecast' | 'risk'>('forecast');
  const [scenario, setScenario] = useState<ForecastScenario>('base');
  const [copyStatus, setCopyStatus] = useState<'idle' | 'copied' | 'error'>('idle');
  const [dateRange, setDateRange] = useState<DateRangeState>({
    preset: '3Y',
    startDate: subtractYears(MAX_AVAILABLE_DATE, 3),
    endDate: MAX_AVAILABLE_DATE,
  });

  // Artificial delay to showcase the loading animation (5 seconds on initial load)
  const [showDelayLoader, setShowDelayLoader] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowDelayLoader(false);
    }, 5000); // 5 second delay

    return () => clearTimeout(timer);
  }, []);

  const startFilter = dateRange.startDate ?? undefined;
  const endFilter = dateRange.endDate ?? undefined;

  // Fetch data
  const { data: latestRates, isLoading: ratesLoading, isError: ratesError } = useLatestRates(startFilter, endFilter);
  const { data: timeSeriesData, isLoading: timeSeriesLoading, isError: timeSeriesError } = useTimeSeriesData(
    undefined,
    startFilter,
    endFilter,
  );
  const { data: yoyData, isLoading: yoyLoading } = useYoYComparison(startFilter, endFilter);
  const { data: forecastData, isLoading: forecastLoading } = useForecast(
    selectedCurrency,
    6,
    startFilter,
    endFilter,
  );
  const { data: highlightsData, isLoading: highlightsLoading } = useHighlights(
    startFilter,
    endFilter,
  );
  const { data: insightsData, isLoading: insightsLoading } = useInsights(selectedCurrency);
  const { data: alertHistory, isLoading: alertsLoading } = useAlertHistory(10);

  const testAlertMutation = useTestAlert();
  const refreshDataMutation = useRefreshData();
  const slackSummaryMutation = useSlackSummary();

  const handleSelectPreset = (preset: DateRangePreset) => {
    if (preset === 'MAX') {
      setDateRange({
        preset,
        startDate: null,
        endDate: MAX_AVAILABLE_DATE,
      });
      return;
    }
    const years = PRESET_YEAR_LOOKUP[preset] ?? 3;
    const anchor = dateRange.endDate ?? MAX_AVAILABLE_DATE;
    setDateRange({
      preset,
      startDate: subtractYears(anchor, years),
      endDate: anchor,
    });
  };

  const handleCustomRangeChange = (range: { startDate?: string | null; endDate?: string | null }) => {
    setDateRange((previous) => {
      let start = range.startDate !== undefined ? (range.startDate || null) : previous.startDate;
      let end =
        range.endDate !== undefined
          ? (range.endDate || MAX_AVAILABLE_DATE)
          : previous.endDate ?? MAX_AVAILABLE_DATE;

      if (start && end && start > end) {
        if (range.startDate !== undefined) {
          end = start;
        } else if (range.endDate !== undefined) {
          start = end;
        }
      }

      return {
        preset: 'CUSTOM',
        startDate: start,
        endDate: end,
      };
    });
  };

  const handleResetRange = () => {
    setDateRange({
      preset: 'MAX',
      startDate: null,
      endDate: MAX_AVAILABLE_DATE,
    });
  };

  const handleRefresh = () => {
    refreshDataMutation.mutate(undefined);
  };

  const handleTestAlert = () => {
    testAlertMutation.mutate();
  };

  const handleSendSlackSummary = () => {
    slackSummaryMutation.mutate({
      start_date: dateRange.startDate ?? null,
      end_date: dateRange.endDate ?? null,
    });
  };

  const timeSeriesPoints = timeSeriesData?.data ?? [];

  const scenarioBullets = useMemo(
    () =>
      generateForecastBullets({
        currency: selectedCurrency,
        scenario,
        forecastData,
        timeSeries: timeSeriesPoints,
      }),
    [selectedCurrency, scenario, forecastData, timeSeriesPoints],
  );

  const volatilityBullet = useMemo(
    () => scenarioBullets.find((bullet) => bullet.toLowerCase().includes('volatility')),
    [scenarioBullets],
  );

  const fmpAvailable = useMemo(() => {
    if (!latestRates || !latestRates.length) {
      return false;
    }
    const flagged = latestRates.find((rate) => typeof rate.fmp_available === 'boolean');
    return flagged ? Boolean(flagged.fmp_available) : false;
  }, [latestRates]);

  const boardSummary = useMemo<string | null>(() => {
    if (!latestRates || !latestRates.length) {
      return null;
    }

    return buildBoardSummary({
      latestRates,
      scenario,
      forecastInsight: forecastData?.insight ?? scenarioBullets[0],
      volatilityBullet,
    });
  }, [latestRates, scenario, forecastData?.insight, scenarioBullets, volatilityBullet]);

  // Loading state
  // In React Query v5 with enabled: false (SSR), isLoading is false but data is undefined.
  // We check for missing data without error to show loading state during hydration.
  const isInitialLoading =
    showDelayLoader ||
    ratesLoading ||
    timeSeriesLoading ||
    (!latestRates && !ratesError) ||
    (!timeSeriesData && !timeSeriesError);

  if (isInitialLoading) {
    return <CampingLoader />;
  }

  const handleDownloadCsv = () => {
    if (!timeSeriesPoints.length) return;
    const csv = buildCsvFromTimeSeries(timeSeriesPoints);
    const fileName = `currency_trends_${startFilter ?? 'start'}_${endFilter ?? 'latest'}.csv`;
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', fileName);
    document.body.appendChild(link);
    link.click();
    link.parentNode?.removeChild(link);
    setTimeout(() => URL.revokeObjectURL(url), 500);
  };

  const handleCopySummary = async () => {
    if (!boardSummary) {
      setCopyStatus('error');
      setTimeout(() => setCopyStatus('idle'), 3000);
      return;
    }

    try {
      await navigator.clipboard.writeText(boardSummary);
      setCopyStatus('copied');
      setTimeout(() => setCopyStatus('idle'), 3000);
    } catch (error) {
      setCopyStatus('error');
      setTimeout(() => setCopyStatus('idle'), 3000);
    }
  };

  if (!latestRates || !timeSeriesData) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-sapphire-950 px-4">
        <div className="max-w-md rounded-2xl bg-sapphire-900 border border-sapphire-800 p-8 text-center shadow-2xl">
          <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-danger/10 text-danger border border-danger/20">
            <Activity className="h-8 w-8" />
          </div>
          <h2 className="mb-3 text-2xl font-bold text-white">Connection Failed</h2>
          <p className="text-sapphire-300 mb-6">
            Unable to establish connection with the analytics engine. Please ensure the backend service is running.
          </p>
          <button onClick={handleRefresh} className="btn-primary w-full">
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  const currencies = ['EUR', 'GBP', 'CAD'] as const;

  return (
    <div className="min-h-screen bg-sapphire-950 text-sapphire-100 selection:bg-sapphire-500/30">
      {/* Background Ambience */}
      <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-sapphire-600/10 rounded-full blur-[120px] animate-pulse-slow"></div>
        <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-sapphire-500/5 rounded-full blur-[100px] animate-float"></div>
      </div>

      <div className="relative z-10">
        <Header
          lastUpdate={latestRates[0]?.latest_date ?? null}
          onRefresh={handleRefresh}
          isRefreshing={refreshDataMutation.isPending}
          presentationMode={presentationMode}
          setPresentationMode={setPresentationMode}
        />

        <main
          className={cn(
            'mx-auto max-w-[1600px] px-4 sm:px-6 lg:px-8 transition-all duration-500',
            presentationMode ? 'py-12 space-y-12' : 'py-8 space-y-8',
          )}
        >
          {/* KPI Section */}
          <section className="space-y-6 animate-slide-up">
            <div className="flex flex-col xl:flex-row xl:items-end justify-between gap-6">
              <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
                <Activity className="h-6 w-6 text-sapphire-400" />
                Market Pulse
              </h2>

              <DateRangeSelector
                value={dateRange}
                onSelectPreset={handleSelectPreset}
                onCustomChange={handleCustomRangeChange}
                onReset={handleResetRange}
                minDate={MIN_AVAILABLE_DATE}
                maxDate={MAX_AVAILABLE_DATE}
              />
            </div>

            <div className="grid grid-cols-1 gap-6 md:grid-cols-3 animate-stagger-fade">
              {latestRates?.map((rate) => (
                <KPICard
                  key={rate.currency}
                  title={rate.pair}
                  value={rate.latest_rate}
                  change={rate.yoy_change}
                  changeLabel="YoY"
                  direction={rate.direction}
                  currency={rate.currency}
                  periodStartRate={rate.period_start_rate}
                />
              ))}
            </div>
          </section>

          {/* Main Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-slide-up-delay">
            {/* Trend Chart - Spans 2 cols */}
            <section className="lg:col-span-2 space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-sapphire-400" />
                  Historical Trends
                </h2>

                <div className="flex items-center gap-3">
                  <label className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-sapphire-900/50 border border-sapphire-700/50 cursor-pointer hover:bg-sapphire-800/50 transition-colors">
                    <input
                      type="checkbox"
                      checked={showMovingAverage}
                      onChange={(event) => setShowMovingAverage(event.target.checked)}
                      className="rounded border-sapphire-600 bg-sapphire-800 text-sapphire-500 focus:ring-sapphire-500 focus:ring-offset-sapphire-900"
                    />
                    <span className="text-xs font-medium text-sapphire-300">Moving Avg</span>
                  </label>

                  <button
                    onClick={handleDownloadCsv}
                    className="p-1.5 text-sapphire-400 hover:text-white hover:bg-sapphire-800/50 rounded-lg transition-colors"
                    title="Download CSV"
                  >
                    <Download className="h-4 w-4" />
                  </button>
                </div>
              </div>

              <div className="glass-panel rounded-2xl p-1 h-[400px]">
                <MultiCurrencyTrendChart
                  data={timeSeriesData?.data || []}
                  showMovingAverage={showMovingAverage}
                />
              </div>
            </section>

            {/* Volatility Chart - Spans 1 col */}
            <section className="space-y-6">
              <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-sapphire-400" />
                Volatility Risk
              </h2>
              <div className="glass-panel rounded-2xl p-1 min-h-[400px]">
                <VolatilityChart data={timeSeriesData?.data || []} />
              </div>
            </section>
          </div>

          {/* Forecast & Analysis Section */}
          <section className="space-y-6 animate-slide-up-delay">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <h2 className="text-xl font-bold text-white tracking-tight">
                Forecast & Intelligence
              </h2>

              <div className="flex flex-wrap items-center gap-3 bg-sapphire-900/50 p-1.5 rounded-xl border border-sapphire-800/50 backdrop-blur-sm">
                {currencies.map((currency) => (
                  <button
                    key={currency}
                    onClick={() => setSelectedCurrency(currency)}
                    className={cn(
                      'px-4 py-1.5 rounded-lg text-sm font-semibold transition-all duration-200',
                      selectedCurrency === currency
                        ? 'bg-sapphire-500 text-white shadow-lg shadow-sapphire-500/20'
                        : 'text-sapphire-400 hover:text-white hover:bg-sapphire-800'
                    )}
                  >
                    {currency}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Forecast Chart */}
              <div className="lg:col-span-2 glass-panel rounded-2xl p-6 min-h-[500px]">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex gap-2 bg-sapphire-900/50 p-1 rounded-lg">
                    {(['forecast', 'risk'] as const).map((tab) => (
                      <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        className={cn(
                          'px-4 py-1.5 rounded-md text-xs font-medium transition-all',
                          activeTab === tab
                            ? 'bg-sapphire-700 text-white shadow-sm'
                            : 'text-sapphire-400 hover:text-white'
                        )}
                      >
                        {tab === 'forecast' ? 'Projection' : 'Risk Distribution'}
                      </button>
                    ))}
                  </div>

                  {activeTab === 'forecast' && (
                    <ScenarioToggle value={scenario} onChange={setScenario} />
                  )}
                </div>

                {activeTab === 'forecast' ? (
                  forecastLoading ? (
                    <SkeletonBlock className="h-[400px] bg-sapphire-800/50" />
                  ) : forecastData ? (
                    <ForecastChart
                      forecastData={forecastData}
                      currency={selectedCurrency}
                      scenario={scenario}
                    />
                  ) : (
                    <div className="h-[400px] flex items-center justify-center text-sapphire-400">
                      No forecast data available
                    </div>
                  )
                ) : (
                  <ReturnDistributionChart data={timeSeriesData?.data || []} />
                )}

                <div className="mt-6 pt-6 border-t border-sapphire-700/30">
                  <ForecastExplanation
                    currency={selectedCurrency}
                    scenario={scenario}
                    forecastData={forecastData}
                    timeSeries={timeSeriesPoints}
                    bullets={scenarioBullets}
                  />
                </div>
              </div>

              {/* Intelligence Panel */}
              <div className="lg:col-span-1 h-full">
                <InsightsPanel
                  currency={selectedCurrency}
                  insights={insightsData?.insights || []}
                  isLoading={insightsLoading}
                />
              </div>
            </div>
          </section>

          {/* Bottom Section: Alerts & YoY */}
          {!presentationMode && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 animate-slide-up-delay">
              <section className="space-y-6">
                <h2 className="text-xl font-bold text-white tracking-tight">
                  Year-on-Year Comparison
                </h2>
                <div className="glass-panel rounded-2xl p-1 min-h-[350px]">
                  {yoyLoading ? (
                    <SkeletonBlock className="h-full bg-sapphire-800/50" />
                  ) : yoyData?.data ? (
                    <YoYComparisonChart data={yoyData.data} />
                  ) : (
                    <div className="h-full flex items-center justify-center text-sapphire-400">
                      No YoY data available
                    </div>
                  )}
                </div>
              </section>

              <section className="space-y-6">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-bold text-white tracking-tight">
                    System Alerts
                  </h2>
                  <button
                    onClick={handleCopySummary}
                    className="flex items-center gap-2 text-xs font-medium text-sapphire-400 hover:text-white transition-colors"
                  >
                    {copyStatus === 'copied' ? <Check className="h-3 w-3" /> : <ClipboardCopy className="h-3 w-3" />}
                    {copyStatus === 'copied' ? 'Copied' : 'Copy Summary'}
                  </button>
                </div>

                <IntelligentAlertsPanel
                  onSendSummary={handleSendSlackSummary}
                  sendSummaryLoading={slackSummaryMutation.isPending}
                  summaryStatus={
                    slackSummaryMutation.isSuccess
                      ? 'success'
                      : slackSummaryMutation.isError
                        ? 'error'
                        : undefined
                  }
                />
              </section>
            </div>
          )}

          {!presentationMode && (
            <footer className="border-t border-sapphire-800/50 py-8 text-center">
              <p className="text-sm text-sapphire-400 font-medium">Currency Intelligence Platform © 2024 Sapphire Capital Partners</p>
              <p className="mt-2 flex items-center justify-center gap-2 text-xs text-sapphire-500">
                <Info className="h-3 w-3" />
                {fmpAvailable
                  ? 'Data Source: U.S. Treasury Fiscal Data API & FMP Real-time Quotes'
                  : 'Data Source: U.S. Treasury Fiscal Data API (Official)'}
              </p>
              <p className="mt-1 text-xs text-sapphire-600 font-mono">
                System Version 2.0.0 • Last Sync: {new Date().toLocaleTimeString()}
              </p>
            </footer>
          )}
        </main>
      </div>
    </div>
  );
}

export default function Home() {
  return <DashboardContent />;
}

function buildCsvFromTimeSeries(points: TimeSeriesDataPoint[], window = 3) {
  const currencies: Array<'EUR' | 'GBP' | 'CAD'> = ['EUR', 'GBP', 'CAD'];
  const dateMap = new Map<string, Record<string, number>>();

  points.forEach((point) => {
    if (!currencies.includes(point.currency as any)) return;
    const existing = dateMap.get(point.record_date) ?? {};
    existing[`USD_${point.currency}`] = point.exchange_rate;
    dateMap.set(point.record_date, existing);
  });

  const sortedDates = Array.from(dateMap.keys()).sort((a, b) => new Date(a).getTime() - new Date(b).getTime());

  const movingAverages: Record<string, Record<string, number>> = {};
  currencies.forEach((currency) => {
    const series = points
      .filter((point) => point.currency === currency)
      .sort((a, b) => new Date(a.record_date).getTime() - new Date(b.record_date).getTime())
      .map((point) => ({ date: point.record_date, value: point.exchange_rate }));

    const maMap: Record<string, number> = {};
    for (let i = 0; i < series.length; i += 1) {
      if (i + 1 >= window) {
        const slice = series.slice(i - window + 1, i + 1);
        const avg = slice.reduce((sum, entry) => sum + entry.value, 0) / slice.length;
        maMap[series[i].date] = avg;
      }
    }
    movingAverages[currency] = maMap;
  });

  const headers = [
    'date',
    ...currencies.map((currency) => `USD_${currency}`),
    ...currencies.map((currency) => `USD_${currency}_MA`),
  ];

  const rows = sortedDates.map((date) => {
    const base = dateMap.get(date) ?? {};
    const values = currencies.map((currency) => {
      const key = `USD_${currency}`;
      const raw = base[key];
      return typeof raw === 'number' ? raw.toFixed(4) : '';
    });

    const maValues = currencies.map((currency) => {
      const ma = movingAverages[currency]?.[date];
      return typeof ma === 'number' ? ma.toFixed(4) : '';
    });

    return [date, ...values, ...maValues].join(',');
  });

  return [headers.join(','), ...rows].join('\n');
}


