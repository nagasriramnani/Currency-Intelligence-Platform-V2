import React, { Suspense } from 'react';
import { SectionHeader } from '@/components/SectionHeader';
import { Activity, BarChart2, GitCommit, Zap, ArrowLeft } from 'lucide-react';
import { CorrelationMatrix } from '@/components/CorrelationMatrix';
import { SeasonalityChart } from '@/components/SeasonalityChart';
import { SkeletonBlock } from '@/components/SkeletonBlock';
import { ScenarioBuilder } from '@/components/ScenarioBuilder';
import Link from 'next/link';

export const dynamic = 'force-dynamic';

export default function AnalysisPage() {
    return (
        <Suspense fallback={<SkeletonBlock className="h-screen w-full" />}>
            <main className="mx-auto max-w-[1600px] px-4 py-8 sm:px-6 lg:px-8 space-y-8">
                <Link href="/" className="inline-flex items-center gap-2 text-sapphire-300 hover:text-white transition-colors">
                    <ArrowLeft className="h-4 w-4" />
                    Back to Dashboard
                </Link>

                <div className="flex flex-col gap-2">
                    <h1 className="text-3xl font-bold tracking-tight text-white">
                        Market <span className="text-sapphire-400">Analysis</span>
                    </h1>
                    <p className="text-sapphire-200">
                        Deep dive into currency correlations, seasonality, and risk scenarios.
                    </p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Correlation Matrix */}
                    <section className="glass-panel p-6 rounded-2xl space-y-4">
                        <SectionHeader
                            title="Correlation Matrix"
                            icon={GitCommit}
                            description="Cross-currency correlation heatmap (90-day rolling)"
                        />
                        <CorrelationMatrix />
                    </section>

                    {/* Seasonality Analysis */}
                    <section className="glass-panel p-6 rounded-2xl space-y-4">
                        <SectionHeader
                            title="Seasonality Analysis"
                            icon={BarChart2}
                            description="Average monthly performance trends (5-year history)"
                        />
                        <SeasonalityChart />
                    </section>
                </div>

                {/* Scenario Builder Placeholder */}
                <section className="glass-panel p-6 rounded-2xl space-y-4">
                    <SectionHeader
                        title="Scenario Builder"
                        icon={Zap}
                        description="Simulate market shocks and portfolio impact"
                    />
                    <ScenarioBuilder />
                </section>
            </main>
        </Suspense>
    );
}
