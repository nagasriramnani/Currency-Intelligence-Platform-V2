'use client';

/**
 * EIS Companies Dashboard
 * Monitors Enterprise Investment Scheme companies for Sapphire Capital Partners
 * Stage 1 deliverable for KTP project
 */

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { SurfaceCard } from '@/components/SurfaceCard';
import { CampingLoader } from '@/components/CampingLoader';
import {
    Building2,
    TrendingUp,
    FileText,
    Download,
    Search,
    AlertTriangle,
    CheckCircle2,
    Clock,
    PoundSterling,
    Users,
    MapPin,
    Calendar,
    Loader2,
    ExternalLink,
    BarChart3,
    PieChart
} from 'lucide-react';

// Types
interface EISCompany {
    company_number: string;
    company_name: string;
    company_status: string;
    company_type: string;
    date_of_creation: string;
    sector: string;
    sic_codes: string[];
    registered_office_address: {
        address_line_1?: string;
        locality?: string;
        postal_code?: string;
        country?: string;
    };
    directors: { name: string; role: string }[];
    eis_status: string;
    investment_stage: string;
    amount_raised: number;
    risk_score: string;
}

interface EISSummary {
    total_companies: number;
    eis_approved: number;
    eis_pending: number;
    total_raised: number;
    average_raised: number;
    risk_breakdown: {
        low: number;
        medium: number;
        high: number;
    };
    sectors: Record<string, number>;
    investment_stages: Record<string, number>;
}

