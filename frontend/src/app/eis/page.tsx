'use client';

/**
 * EIS Companies Dashboard - Stage 1 MVP
 * Enterprise Investment Scheme fact-finding and assessment
 * 
 * Features:
 * - Full Companies House data integration (Profile, Officers, PSCs, Charges, Filings)
 * - EIS-likelihood heuristic scoring
 * - Dynamic portfolio dashboard
 * - Comprehensive company fact sheets
 * - Automated newsletter generation
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import Link from 'next/link';
import { SurfaceCard } from '@/components/SurfaceCard';
import { CampingLoader } from '@/components/CampingLoader';
import {
    Building2, TrendingUp, FileText, Download, Search, AlertTriangle,
    CheckCircle2, Clock, Users, MapPin, Loader2, ExternalLink,
    BarChart3, PieChart, Database, X, ChevronDown, ChevronUp,
    Shield, Info, Award, FileCheck, Briefcase, Scale, AlertCircle,
    Target, DollarSign, User
} from 'lucide-react';

// === TYPES ===
interface FullCompanyProfile {
    company: {
        company_number: string;
        company_name: string;
        company_status: string;
        company_type: string;
        date_of_creation?: string;
        jurisdiction: string;
        registered_office_address: Record<string, string>;
        sic_codes: string[];
        has_charges: boolean;
        has_insolvency_history: boolean;
    };
    officers: {
        items: Array<{
            name: string;
            officer_role: string;
            appointed_on?: string;
            nationality?: string;
            occupation?: string;
        }>;
        director_count: number;
        total_count: number;
        directors: Array<any>;
    };
    pscs: {
        items: Array<{
            name: string;
            ownership_level: string;
            natures_of_control: string[];
            is_active: boolean;
            nationality?: string;
        }>;
        active_count: number;
        total_count: number;
    };
    charges: {
        items: Array<{
            status: string;
            created_on?: string;
            description: string;
            persons_entitled: string[];
            is_outstanding: boolean;
        }>;
        outstanding_count: number;
        total_count: number;
        has_outstanding: boolean;
    };
    filings: {
        items: Array<{
            date: string;
            type: string;
            category: string;
            description: string;
        }>;
        analysis: {
            total_filings: number;
            has_share_allotments: boolean;
            share_allotment_count: number;
            has_annual_accounts: boolean;
            accounts_type?: string;
            last_accounts_date?: string;
            last_confirmation_statement?: string;
        };
    };
    eis_assessment: {
        score: number;
        max_score: number;
        percentage: number;
        status: string;
        status_description: string;
        confidence: string;
        factors: Array<{
            factor: string;
            value: string;
            points: number;
            max_points: number;
            rationale: string;
            impact: string;
        }>;
        flags: string[];
        recommendations: string[];
        disclaimer: string;
    };
    data_sources: string[];
    retrieved_at: string;
}

interface SearchResult {
    company_number: string;
    title: string;
    company_status: string;
    company_type: string;
    date_of_creation?: string;
    address_snippet?: string;
}

// === CONSTANTS ===
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// === COMPONENT ===
export default function EISPage() {
    // State
    const [isLoading, setIsLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
    const [selectedCompanies, setSelectedCompanies] = useState<FullCompanyProfile[]>([]);
    const [isSearching, setIsSearching] = useState(false);
    const [isGeneratingNewsletter, setIsGeneratingNewsletter] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [apiConfigured, setApiConfigured] = useState(true);
    const [lastSearchQuery, setLastSearchQuery] = useState('');
    const [loadingDetails, setLoadingDetails] = useState<Set<string>>(new Set());
    const [expandedCompanies, setExpandedCompanies] = useState<Set<string>>(new Set());
    const [expandedSections, setExpandedSections] = useState<Record<string, Set<string>>>({});

    // Calculate portfolio analytics
    const portfolioStats = useMemo(() => {
        if (selectedCompanies.length === 0) return null;

        const companies = selectedCompanies;

        // EIS status distribution
        const eisStatus = { eligible: 0, review: 0, ineligible: 0 };
        companies.forEach(c => {
            const status = c.eis_assessment?.status || '';
            if (status.includes('Likely Eligible')) eisStatus.eligible++;
            else if (status.includes('Review')) eisStatus.review++;
            else eisStatus.ineligible++;
        });

        // Average score
        const avgScore = companies.reduce((sum, c) => sum + (c.eis_assessment?.score || 0), 0) / companies.length;

        // Sector breakdown
        const sectors: Record<string, number> = {};
        companies.forEach(c => {
            const sic = c.company.sic_codes?.[0]?.substring(0, 2) || 'Other';
            const sector = getSectorFromSic(sic);
            sectors[sector] = (sectors[sector] || 0) + 1;
        });

        // Total directors & PSCs
        const totalDirectors = companies.reduce((sum, c) => sum + (c.officers?.director_count || 0), 0);
        const totalPSCs = companies.reduce((sum, c) => sum + (c.pscs?.active_count || 0), 0);

        // Risk indicators
        const withCharges = companies.filter(c => c.charges?.has_outstanding).length;
        const withInsolvency = companies.filter(c => c.company.has_insolvency_history).length;

        return {
            total: companies.length,
            eisStatus,
            avgScore: Math.round(avgScore),
            sectors,
            totalDirectors,
            totalPSCs,
            withCharges,
            withInsolvency
        };
    }, [selectedCompanies]);

    // Helper functions
    function getSectorFromSic(sicPrefix: string): string {
        const map: Record<string, string> = {
            '62': 'Technology', '63': 'Technology', '72': 'R&D',
            '58': 'Media', '61': 'Telecoms', '64': 'Finance',
            '86': 'Healthcare', '21': 'Pharma', '35': 'Energy',
            '01': 'Agriculture', '41': 'Construction', '68': 'Real Estate'
        };
        return map[sicPrefix] || 'Other';
    }

    function getCompanyAge(dateOfCreation?: string): number {
        if (!dateOfCreation) return 0;
        const created = new Date(dateOfCreation);
        const now = new Date();
        return Math.floor((now.getTime() - created.getTime()) / (365.25 * 24 * 60 * 60 * 1000));
    }

    // Load initial data
    useEffect(() => {
        const checkHealth = async () => {
            try {
                const res = await fetch(`${API_BASE}/api/eis/health`);
                if (res.ok) {
                    const data = await res.json();
                    setApiConfigured(data.companies_house_configured);
                }
            } catch (err) {
                console.error('Health check failed:', err);
            } finally {
                setTimeout(() => setIsLoading(false), 1000);
            }
        };
        checkHealth();
    }, []);

    // Search handler
    const handleSearch = useCallback(async () => {
        if (!searchQuery.trim() || searchQuery.length < 2) {
            setError('Please enter at least 2 characters');
            return;
        }
        setIsSearching(true);
        setError(null);
        setLastSearchQuery(searchQuery);

        try {
            const res = await fetch(`${API_BASE}/api/eis/search?query=${encodeURIComponent(searchQuery)}&limit=30`);
            if (!res.ok) throw new Error('Search failed');
            const data = await res.json();
            setSearchResults(data.results || []);
            if (data.results.length === 0) {
                setError(`No companies found for "${searchQuery}"`);
            }
        } catch (err: any) {
            setError(err.message);
            setSearchResults([]);
        } finally {
            setIsSearching(false);
        }
    }, [searchQuery]);

    // Load full company profile
    const loadFullProfile = async (companyNumber: string) => {
        if (selectedCompanies.some(c => c.company.company_number === companyNumber)) return;

        setLoadingDetails(prev => new Set(prev).add(companyNumber));
        try {
            const res = await fetch(`${API_BASE}/api/eis/company/${companyNumber}/full-profile`);
            if (res.ok) {
                const profile: FullCompanyProfile = await res.json();
                setSelectedCompanies(prev => [...prev, profile]);
                setExpandedCompanies(prev => new Set(prev).add(companyNumber));
            } else {
                throw new Error('Failed to load company profile');
            }
        } catch (err) {
            console.error('Failed to load profile:', err);
            setError('Failed to load company details');
        } finally {
            setLoadingDetails(prev => {
                const next = new Set(prev);
                next.delete(companyNumber);
                return next;
            });
        }
    };

    // Download newsletter
    const handleDownloadNewsletter = async () => {
        if (selectedCompanies.length === 0) {
            alert('Please select at least one company');
            return;
        }

        setIsGeneratingNewsletter(true);
        try {
            const companies = selectedCompanies.map(p => ({
                ...p.company,
                directors: p.officers?.directors || [],
                pscs: p.pscs?.items || [],
                charges: p.charges?.items || [],
                filings: p.filings?.items || [],
                filing_analysis: p.filings?.analysis || {},
                eis_assessment: p.eis_assessment
            }));

            const response = await fetch(`${API_BASE}/api/eis/newsletter`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(companies)
            });

            if (!response.ok) throw new Error('Newsletter generation failed');

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `eis_portfolio_report_${new Date().toISOString().split('T')[0]}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        } catch (err: any) {
            alert(err.message || 'Failed to generate newsletter');
        } finally {
            setIsGeneratingNewsletter(false);
        }
    };

    // Toggle section
    const toggleSection = (companyNumber: string, section: string) => {
        setExpandedSections(prev => {
            const companySections = prev[companyNumber] || new Set();
            const next = new Set(companySections);
            if (next.has(section)) next.delete(section);
            else next.add(section);
            return { ...prev, [companyNumber]: next };
        });
    };

    const removeCompany = (companyNumber: string) => {
        setSelectedCompanies(prev => prev.filter(c => c.company.company_number !== companyNumber));
    };

    // EIS Score Badge
    const EISScoreBadge = ({ assessment }: { assessment: FullCompanyProfile['eis_assessment'] }) => {
        const score = assessment?.score || 0;
        const status = assessment?.status || 'Unknown';

        let bgColor = 'bg-gray-500/20';
        let textColor = 'text-gray-400';
        let borderColor = 'border-gray-500/30';

        if (status.includes('Likely Eligible')) {
            bgColor = 'bg-green-500/20';
            textColor = 'text-green-400';
            borderColor = 'border-green-500/30';
        } else if (status.includes('Review')) {
            bgColor = 'bg-yellow-500/20';
            textColor = 'text-yellow-400';
            borderColor = 'border-yellow-500/30';
        } else if (status.includes('Ineligible')) {
            bgColor = 'bg-red-500/20';
            textColor = 'text-red-400';
            borderColor = 'border-red-500/30';
        }

        return (
            <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg ${bgColor} ${textColor} border ${borderColor}`}>
                <Target className="h-4 w-4" />
                <span className="font-bold">{score}/100</span>
                <span className="text-xs opacity-80">{status}</span>
            </div>
        );
    };

    if (isLoading) return <CampingLoader />;

    return (
        <div className="min-h-screen bg-sapphire-950 text-white">
            {/* Header */}
            <header className="sticky top-0 z-50 w-full border-b border-sapphire-700/50 bg-sapphire-900/80 backdrop-blur-xl">
                <div className="container mx-auto px-4 h-16 flex items-center justify-between">
                    <Link href="/" className="text-xl font-bold text-white">
                        Sapphire<span className="text-sapphire-400">Intelligence</span>
                    </Link>
                    <nav className="flex items-center gap-1">
                        <Link href="/" className="px-3 py-2 text-sm text-sapphire-200 hover:text-white rounded-lg hover:bg-sapphire-800/30">Dashboard</Link>
                        <Link href="/analysis" className="px-3 py-2 text-sm text-sapphire-200 hover:text-white rounded-lg hover:bg-sapphire-800/30">Analysis</Link>
                        <Link href="/eis" className="px-3 py-2 text-sm text-white bg-sapphire-800/50 rounded-lg ring-1 ring-sapphire-700/50">EIS</Link>
                        <Link href="/settings" className="px-3 py-2 text-sm text-sapphire-200 hover:text-white rounded-lg hover:bg-sapphire-800/30">Settings</Link>
                    </nav>
                </div>
            </header>

            <main className="container mx-auto px-4 py-8 max-w-7xl">
                {/* Page Header */}
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
                    <div>
                        <h1 className="text-3xl font-bold">EIS <span className="accent-text-light">Fact-Finding</span></h1>
                        <p className="text-sapphire-300 mt-1">Stage 1: Company assessment using Companies House data</p>
                    </div>

                    <div className="flex items-center gap-3">
                        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm ${apiConfigured ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                            }`}>
                            <Database className="h-4 w-4" />
                            {apiConfigured ? 'API Connected' : 'API Error'}
                        </div>

                        <button
                            onClick={handleDownloadNewsletter}
                            disabled={isGeneratingNewsletter || selectedCompanies.length === 0}
                            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium transition-all duration-200
                                       ${selectedCompanies.length > 0
                                    ? 'accent-bg text-white hover:opacity-90'
                                    : 'bg-sapphire-800/50 text-sapphire-400 cursor-not-allowed'}`}
                        >
                            {isGeneratingNewsletter ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
                            <span>Generate Report ({selectedCompanies.length})</span>
                            <Download className="h-4 w-4" />
                        </button>
                    </div>
                </div>

                {/* Error Banner */}
                {error && (
                    <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 flex items-center gap-3">
                        <AlertTriangle className="h-5 w-5 flex-shrink-0" />
                        <span>{error}</span>
                        <button onClick={() => setError(null)} className="ml-auto"><X className="h-4 w-4" /></button>
                    </div>
                )}

                {/* Portfolio Dashboard */}
                {portfolioStats && (
                    <div className="mb-8">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                                <PieChart className="h-5 w-5 accent-text-light" />
                                Portfolio Analysis ({portfolioStats.total} Companies)
                            </h2>
                            <button onClick={() => setSelectedCompanies([])} className="text-sm text-sapphire-400 hover:text-white">
                                Clear All
                            </button>
                        </div>

                        {/* KPI Cards */}
                        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-6">
                            <SurfaceCard className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-green-500/20"><CheckCircle2 className="h-5 w-5 text-green-400" /></div>
                                    <div>
                                        <p className="text-xs text-sapphire-400">Likely Eligible</p>
                                        <p className="text-2xl font-bold text-green-400">{portfolioStats.eisStatus.eligible}</p>
                                    </div>
                                </div>
                            </SurfaceCard>
                            <SurfaceCard className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-yellow-500/20"><AlertCircle className="h-5 w-5 text-yellow-400" /></div>
                                    <div>
                                        <p className="text-xs text-sapphire-400">Review Required</p>
                                        <p className="text-2xl font-bold text-yellow-400">{portfolioStats.eisStatus.review}</p>
                                    </div>
                                </div>
                            </SurfaceCard>
                            <SurfaceCard className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg accent-bg-subtle"><Target className="h-5 w-5 accent-text-light" /></div>
                                    <div>
                                        <p className="text-xs text-sapphire-400">Avg EIS Score</p>
                                        <p className="text-2xl font-bold text-white">{portfolioStats.avgScore}</p>
                                    </div>
                                </div>
                            </SurfaceCard>
                            <SurfaceCard className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-purple-500/20"><Users className="h-5 w-5 text-purple-400" /></div>
                                    <div>
                                        <p className="text-xs text-sapphire-400">Directors</p>
                                        <p className="text-2xl font-bold text-white">{portfolioStats.totalDirectors}</p>
                                    </div>
                                </div>
                            </SurfaceCard>
                            <SurfaceCard className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-blue-500/20"><User className="h-5 w-5 text-blue-400" /></div>
                                    <div>
                                        <p className="text-xs text-sapphire-400">PSCs</p>
                                        <p className="text-2xl font-bold text-white">{portfolioStats.totalPSCs}</p>
                                    </div>
                                </div>
                            </SurfaceCard>
                            <SurfaceCard className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className={`p-2 rounded-lg ${portfolioStats.withCharges > 0 ? 'bg-red-500/20' : 'bg-green-500/20'}`}>
                                        <Scale className={`h-5 w-5 ${portfolioStats.withCharges > 0 ? 'text-red-400' : 'text-green-400'}`} />
                                    </div>
                                    <div>
                                        <p className="text-xs text-sapphire-400">With Charges</p>
                                        <p className="text-2xl font-bold text-white">{portfolioStats.withCharges}</p>
                                    </div>
                                </div>
                            </SurfaceCard>
                        </div>

                        {/* Data Source Info */}
                        <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-300 text-sm flex items-start gap-2">
                            <Info className="h-4 w-4 mt-0.5 flex-shrink-0" />
                            <span>
                                <strong>Data Source:</strong> UK Companies House Registry (Profile, Officers, PSCs, Charges, Filings).
                                EIS scores are heuristic-based assessments, not official HMRC determinations.
                            </span>
                        </div>
                    </div>
                )}

                {/* Search */}
                <SurfaceCard className="p-6 mb-8">
                    <div className="flex gap-3">
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-sapphire-400" />
                            <input
                                type="text"
                                placeholder="Search company name or number..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                                className="w-full pl-10 pr-4 py-3 rounded-xl bg-sapphire-800/50 border border-sapphire-700/50
                                           text-white placeholder-sapphire-400 focus:outline-none focus:ring-2 focus:ring-sapphire-500/50 text-lg"
                            />
                            {searchQuery && (
                                <button onClick={() => { setSearchQuery(''); setSearchResults([]); setLastSearchQuery(''); }} className="absolute right-3 top-1/2 -translate-y-1/2">
                                    <X className="h-4 w-4 text-sapphire-400 hover:text-white" />
                                </button>
                            )}
                        </div>
                        <button
                            onClick={handleSearch}
                            disabled={isSearching || !apiConfigured}
                            className="flex items-center gap-2 px-6 py-3 rounded-xl bg-sapphire-600 text-white font-medium hover:bg-sapphire-500 transition-all disabled:opacity-50"
                        >
                            {isSearching ? <Loader2 className="h-5 w-5 animate-spin" /> : <Search className="h-5 w-5" />}
                            <span>Search</span>
                        </button>
                    </div>
                    <p className="text-sm text-sapphire-500 mt-2">
                        💡 Click "Add to Portfolio" to load full company data with EIS assessment
                    </p>
                </SurfaceCard>

                {/* Search Results */}
                {searchResults.length > 0 && (
                    <div className="mb-8">
                        <h2 className="text-lg font-semibold text-white mb-4">Results for "{lastSearchQuery}" ({searchResults.length})</h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {searchResults.map((company) => {
                                const isLoading = loadingDetails.has(company.company_number);
                                const isSelected = selectedCompanies.some(c => c.company.company_number === company.company_number);

                                return (
                                    <SurfaceCard key={company.company_number} className="p-4 hover:border-sapphire-600/50 transition-all">
                                        <div className="flex items-start justify-between mb-2">
                                            <div className="flex-1 min-w-0">
                                                <h3 className="font-semibold text-white truncate">{company.title}</h3>
                                                <p className="text-xs text-sapphire-400">#{company.company_number}</p>
                                            </div>
                                            <span className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-xs ${company.company_status === 'active' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'
                                                }`}>
                                                {company.company_status === 'active' ? <CheckCircle2 className="h-3 w-3" /> : <Clock className="h-3 w-3" />}
                                                {company.company_status}
                                            </span>
                                        </div>
                                        {company.address_snippet && (
                                            <p className="text-sm text-sapphire-300 mb-3 line-clamp-1">
                                                <MapPin className="h-3 w-3 inline mr-1" />{company.address_snippet}
                                            </p>
                                        )}
                                        <button
                                            onClick={() => loadFullProfile(company.company_number)}
                                            disabled={isLoading || isSelected}
                                            className={`w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors
                                                ${isSelected
                                                    ? 'bg-green-500/20 text-green-400'
                                                    : 'bg-sapphire-700/50 text-white hover:bg-sapphire-600/50'}`}
                                        >
                                            {isLoading ? (
                                                <><Loader2 className="h-4 w-4 animate-spin" /> Loading...</>
                                            ) : isSelected ? (
                                                <><CheckCircle2 className="h-4 w-4" /> Added to Portfolio</>
                                            ) : (
                                                <><ExternalLink className="h-4 w-4" /> Add to Portfolio</>
                                            )}
                                        </button>
                                    </SurfaceCard>
                                );
                            })}
                        </div>
                    </div>
                )}

                {/* Selected Company Profiles */}
                {selectedCompanies.length > 0 && (
                    <div>
                        <h2 className="text-lg font-semibold text-white mb-4">Company Fact Sheets</h2>

                        <div className="space-y-6">
                            {selectedCompanies.map((profile) => {
                                const companyNum = profile.company.company_number;
                                const sections = expandedSections[companyNum] || new Set();
                                const age = getCompanyAge(profile.company.date_of_creation);

                                return (
                                    <SurfaceCard key={companyNum} className="overflow-hidden">
                                        {/* Header */}
                                        <div className="p-6 border-b border-sapphire-700/30">
                                            <div className="flex items-start justify-between">
                                                <div>
                                                    <h3 className="text-xl font-bold text-white">{profile.company.company_name}</h3>
                                                    <p className="text-sm text-sapphire-400">
                                                        #{profile.company.company_number} • {profile.company.company_type} • {age} years old
                                                    </p>
                                                </div>
                                                <div className="flex items-center gap-3">
                                                    <EISScoreBadge assessment={profile.eis_assessment} />
                                                    <button onClick={() => removeCompany(companyNum)} className="text-sapphire-400 hover:text-white">
                                                        <X className="h-5 w-5" />
                                                    </button>
                                                </div>
                                            </div>

                                            {/* Quick Stats */}
                                            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mt-4">
                                                <div className="p-2 rounded bg-sapphire-800/30 text-center">
                                                    <p className="text-xs text-sapphire-400">Status</p>
                                                    <p className={`text-sm font-medium ${profile.company.company_status === 'active' ? 'text-green-400' : 'text-yellow-400'}`}>
                                                        {profile.company.company_status}
                                                    </p>
                                                </div>
                                                <div className="p-2 rounded bg-sapphire-800/30 text-center">
                                                    <p className="text-xs text-sapphire-400">Directors</p>
                                                    <p className="text-sm font-medium text-white">{profile.officers?.director_count || 0}</p>
                                                </div>
                                                <div className="p-2 rounded bg-sapphire-800/30 text-center">
                                                    <p className="text-xs text-sapphire-400">PSCs</p>
                                                    <p className="text-sm font-medium text-white">{profile.pscs?.active_count || 0}</p>
                                                </div>
                                                <div className="p-2 rounded bg-sapphire-800/30 text-center">
                                                    <p className="text-xs text-sapphire-400">Charges</p>
                                                    <p className={`text-sm font-medium ${profile.charges?.has_outstanding ? 'text-red-400' : 'text-green-400'}`}>
                                                        {profile.charges?.outstanding_count || 0} outstanding
                                                    </p>
                                                </div>
                                                <div className="p-2 rounded bg-sapphire-800/30 text-center">
                                                    <p className="text-xs text-sapphire-400">Filings</p>
                                                    <p className="text-sm font-medium text-white">{profile.filings?.analysis?.total_filings || 0}</p>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Expandable Sections */}
                                        <div className="divide-y divide-sapphire-700/30">
                                            {/* EIS Assessment */}
                                            <div>
                                                <button
                                                    onClick={() => toggleSection(companyNum, 'eis')}
                                                    className="w-full flex items-center justify-between p-4 hover:bg-sapphire-800/30 transition-colors"
                                                >
                                                    <div className="flex items-center gap-3">
                                                        <Award className="h-5 w-5 accent-text-light" />
                                                        <span className="font-medium text-white">EIS Assessment Details</span>
                                                    </div>
                                                    {sections.has('eis') ? <ChevronUp className="h-5 w-5 text-sapphire-400" /> : <ChevronDown className="h-5 w-5 text-sapphire-400" />}
                                                </button>
                                                {sections.has('eis') && (
                                                    <div className="px-4 pb-4">
                                                        <div className="bg-sapphire-800/30 rounded-lg p-4">
                                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                                {profile.eis_assessment?.factors?.map((factor, i) => (
                                                                    <div key={i} className="flex items-start gap-3">
                                                                        <div className={`p-1 rounded ${factor.impact === 'positive' ? 'bg-green-500/20' :
                                                                                factor.impact === 'negative' ? 'bg-red-500/20' : 'bg-yellow-500/20'
                                                                            }`}>
                                                                            {factor.impact === 'positive' ? <CheckCircle2 className="h-4 w-4 text-green-400" /> :
                                                                                factor.impact === 'negative' ? <X className="h-4 w-4 text-red-400" /> :
                                                                                    <AlertCircle className="h-4 w-4 text-yellow-400" />}
                                                                        </div>
                                                                        <div className="flex-1">
                                                                            <div className="flex justify-between">
                                                                                <span className="text-sm font-medium text-white">{factor.factor}</span>
                                                                                <span className="text-sm text-sapphire-400">{factor.points}/{factor.max_points}</span>
                                                                            </div>
                                                                            <p className="text-xs text-sapphire-400">{factor.rationale}</p>
                                                                        </div>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                            {profile.eis_assessment?.flags?.length > 0 && (
                                                                <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                                                                    <p className="text-sm font-medium text-yellow-400 mb-2">⚠️ Flags</p>
                                                                    {profile.eis_assessment.flags.map((flag, i) => (
                                                                        <p key={i} className="text-sm text-yellow-300">• {flag}</p>
                                                                    ))}
                                                                </div>
                                                            )}
                                                            <p className="text-xs text-sapphire-500 mt-4 italic">{profile.eis_assessment?.disclaimer}</p>
                                                        </div>
                                                    </div>
                                                )}
                                            </div>

                                            {/* Directors */}
                                            <div>
                                                <button
                                                    onClick={() => toggleSection(companyNum, 'directors')}
                                                    className="w-full flex items-center justify-between p-4 hover:bg-sapphire-800/30 transition-colors"
                                                >
                                                    <div className="flex items-center gap-3">
                                                        <Users className="h-5 w-5 text-purple-400" />
                                                        <span className="font-medium text-white">Directors & Officers ({profile.officers?.total_count || 0})</span>
                                                    </div>
                                                    {sections.has('directors') ? <ChevronUp className="h-5 w-5 text-sapphire-400" /> : <ChevronDown className="h-5 w-5 text-sapphire-400" />}
                                                </button>
                                                {sections.has('directors') && (
                                                    <div className="px-4 pb-4 grid grid-cols-1 md:grid-cols-2 gap-3">
                                                        {profile.officers?.items?.slice(0, 10).map((officer, i) => (
                                                            <div key={i} className="p-3 bg-sapphire-800/30 rounded-lg">
                                                                <p className="font-medium text-white">{officer.name}</p>
                                                                <p className="text-sm text-sapphire-400">{officer.officer_role}</p>
                                                                {officer.appointed_on && <p className="text-xs text-sapphire-500">Appointed: {officer.appointed_on}</p>}
                                                            </div>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>

                                            {/* PSCs */}
                                            <div>
                                                <button
                                                    onClick={() => toggleSection(companyNum, 'pscs')}
                                                    className="w-full flex items-center justify-between p-4 hover:bg-sapphire-800/30 transition-colors"
                                                >
                                                    <div className="flex items-center gap-3">
                                                        <User className="h-5 w-5 text-blue-400" />
                                                        <span className="font-medium text-white">Significant Shareholders ({profile.pscs?.total_count || 0})</span>
                                                    </div>
                                                    {sections.has('pscs') ? <ChevronUp className="h-5 w-5 text-sapphire-400" /> : <ChevronDown className="h-5 w-5 text-sapphire-400" />}
                                                </button>
                                                {sections.has('pscs') && (
                                                    <div className="px-4 pb-4 grid grid-cols-1 md:grid-cols-2 gap-3">
                                                        {profile.pscs?.items?.map((psc, i) => (
                                                            <div key={i} className={`p-3 rounded-lg ${psc.is_active ? 'bg-sapphire-800/30' : 'bg-sapphire-800/10 opacity-60'}`}>
                                                                <p className="font-medium text-white">{psc.name}</p>
                                                                <p className="text-sm text-sapphire-400">Ownership: {psc.ownership_level}</p>
                                                                {!psc.is_active && <p className="text-xs text-red-400">No longer active</p>}
                                                            </div>
                                                        ))}
                                                        {(profile.pscs?.items?.length || 0) === 0 && (
                                                            <p className="text-sapphire-400 text-sm">No PSC records found</p>
                                                        )}
                                                    </div>
                                                )}
                                            </div>

                                            {/* Charges */}
                                            <div>
                                                <button
                                                    onClick={() => toggleSection(companyNum, 'charges')}
                                                    className="w-full flex items-center justify-between p-4 hover:bg-sapphire-800/30 transition-colors"
                                                >
                                                    <div className="flex items-center gap-3">
                                                        <Scale className={`h-5 w-5 ${profile.charges?.has_outstanding ? 'text-red-400' : 'text-green-400'}`} />
                                                        <span className="font-medium text-white">Charges & Security ({profile.charges?.total_count || 0})</span>
                                                    </div>
                                                    {sections.has('charges') ? <ChevronUp className="h-5 w-5 text-sapphire-400" /> : <ChevronDown className="h-5 w-5 text-sapphire-400" />}
                                                </button>
                                                {sections.has('charges') && (
                                                    <div className="px-4 pb-4">
                                                        {(profile.charges?.items?.length || 0) > 0 ? (
                                                            <div className="space-y-3">
                                                                {profile.charges.items.map((charge, i) => (
                                                                    <div key={i} className={`p-3 rounded-lg ${charge.is_outstanding ? 'bg-red-500/10 border border-red-500/30' : 'bg-sapphire-800/30'}`}>
                                                                        <div className="flex justify-between">
                                                                            <p className="font-medium text-white">{charge.status}</p>
                                                                            <span className={`text-xs px-2 py-0.5 rounded ${charge.is_outstanding ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'}`}>
                                                                                {charge.is_outstanding ? 'Outstanding' : 'Satisfied'}
                                                                            </span>
                                                                        </div>
                                                                        {charge.created_on && <p className="text-sm text-sapphire-400">Created: {charge.created_on}</p>}
                                                                        {charge.persons_entitled?.length > 0 && (
                                                                            <p className="text-xs text-sapphire-500">Entitled: {charge.persons_entitled.join(', ')}</p>
                                                                        )}
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        ) : (
                                                            <p className="text-green-400 text-sm">✅ No charges registered</p>
                                                        )}
                                                    </div>
                                                )}
                                            </div>

                                            {/* Filings */}
                                            <div>
                                                <button
                                                    onClick={() => toggleSection(companyNum, 'filings')}
                                                    className="w-full flex items-center justify-between p-4 hover:bg-sapphire-800/30 transition-colors"
                                                >
                                                    <div className="flex items-center gap-3">
                                                        <FileCheck className="h-5 w-5 text-cyan-400" />
                                                        <span className="font-medium text-white">Filing History</span>
                                                        {profile.filings?.analysis?.has_share_allotments && (
                                                            <span className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded">Share allotments found</span>
                                                        )}
                                                    </div>
                                                    {sections.has('filings') ? <ChevronUp className="h-5 w-5 text-sapphire-400" /> : <ChevronDown className="h-5 w-5 text-sapphire-400" />}
                                                </button>
                                                {sections.has('filings') && (
                                                    <div className="px-4 pb-4">
                                                        <div className="grid grid-cols-3 gap-3 mb-4">
                                                            <div className="p-2 bg-sapphire-800/30 rounded text-center">
                                                                <p className="text-xs text-sapphire-400">Total Filings</p>
                                                                <p className="text-lg font-bold text-white">{profile.filings?.analysis?.total_filings || 0}</p>
                                                            </div>
                                                            <div className="p-2 bg-sapphire-800/30 rounded text-center">
                                                                <p className="text-xs text-sapphire-400">Accounts Type</p>
                                                                <p className="text-lg font-bold text-white">{profile.filings?.analysis?.accounts_type || 'Unknown'}</p>
                                                            </div>
                                                            <div className="p-2 bg-sapphire-800/30 rounded text-center">
                                                                <p className="text-xs text-sapphire-400">Share Allotments</p>
                                                                <p className="text-lg font-bold text-white">{profile.filings?.analysis?.share_allotment_count || 0}</p>
                                                            </div>
                                                        </div>
                                                        <div className="space-y-2 max-h-60 overflow-y-auto">
                                                            {profile.filings?.items?.slice(0, 10).map((filing, i) => (
                                                                <div key={i} className="flex items-center justify-between p-2 bg-sapphire-800/20 rounded">
                                                                    <div>
                                                                        <p className="text-sm text-white">{filing.description}</p>
                                                                        <p className="text-xs text-sapphire-500">{filing.type} • {filing.category}</p>
                                                                    </div>
                                                                    <span className="text-xs text-sapphire-400">{filing.date}</span>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </SurfaceCard>
                                );
                            })}
                        </div>
                    </div>
                )}

                {/* Empty State */}
                {!searchResults.length && !selectedCompanies.length && (
                    <div className="text-center py-16">
                        <Building2 className="h-16 w-16 text-sapphire-600 mx-auto mb-4" />
                        <h3 className="text-xl font-medium text-white mb-2">Start Your EIS Fact-Finding</h3>
                        <p className="text-sapphire-400 mb-4">Search for companies to load comprehensive data from Companies House</p>
                        <div className="flex flex-wrap justify-center gap-3 text-sm text-sapphire-500">
                            <span className="px-3 py-1 bg-sapphire-800/30 rounded">✓ Company Profile</span>
                            <span className="px-3 py-1 bg-sapphire-800/30 rounded">✓ Directors & Officers</span>
                            <span className="px-3 py-1 bg-sapphire-800/30 rounded">✓ Shareholders (PSCs)</span>
                            <span className="px-3 py-1 bg-sapphire-800/30 rounded">✓ Charges & Security</span>
                            <span className="px-3 py-1 bg-sapphire-800/30 rounded">✓ Filing History</span>
                            <span className="px-3 py-1 bg-sapphire-800/30 rounded">✓ EIS Assessment</span>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}
