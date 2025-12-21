'use client';

import React, { Suspense, useState, useEffect } from 'react';
import { SectionHeader } from '@/components/SectionHeader';
import { Activity, BarChart2, GitCommit, Zap, FileText, Download, Loader2 } from 'lucide-react';
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
    const [isGenerating, setIsGenerating] = useState(false);
    const [showReportMenu, setShowReportMenu] = useState(false);

    useEffect(() => {
        const timer = setTimeout(() => setIsLoading(false), 3500);
        return () => clearTimeout(timer);
    }, []);

    const handleGenerateReport = async (reportType: 'executive-summary' | 'risk-report') => {
        setIsGenerating(true);
        setShowReportMenu(false);

        try {
            const response = await fetch(`http://localhost:8000/api/reports/${reportType}`);

            if (!response.ok) {
                throw new Error('Failed to generate report');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${reportType}_${new Date().toISOString().split('T')[0]}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            console.error('Error generating report:', error);
            alert('Failed to generate report. Please ensure the backend is running.');
        } finally {
            setIsGenerating(false);
        }
    };

    if (isLoading) {
        return <CampingLoader />;
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-sapphire-950 via-sapphire-900 to-sapphire-950">
            <NavBar />
            <main className="mx-auto max-w-[1600px] px-4 py-8 sm:px-6 lg:px-8 space-y-8">

                {/* Page Header with fade-in animation */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 animate-fade-in-up">
                    <div className="flex flex-col gap-2">
                        <h1 className="text-3xl font-bold tracking-tight text-white">
                            Market <span className="text-sapphire-400">Analysis</span>
                        </h1>
                        <p className="text-sapphire-200">
                            Deep dive into currency correlations, seasonality, and risk scenarios.
                        </p>
                    </div>

                    {/* Generate Report Button */}
                    <button
                        onClick={() => setShowReportMenu(true)}
                        disabled={isGenerating}
                        className="flex items-center gap-2 px-4 py-2.5 rounded-xl accent-bg text-white font-medium
                                   hover:opacity-90 transition-all duration-200 accent-glow-sm disabled:opacity-50"
                    >
                        {isGenerating ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                            <FileText className="h-4 w-4" />
                        )}
                        <span>{isGenerating ? 'Generating...' : 'Generate Report'}</span>
                    </button>
                </div>

                {/* Report Selection Modal */}
                {showReportMenu && (
                    <div
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100] flex items-center justify-center animate-fade-in"
                        onClick={() => setShowReportMenu(false)}
                    >
                        <div
                            className="bg-sapphire-900/95 border border-sapphire-700/50 rounded-2xl p-6 w-full max-w-md mx-4 shadow-2xl animate-fade-in-up"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <div className="flex items-center justify-between mb-6">
                                <h3 className="text-xl font-semibold text-white">Generate Report</h3>
                                <button
                                    onClick={() => setShowReportMenu(false)}
                                    className="text-sapphire-400 hover:text-white transition-colors"
                                >
                                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                </button>
                            </div>

                            <p className="text-sapphire-300 text-sm mb-6">
                                Select a report type to download as PDF
                            </p>

                            <div className="space-y-3">
                                <button
                                    onClick={() => handleGenerateReport('executive-summary')}
                                    className="w-full flex items-center gap-4 p-4 rounded-xl bg-sapphire-800/50 border border-sapphire-700/50
                                               hover:bg-sapphire-700/50 hover:border-sapphire-600/50 transition-all group"
                                >
                                    <div className="p-3 rounded-lg accent-bg-subtle">
                                        <FileText className="h-5 w-5 accent-text-light" />
                                    </div>
                                    <div className="text-left flex-1">
                                        <p className="font-medium text-white group-hover:accent-text-light transition-colors">
                                            Executive Summary
                                        </p>
                                        <p className="text-xs text-sapphire-400">
                                            KPIs, market regime & hedging recommendations
                                        </p>
                                    </div>
                                    <Download className="h-4 w-4 text-sapphire-500 group-hover:accent-text-light transition-colors" />
                                </button>

                                <button
                                    onClick={() => handleGenerateReport('risk-report')}
                                    className="w-full flex items-center gap-4 p-4 rounded-xl bg-sapphire-800/50 border border-sapphire-700/50
                                               hover:bg-sapphire-700/50 hover:border-sapphire-600/50 transition-all group"
                                >
                                    <div className="p-3 rounded-lg bg-orange-500/20">
                                        <Activity className="h-5 w-5 text-orange-400" />
                                    </div>
                                    <div className="text-left flex-1">
                                        <p className="font-medium text-white group-hover:text-orange-300 transition-colors">
                                            Risk Report
                                        </p>
                                        <p className="text-xs text-sapphire-400">
                                            VaR analysis, stress tests & hedging actions
                                        </p>
                                    </div>
                                    <Download className="h-4 w-4 text-sapphire-500 group-hover:text-orange-400 transition-colors" />
                                </button>
                            </div>

                            <p className="text-xs text-sapphire-500 mt-6 text-center">
                                Reports are generated using the latest data
                            </p>
                        </div>
                    </div>
                )}

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
