'use client';

import React, { Suspense, useState, useEffect } from 'react';
import { SectionHeader } from '@/components/SectionHeader';
import { Activity, BarChart2, GitCommit, Zap } from 'lucide-react';
import { CorrelationMatrix } from '@/components/CorrelationMatrix';
import { SeasonalityChart } from '@/components/SeasonalityChart';
import { SkeletonBlock } from '@/components/SkeletonBlock';
import { ScenarioBuilder } from '@/components/ScenarioBuilder';
import { NavBar } from '@/components/NavBar';
import { CampingLoader } from '@/components/CampingLoader';

export const dynamic = 'force-dynamic';

export default function AnalysisPage() {
    // Loading delay for page transition animation
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const timer = setTimeout(() => setIsLoading(false), 3500);
        return () => clearTimeout(timer);
    }, []);

    if (isLoading) {
        return <CampingLoader />;
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-sapphire-950 via-sapphire-900 to-sapphire-950">
            <NavBar />
            <main className="mx-auto max-w-[1600px] px-4 py-8 sm:px-6 lg:px-8 space-y-8">

                {/* Page Header with fade-in animation */}
                <div className="flex flex-col gap-2 animate-fade-in-up">
                    <h1 className="text-3xl font-bold tracking-tight text-white">
                        Market <span className="text-sapphire-400">Analysis</span>
                    </h1>
                    <p className="text-sapphire-200">
                        Deep dive into currency correlations, seasonality, and risk scenarios.
                    </p>
                </div>

                {/* Main grid with staggered fade */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-stagger-fade">
                    {/* Correlation Matrix */}
                    <section className="glass-panel p-6 rounded-2xl space-y-4 group hover:-translate-y-1 hover:shadow-xl hover:shadow-sapphire-500/10 transition-all duration-500 relative overflow-hidden">
                        <SectionHeader
                            title="Correlation Matrix"
                            icon={GitCommit}
                            description="Cross-currency correlation heatmap (90-day rolling)"
                        />
                        <Suspense fallback={<SkeletonBlock className="h-[300px] w-full" />}>
                            <CorrelationMatrix />
                        </Suspense>
                        {/* Shimmer effect */}
                        <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/[0.03] to-transparent pointer-events-none"></div>
                    </section>

                    {/* Seasonality Analysis */}
                    <section className="glass-panel p-6 rounded-2xl space-y-4 group hover:-translate-y-1 hover:shadow-xl hover:shadow-sapphire-500/10 transition-all duration-500 relative overflow-hidden">
                        <SectionHeader
                            title="Seasonality Analysis"
                            icon={BarChart2}
                            description="Average monthly performance trends (5-year history)"
                        />
                        <Suspense fallback={<SkeletonBlock className="h-[300px] w-full" />}>
                            <SeasonalityChart />
                        </Suspense>
                        {/* Shimmer effect */}
                        <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/[0.03] to-transparent pointer-events-none"></div>
                    </section>
                </div>

                {/* Scenario Builder with delayed animation */}
                <section
                    className="glass-panel p-6 rounded-2xl space-y-4 group hover:-translate-y-1 hover:shadow-xl hover:shadow-sapphire-500/10 transition-all duration-500 relative overflow-hidden animate-fade-in-up"
                    style={{ animationDelay: '0.4s' }}
                >
                    <SectionHeader
                        title="Scenario Builder"
                        icon={Zap}
                        description="Simulate market shocks and portfolio impact"
                    />
                    <Suspense fallback={<SkeletonBlock className="h-[200px] w-full" />}>
                        <ScenarioBuilder />
                    </Suspense>
                    {/* Shimmer effect */}
                    <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/[0.03] to-transparent pointer-events-none"></div>
                </section>
            </main>
        </div>
    );
}