// API URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function EISPage() {
    const [isLoading, setIsLoading] = useState(true);
    const [companies, setCompanies] = useState<EISCompany[]>([]);
    const [summary, setSummary] = useState<EISSummary | null>(null);
    const [isGeneratingNewsletter, setIsGeneratingNewsletter] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedSector, setSelectedSector] = useState<string>('all');
    const [error, setError] = useState<string | null>(null);

    // Fetch EIS data
    useEffect(() => {
        const fetchData = async () => {
            try {
                // Fetch companies
                const companiesRes = await fetch(`${API_BASE}/api/eis/companies`);
                if (companiesRes.ok) {
                    const data = await companiesRes.json();
                    setCompanies(data.companies || []);
                }

                // Fetch summary
                const summaryRes = await fetch(`${API_BASE}/api/eis/summary`);
                if (summaryRes.ok) {
                    const data = await summaryRes.json();
                    setSummary(data);
                }
            } catch (err) {
                console.error('Failed to fetch EIS data:', err);
                setError('Failed to connect to backend. Please ensure the server is running.');
            } finally {
                // Artificial delay for loading animation
                setTimeout(() => setIsLoading(false), 2500);
            }
        };

        fetchData();
    }, []);

    // Download newsletter
    const handleDownloadNewsletter = async () => {
        setIsGeneratingNewsletter(true);
        try {
            const response = await fetch(`${API_BASE}/api/eis/newsletter`);
            if (!response.ok) throw new Error('Newsletter generation failed');

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `eis_newsletter_${new Date().toISOString().split('T')[0]}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        } catch (err) {
            console.error('Newsletter download failed:', err);
            alert('Failed to generate newsletter. Please ensure the backend is running.');
        } finally {
            setIsGeneratingNewsletter(false);
        }
    };

    // Filter companies
    const filteredCompanies = companies.filter(company => {
        const matchesSearch = searchQuery === '' ||
            company.company_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            company.company_number.includes(searchQuery);
        const matchesSector = selectedSector === 'all' || company.sector === selectedSector;
        return matchesSearch && matchesSector;
    });

    // Get unique sectors
    const sectors = [...new Set(companies.map(c => c.sector))];

    // Risk badge color
    const getRiskColor = (risk: string) => {
        switch (risk) {
            case 'Low': return 'bg-green-500/20 text-green-400 border-green-500/30';
            case 'Medium': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
            case 'High': return 'bg-red-500/20 text-red-400 border-red-500/30';
            default: return 'bg-sapphire-500/20 text-sapphire-400 border-sapphire-500/30';
        }
    };

    // EIS status badge
    const getStatusBadge = (status: string) => {
        if (status === 'Approved') {
            return (
                <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-500/20 text-green-400 text-xs">
                    <CheckCircle2 className="h-3 w-3" />
                    EIS Approved
                </span>
            );
        }
        return (
            <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-yellow-500/20 text-yellow-400 text-xs">
                <Clock className="h-3 w-3" />
                Pending
            </span>
        );
    };

    if (isLoading) {
        return <CampingLoader />;
    }

    return (
        <div className="min-h-screen bg-sapphire-950 text-white">
            {/* Simple EIS Header */}
            <header className="sticky top-0 z-50 w-full border-b border-sapphire-700/50 bg-sapphire-900/80 backdrop-blur-xl">
                <div className="container mx-auto px-4 h-16 flex items-center justify-between">
                    <Link href="/" className="flex items-center gap-3">
                        <div className="text-xl font-bold tracking-tight text-white">
                            Sapphire<span className="text-sapphire-400">Intelligence</span>
                        </div>
                    </Link>
                    <nav className="flex items-center gap-1">
                        <Link href="/" className="px-3 py-2 text-sm text-sapphire-200 hover:text-white rounded-lg hover:bg-sapphire-800/30">
                            Dashboard
                        </Link>
                        <Link href="/analysis" className="px-3 py-2 text-sm text-sapphire-200 hover:text-white rounded-lg hover:bg-sapphire-800/30">
                            Analysis
                        </Link>
                        <Link href="/risk" className="px-3 py-2 text-sm text-sapphire-200 hover:text-white rounded-lg hover:bg-sapphire-800/30">
                            Risk
                        </Link>
                        <Link href="/eis" className="px-3 py-2 text-sm text-white bg-sapphire-800/50 rounded-lg ring-1 ring-sapphire-700/50">
                            EIS
                        </Link>
                        <Link href="/settings" className="px-3 py-2 text-sm text-sapphire-200 hover:text-white rounded-lg hover:bg-sapphire-800/30">
                            Settings
                        </Link>
                    </nav>
                </div>
            </header>

            <main className="container mx-auto px-4 py-8 max-w-7xl">
                {/* Page Header */}
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8 animate-fade-in">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight text-white">
                            EIS <span className="accent-text-light">Companies</span>
                        </h1>
                        <p className="text-sapphire-300 mt-1">
                            Enterprise Investment Scheme company monitoring and newsletter automation
                        </p>
                    </div>

                    {/* Newsletter Download Button */}
                    <button
                        onClick={handleDownloadNewsletter}
                        disabled={isGeneratingNewsletter}
                        className="flex items-center gap-2 px-5 py-2.5 rounded-xl accent-bg text-white font-medium
                                   hover:opacity-90 transition-all duration-200 accent-glow-sm disabled:opacity-50
                                   self-start md:self-auto"
                    >
                        {isGeneratingNewsletter ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                            <FileText className="h-4 w-4" />
                        )}
                        <span>{isGeneratingNewsletter ? 'Generating...' : 'Download Newsletter'}</span>
                        <Download className="h-4 w-4" />
                    </button>
                </div>

                {/* Error Banner */}
                {error && (
                    <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 flex items-center gap-3">
                        <AlertTriangle className="h-5 w-5" />
                        <span>{error}</span>
                    </div>
                )}

                {/* KPI Cards */}
                {summary && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8 animate-stagger-fade">
                        <SurfaceCard className="p-4 bg-gradient-to-br from-sapphire-800/50 to-sapphire-900/50">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg accent-bg-subtle">
                                    <Building2 className="h-5 w-5 accent-text-light" />
                                </div>
                                <div>
                                    <p className="text-xs text-sapphire-400">Total Companies</p>
                                    <p className="text-2xl font-bold text-white">{summary.total_companies}</p>
                                </div>
                            </div>
                        </SurfaceCard>

                        <SurfaceCard className="p-4 bg-gradient-to-br from-green-900/30 to-sapphire-900/50">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-green-500/20">
                                    <CheckCircle2 className="h-5 w-5 text-green-400" />
                                </div>
                                <div>
                                    <p className="text-xs text-sapphire-400">EIS Approved</p>
                                    <p className="text-2xl font-bold text-green-400">{summary.eis_approved}</p>
                                </div>
                            </div>
                        </SurfaceCard>

                        <SurfaceCard className="p-4 bg-gradient-to-br from-sapphire-800/50 to-sapphire-900/50">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-emerald-500/20">
                                    <PoundSterling className="h-5 w-5 text-emerald-400" />
                                </div>
                                <div>
                                    <p className="text-xs text-sapphire-400">Total Raised</p>
                                    <p className="text-2xl font-bold text-white">£{(summary.total_raised / 1000000).toFixed(1)}M</p>
                                </div>
                            </div>
                        </SurfaceCard>

                        <SurfaceCard className="p-4 bg-gradient-to-br from-sapphire-800/50 to-sapphire-900/50">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-blue-500/20">
                                    <TrendingUp className="h-5 w-5 text-blue-400" />
                                </div>
                                <div>
                                    <p className="text-xs text-sapphire-400">Avg Investment</p>
                                    <p className="text-2xl font-bold text-white">£{(summary.average_raised / 1000).toFixed(0)}K</p>
                                </div>
                            </div>
                        </SurfaceCard>
                    </div>
                )}

                {/* Summary Charts Row */}
                {summary && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                        {/* Sector Breakdown */}
                        <SurfaceCard className="p-5">
                            <div className="flex items-center gap-2 mb-4">
                                <PieChart className="h-5 w-5 accent-text-light" />
                                <h3 className="font-semibold text-white">Sector Breakdown</h3>
                            </div>
                            <div className="space-y-3">
                                {Object.entries(summary.sectors).map(([sector, count]) => (
                                    <div key={sector} className="flex items-center justify-between">
                                        <span className="text-sapphire-300">{sector}</span>
                                        <div className="flex items-center gap-3">
                                            <div className="w-24 h-2 bg-sapphire-800 rounded-full overflow-hidden">
                                                <div
                                                    className="h-full accent-bg rounded-full transition-all duration-500"
                                                    style={{ width: `${(count / summary.total_companies) * 100}%` }}
                                                />
                                            </div>
                                            <span className="text-sm text-white font-medium w-6">{count}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </SurfaceCard>

                        {/* Risk Distribution */}
                        <SurfaceCard className="p-5">
                            <div className="flex items-center gap-2 mb-4">
                                <BarChart3 className="h-5 w-5 accent-text-light" />
                                <h3 className="font-semibold text-white">Risk Distribution</h3>
                            </div>
                            <div className="flex gap-4 h-32">
                                {['low', 'medium', 'high'].map((risk) => {
                                    const count = summary.risk_breakdown[risk as keyof typeof summary.risk_breakdown];
                                    const percentage = (count / summary.total_companies) * 100;
                                    const colors = {
                                        low: 'bg-green-500',
                                        medium: 'bg-yellow-500',
                                        high: 'bg-red-500'
                                    };
                                    return (
                                        <div key={risk} className="flex-1 flex flex-col items-center justify-end">
                                            <span className="text-lg font-bold text-white mb-2">{count}</span>
                                            <div
                                                className={`w-full ${colors[risk as keyof typeof colors]} rounded-t-lg transition-all duration-500`}
                                                style={{ height: `${Math.max(percentage, 10)}%` }}
                                            />
                                            <span className="text-xs text-sapphire-400 mt-2 capitalize">{risk}</span>
                                        </div>
                                    );
                                })}
                            </div>
                        </SurfaceCard>
                    </div>
                )}

                {/* Filters */}
                <div className="flex flex-col md:flex-row gap-4 mb-6">
                    {/* Search */}
                    <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-sapphire-400" />
                        <input
                            type="text"
                            placeholder="Search companies..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-sapphire-800/50 border border-sapphire-700/50
                                       text-white placeholder-sapphire-400 focus:outline-none focus:ring-2 focus:ring-sapphire-500/50"
                        />
                    </div>

                    {/* Sector Filter */}
                    <select
                        value={selectedSector}
                        onChange={(e) => setSelectedSector(e.target.value)}
                        className="px-4 py-2.5 rounded-xl bg-sapphire-800/50 border border-sapphire-700/50
                                   text-white focus:outline-none focus:ring-2 focus:ring-sapphire-500/50"
                    >
                        <option value="all">All Sectors</option>
                        {sectors.map(sector => (
                            <option key={sector} value={sector}>{sector}</option>
                        ))}
                    </select>
                </div>

                {/* Company Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-stagger-fade">
                    {filteredCompanies.map((company) => (
                        <SurfaceCard
                            key={company.company_number}
                            className="p-5 hover:border-sapphire-600/50 transition-all duration-300 group"
                        >
                            {/* Header */}
                            <div className="flex items-start justify-between mb-3">
                                <div className="flex-1 min-w-0">
                                    <h3 className="font-semibold text-white truncate group-hover:accent-text-light transition-colors">
                                        {company.company_name}
                                    </h3>
                                    <p className="text-xs text-sapphire-400">#{company.company_number}</p>
                                </div>
                                {getStatusBadge(company.eis_status)}
                            </div>

                            {/* Sector & Location */}
                            <div className="flex flex-wrap gap-2 mb-4">
                                <span className="flex items-center gap-1 px-2 py-1 rounded-lg bg-sapphire-800/50 text-xs text-sapphire-300">
                                    <TrendingUp className="h-3 w-3" />
                                    {company.sector}
                                </span>
                                <span className="flex items-center gap-1 px-2 py-1 rounded-lg bg-sapphire-800/50 text-xs text-sapphire-300">
                                    <MapPin className="h-3 w-3" />
                                    {company.registered_office_address?.locality || 'UK'}
                                </span>
                            </div>

                            {/* Metrics */}
                            <div className="grid grid-cols-3 gap-3 mb-4">
                                <div className="text-center p-2 rounded-lg bg-sapphire-800/30">
                                    <p className="text-xs text-sapphire-400">Raised</p>
                                    <p className="text-sm font-semibold text-white">
                                        £{(company.amount_raised / 1000).toFixed(0)}K
                                    </p>
                                </div>
                                <div className="text-center p-2 rounded-lg bg-sapphire-800/30">
                                    <p className="text-xs text-sapphire-400">Stage</p>
                                    <p className="text-sm font-semibold text-white">{company.investment_stage}</p>
                                </div>
                                <div className="text-center p-2 rounded-lg bg-sapphire-800/30">
                                    <p className="text-xs text-sapphire-400">Risk</p>
                                    <span className={`text-sm font-semibold px-2 py-0.5 rounded border ${getRiskColor(company.risk_score)}`}>
                                        {company.risk_score}
                                    </span>
                                </div>
                            </div>

                            {/* Directors */}
                            {company.directors && company.directors.length > 0 && (
                                <div className="pt-3 border-t border-sapphire-700/30">
                                    <div className="flex items-center gap-2 text-xs text-sapphire-400 mb-2">
                                        <Users className="h-3 w-3" />
                                        <span>Key Directors</span>
                                    </div>
                                    <div className="space-y-1">
                                        {company.directors.slice(0, 2).map((director, i) => (
                                            <p key={i} className="text-sm text-sapphire-200 truncate">
                                                {director.name}
                                            </p>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Founded Date */}
                            <div className="flex items-center gap-2 mt-3 text-xs text-sapphire-500">
                                <Calendar className="h-3 w-3" />
                                <span>Founded {company.date_of_creation}</span>
                            </div>
                        </SurfaceCard>
                    ))}
                </div>

                {/* Empty State */}
                {filteredCompanies.length === 0 && !error && (
                    <div className="text-center py-16">
                        <Building2 className="h-12 w-12 text-sapphire-600 mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-sapphire-300 mb-2">No companies found</h3>
                        <p className="text-sapphire-500">Try adjusting your search or filter criteria</p>
                    </div>
                )}
            </main>
        </div>
    );
}
