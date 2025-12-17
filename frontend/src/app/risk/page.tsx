'use client';

import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { NavBar } from '@/components/NavBar';
import { SectionHeader } from '@/components/SectionHeader';
import { VaRPanel } from '@/components/VaRPanel';
import { RecommendationsPanel } from '@/components/RecommendationsPanel';
import { StressScenariosTable } from '@/components/StressScenariosTable';
import { Shield, RefreshCw, Settings2 } from 'lucide-react';
import { CampingLoader } from '@/components/CampingLoader';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// API fetchers
async function fetchVaR(confidence: number, horizon: number) {
    const res = await fetch(`${API_BASE}/api/risk/var?confidence=${confidence}&horizon=${horizon}`);
    if (!res.ok) throw new Error('Failed to fetch VaR');
    return res.json();
}

async function fetchStressTests() {
    const res = await fetch(`${API_BASE}/api/risk/stress-test`);
    if (!res.ok) throw new Error('Failed to fetch stress tests');
    return res.json();
}

async function fetchRecommendations() {
    const res = await fetch(`${API_BASE}/api/risk/recommendations`);
    if (!res.ok) throw new Error('Failed to fetch recommendations');
    return res.json();
}

export default function RiskPage() {
    const [confidence, setConfidence] = React.useState(0.95);
    const [horizon, setHorizon] = React.useState(1);

    // Loading delay for page transition animation
    const [showLoader, setShowLoader] = useState(true);

    useEffect(() => {
        const timer = setTimeout(() => setShowLoader(false), 3500);
        return () => clearTimeout(timer);
    }, []);

    // Queries
    const varQuery = useQuery({
        queryKey: ['var', confidence, horizon],
        queryFn: () => fetchVaR(confidence, horizon),
        refetchInterval: 60000,
    });

    const stressQuery = useQuery({
        queryKey: ['stress-tests'],
        queryFn: fetchStressTests,
    });

    const recsQuery = useQuery({
        queryKey: ['recommendations'],
        queryFn: fetchRecommendations,
        refetchInterval: 60000,
    });

    const isLoading = varQuery.isLoading || stressQuery.isLoading || recsQuery.isLoading;

    if (showLoader) {
        return <CampingLoader />;
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-sapphire-950 via-sapphire-900 to-sapphire-950">
            <NavBar />

            <main className="container mx-auto px-4 py-8 space-y-8">
                {/* Page Header with fade-in animation */}
                <div className="flex items-center justify-between animate-fade-in-up">
                    <SectionHeader
                        title="Risk Analytics"
                        subtitle="Value-at-Risk, stress testing, and hedging recommendations"
                        icon={Shield}
                    />

                    {/* Controls with hover effects */}
                    <div className="flex items-center gap-4">
                        {/* Confidence Selector */}
                        <div className="flex items-center gap-2 bg-sapphire-800/30 rounded-lg px-3 py-2 border border-sapphire-700/30 hover:bg-sapphire-800/50 hover:border-sapphire-600/40 transition-all duration-300">
                            <Settings2 className="h-4 w-4 text-sapphire-400" />
                            <select
                                value={confidence}
                                onChange={(e) => setConfidence(parseFloat(e.target.value))}
                                className="bg-transparent text-sm text-white border-none focus:outline-none cursor-pointer"
                            >
                                <option value="0.95" className="bg-sapphire-900">95% Confidence</option>
                                <option value="0.99" className="bg-sapphire-900">99% Confidence</option>
                                <option value="0.90" className="bg-sapphire-900">90% Confidence</option>
                            </select>
                        </div>

                        {/* Horizon Selector */}
                        <div className="flex items-center gap-2 bg-sapphire-800/30 rounded-lg px-3 py-2 border border-sapphire-700/30 hover:bg-sapphire-800/50 hover:border-sapphire-600/40 transition-all duration-300">
                            <select
                                value={horizon}
                                onChange={(e) => setHorizon(parseInt(e.target.value))}
                                className="bg-transparent text-sm text-white border-none focus:outline-none cursor-pointer"
                            >
                                <option value="1" className="bg-sapphire-900">1-Day Horizon</option>
                                <option value="5" className="bg-sapphire-900">5-Day Horizon</option>
                                <option value="10" className="bg-sapphire-900">10-Day Horizon</option>
                            </select>
                        </div>

                        {/* Refresh Button with pulse animation */}
                        <button
                            onClick={() => {
                                varQuery.refetch();
                                recsQuery.refetch();
                            }}
                            disabled={isLoading}
                            className="flex items-center gap-2 px-4 py-2 accent-bg hover:opacity-90 hover:scale-105 rounded-lg text-white text-sm font-medium transition-all duration-300 disabled:opacity-50 hover:shadow-lg accent-glow-sm"
                        >
                            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                            Refresh
                        </button>
                    </div>
                </div>

                {/* VaR Analysis with fade-in */}
                <div className="animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
                    <VaRPanel
                        data={varQuery.data?.currencies || {}}
                        confidence={confidence}
                        horizonDays={horizon}
                        isLoading={varQuery.isLoading}
                    />
                </div>

                {/* Two Column Layout with staggered fade */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 animate-stagger-fade">
                    {/* Stress Tests with hover effects */}
                    <div className="group hover:-translate-y-1 hover:shadow-xl hover:shadow-sapphire-500/10 transition-all duration-500 relative overflow-hidden rounded-xl">
                        <StressScenariosTable
                            scenarios={stressQuery.data?.scenarios || []}
                            isLoading={stressQuery.isLoading}
                        />
                        {/* Shimmer effect */}
                        <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/[0.03] to-transparent pointer-events-none"></div>
                    </div>

                    {/* Recommendations with hover effects */}
                    <div className="group hover:-translate-y-1 hover:shadow-xl hover:shadow-sapphire-500/10 transition-all duration-500 relative overflow-hidden rounded-xl">
                        <RecommendationsPanel
                            data={recsQuery.data}
                            isLoading={recsQuery.isLoading}
                        />
                        {/* Shimmer effect */}
                        <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/[0.03] to-transparent pointer-events-none"></div>
                    </div>
                </div>

                {/* Data Attribution with fade-in */}
                <div className="text-center text-xs text-sapphire-400 pt-4 animate-fade-in-up" style={{ animationDelay: '0.5s' }}>
                    Risk metrics calculated using historical data. Past performance does not guarantee future results.
                </div>
            </main>
        </div>
    );
}
