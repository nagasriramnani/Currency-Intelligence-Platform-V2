'use client';

/**
 * EIS Companies Dashboard
 * Monitors Enterprise Investment Scheme companies for Sapphire Capital Partners
 * Stage 1 deliverable for KTP project
 * 
 * Features:
 * - Initial display of top companies by sector
 * - Live search from Companies House API
 * - Dynamic dashboard that updates with selected companies
 * - Company details with directors, SIC codes, risk flags
 * - Newsletter download with selected companies
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
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
    Users,
    MapPin,
    Loader2,
    ExternalLink,
    BarChart3,
    PieChart,
    Database,
    X,
    ChevronDown,
    ChevronUp,
    Shield,
    AlertCircle,
    Info
} from 'lucide-react';

// Types for Companies House API response
interface CompanySearchResult {
    company_number: string;
    title: string;
    company_status: string;
    company_type: string;
    date_of_creation?: string;
    address_snippet?: string;
    description?: string;
}

interface CompanyDetails {
    company: {
        company_number: string;
        company_name: string;
        company_status: string;
        company_type: string;
        date_of_creation?: string;
        jurisdiction: string;
        registered_office_address: {
            address_line_1?: string;
            locality?: string;
            postal_code?: string;
            country?: string;
        };
        sic_codes: string[];
        has_charges: boolean;
        has_insolvency_history: boolean;
    };
    directors: Array<{
        name: string;
        officer_role: string;
        appointed_on?: string;
        nationality?: string;
        occupation?: string;
    }>;
    recent_filings: any[];
    director_count: number;
    total_officers: number;
}

interface SectorData {
    [sector: string]: CompanySearchResult[];
}

// API URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// SIC code to sector mapping
const SIC_TO_SECTOR: Record<string, string> = {
    '62': 'Technology', '63': 'Technology', '72': 'R&D',
    '58': 'Media', '61': 'Telecoms', '64': 'Finance',
    '65': 'Finance', '66': 'Finance', '85': 'Education',
    '86': 'Healthcare', '21': 'Pharma', '35': 'Energy',
    '01': 'Agriculture', '10': 'Food', '41': 'Construction',
    '70': 'Real Estate', '71': 'Engineering', '47': 'Retail',
};

function getSectorFromSIC(sicCodes: string[] | undefined): string {
    if (!sicCodes?.length) return 'Other';
    const firstTwo = sicCodes[0]?.substring(0, 2) || '';
    return SIC_TO_SECTOR[firstTwo] || 'Other';
}

function getCompanyAge(dateOfCreation: string | undefined): number {
    if (!dateOfCreation) return 0;
    try {
        const created = new Date(dateOfCreation);
        const now = new Date();
        return Math.floor((now.getTime() - created.getTime()) / (365.25 * 24 * 60 * 60 * 1000));
    } catch {
        return 0;
    }
}

function getRiskLevel(company: CompanyDetails['company']): { level: string; color: string; score: number } {
    if (company.has_insolvency_history) return { level: 'High', color: 'red', score: 8 };
    if (company.has_charges) return { level: 'Medium', color: 'yellow', score: 5 };
    if (company.company_status !== 'active') return { level: 'High', color: 'red', score: 7 };
    const age = getCompanyAge(company.date_of_creation);
    if (age < 2) return { level: 'High', color: 'red', score: 6 };
    if (age < 5) return { level: 'Medium', color: 'yellow', score: 4 };
    return { level: 'Low', color: 'green', score: 2 };
}

function getEISEligibility(company: CompanyDetails['company']): { status: string; color: string } {
    const age = getCompanyAge(company.date_of_creation);
    if (company.company_status !== 'active') return { status: 'Ineligible', color: 'red' };
    if (age > 7) return { status: 'Review Required', color: 'yellow' };
    if (company.has_insolvency_history) return { status: 'Ineligible', color: 'red' };
    return { status: 'Potentially Eligible', color: 'green' };
}

export default function EISPage() {
    const [isLoading, setIsLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<CompanySearchResult[]>([]);
    const [sectorData, setSectorData] = useState<SectorData>({});
    const [selectedCompanies, setSelectedCompanies] = useState<CompanyDetails[]>([]);
    const [isSearching, setIsSearching] = useState(false);
    const [isGeneratingNewsletter, setIsGeneratingNewsletter] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [apiConfigured, setApiConfigured] = useState(true);
    const [lastSearchQuery, setLastSearchQuery] = useState('');
    const [expandedSectors, setExpandedSectors] = useState<Set<string>>(new Set(['Technology', 'Fintech']));
    const [loadingDetails, setLoadingDetails] = useState<Set<string>>(new Set());

    // Calculate portfolio analytics from selected companies
    const portfolioStats = useMemo(() => {
        if (selectedCompanies.length === 0) return null;

        const companies = selectedCompanies.map(c => c.company);

        // Sector breakdown
        const sectorCounts: Record<string, number> = {};
        companies.forEach(c => {
            const sector = getSectorFromSIC(c.sic_codes);
            sectorCounts[sector] = (sectorCounts[sector] || 0) + 1;
        });

        // Risk breakdown
        const riskCounts = { Low: 0, Medium: 0, High: 0 };
        companies.forEach(c => {
            const risk = getRiskLevel(c);
            riskCounts[risk.level as keyof typeof riskCounts]++;
        });

        // EIS eligibility
        const eligibility = { eligible: 0, review: 0, ineligible: 0 };
        companies.forEach(c => {
            const eis = getEISEligibility(c);
            if (eis.status === 'Potentially Eligible') eligibility.eligible++;
            else if (eis.status === 'Review Required') eligibility.review++;
            else eligibility.ineligible++;
        });

        // Status breakdown
        const statusCounts = { active: 0, dissolved: 0, other: 0 };
        companies.forEach(c => {
            if (c.company_status === 'active') statusCounts.active++;
            else if (c.company_status === 'dissolved') statusCounts.dissolved++;
            else statusCounts.other++;
        });

        // Average age
        const ages = companies.map(c => getCompanyAge(c.date_of_creation));
        const avgAge = ages.reduce((a, b) => a + b, 0) / ages.length;

        // Total directors
        const totalDirectors = selectedCompanies.reduce((sum, c) => sum + c.director_count, 0);

        return {
            total: companies.length,
            sectors: sectorCounts,
            sectorCount: Object.keys(sectorCounts).length,
            risk: riskCounts,
            eligibility,
            status: statusCounts,
            avgAge: avgAge.toFixed(1),
            totalDirectors,
            hasFlags: companies.some(c => c.has_charges || c.has_insolvency_history)
        };
    }, [selectedCompanies]);

    // Load initial sector data
    useEffect(() => {
        const fetchInitialData = async () => {
            try {
                const healthRes = await fetch(`${API_BASE}/api/eis/health`);
                if (healthRes.ok) {
                    const healthData = await healthRes.json();
                    setApiConfigured(healthData.companies_house_configured);
                }

                const sectorsRes = await fetch(`${API_BASE}/api/eis/sectors`);
                if (sectorsRes.ok) {
                    const data = await sectorsRes.json();
                    setSectorData(data.sectors || {});
                    if (!data.api_configured) {
                        setError('Companies House API not configured. Add COMPANIES_HOUSE_API_KEY to .env');
                    }
                }
            } catch (err) {
                console.error('Failed to fetch initial data:', err);
                setError('Failed to connect to backend. Please ensure the server is running.');
            } finally {
                setTimeout(() => setIsLoading(false), 1500);
            }
        };
        fetchInitialData();
    }, []);

    // Search companies
    const handleSearch = useCallback(async () => {
        if (!searchQuery.trim() || searchQuery.length < 2) {
            setError('Please enter at least 2 characters to search');
            return;
        }

        setIsSearching(true);
        setError(null);
        setLastSearchQuery(searchQuery);

        try {
            const res = await fetch(`${API_BASE}/api/eis/search?query=${encodeURIComponent(searchQuery)}&limit=30`);

            if (!res.ok) {
                const errorData = await res.json();
                throw new Error(errorData.detail || 'Search failed');
            }

            const data = await res.json();
            setSearchResults(data.results || []);

            if (data.results.length === 0) {
                setError(`No companies found for "${searchQuery}"`);
            }
        } catch (err: any) {
            console.error('Search failed:', err);
            setError(err.message || 'Search failed');
            setSearchResults([]);
        } finally {
            setIsSearching(false);
        }
    }, [searchQuery]);

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') handleSearch();
    };

    const clearSearch = () => {
        setSearchQuery('');
        setSearchResults([]);
        setLastSearchQuery('');
        setError(null);
    };

    // Load company details
    const loadCompanyDetails = async (companyNumber: string) => {
        setLoadingDetails(prev => new Set(prev).add(companyNumber));
        try {
            const res = await fetch(`${API_BASE}/api/eis/company/${companyNumber}`);
            if (res.ok) {
                const details: CompanyDetails = await res.json();
                setSelectedCompanies(prev => {
                    const exists = prev.some(c => c.company.company_number === companyNumber);
                    if (exists) return prev;
                    return [...prev, details];
                });
            }
        } catch (err) {
            console.error('Failed to load company details:', err);
        } finally {
            setLoadingDetails(prev => {
                const next = new Set(prev);
                next.delete(companyNumber);
                return next;
            });
        }
    };

    // Download newsletter with selected company data
    const handleDownloadNewsletter = async () => {
        if (selectedCompanies.length === 0) {
            alert('Please select at least one company by clicking "Details" on a company card.');
            return;
        }

        setIsGeneratingNewsletter(true);
        try {
            const companies = selectedCompanies.map(details => ({
                company_number: details.company.company_number,
                company_name: details.company.company_name,
                company_status: details.company.company_status,
                company_type: details.company.company_type,
                date_of_creation: details.company.date_of_creation,
                jurisdiction: details.company.jurisdiction,
                registered_office_address: details.company.registered_office_address,
                sic_codes: details.company.sic_codes,
                has_charges: details.company.has_charges,
                has_insolvency_history: details.company.has_insolvency_history,
                directors: details.directors
            }));

            const response = await fetch(`${API_BASE}/api/eis/newsletter`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(companies)
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Newsletter generation failed');
            }

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
            console.error('Newsletter download failed:', err);
            alert(err.message || 'Failed to generate newsletter.');
        } finally {
            setIsGeneratingNewsletter(false);
        }
    };

    const toggleSector = (sector: string) => {
        setExpandedSectors(prev => {
            const next = new Set(prev);
            if (next.has(sector)) next.delete(sector);
            else next.add(sector);
            return next;
        });
    };

    const removeCompany = (companyNumber: string) => {
        setSelectedCompanies(prev => prev.filter(c => c.company.company_number !== companyNumber));
    };

    const getStatusBadge = (status: string) => {
        const isActive = status === 'active';
        return (
            <span className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-xs ${isActive ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'
                }`}>
                {isActive ? <CheckCircle2 className="h-3 w-3" /> : <Clock className="h-3 w-3" />}
                {status === 'active' ? 'Active' : status}
            </span>
        );
    };

    const totalSectorCompanies = Object.values(sectorData).reduce((sum, arr) => sum + arr.length, 0);

    if (isLoading) {
        return <CampingLoader />;
    }

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
                        <Link href="/risk" className="px-3 py-2 text-sm text-sapphire-200 hover:text-white rounded-lg hover:bg-sapphire-800/30">Risk</Link>
                        <Link href="/eis" className="px-3 py-2 text-sm text-white bg-sapphire-800/50 rounded-lg ring-1 ring-sapphire-700/50">EIS</Link>
                        <Link href="/settings" className="px-3 py-2 text-sm text-sapphire-200 hover:text-white rounded-lg hover:bg-sapphire-800/30">Settings</Link>
                    </nav>
                </div>
            </header>

            <main className="container mx-auto px-4 py-8 max-w-7xl">
                {/* Page Header */}
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-white">
                            EIS <span className="accent-text-light">Companies</span>
                        </h1>
                        <p className="text-sapphire-300 mt-1">
                            Browse, select companies, and generate portfolio reports
                        </p>
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
                            <span>Download Report ({selectedCompanies.length})</span>
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

                {/* Dynamic Portfolio Dashboard - Shows when companies are selected */}
                {portfolioStats && (
                    <div className="mb-8 animate-fade-in">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                                <PieChart className="h-5 w-5 accent-text-light" />
                                Portfolio Analysis ({portfolioStats.total} Companies Selected)
                            </h2>
                            <button
                                onClick={() => setSelectedCompanies([])}
                                className="text-sm text-sapphire-400 hover:text-white"
                            >
                                Clear All
                            </button>
                        </div>

                        {/* KPI Row */}
                        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-6">
                            <SurfaceCard className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg accent-bg-subtle"><Building2 className="h-5 w-5 accent-text-light" /></div>
                                    <div>
                                        <p className="text-xs text-sapphire-400">Companies</p>
                                        <p className="text-2xl font-bold text-white">{portfolioStats.total}</p>
                                    </div>
                                </div>
                            </SurfaceCard>
                            <SurfaceCard className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-green-500/20"><CheckCircle2 className="h-5 w-5 text-green-400" /></div>
                                    <div>
                                        <p className="text-xs text-sapphire-400">EIS Eligible</p>
                                        <p className="text-2xl font-bold text-green-400">{portfolioStats.eligibility.eligible}</p>
                                    </div>
                                </div>
                            </SurfaceCard>
                            <SurfaceCard className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-blue-500/20"><TrendingUp className="h-5 w-5 text-blue-400" /></div>
                                    <div>
                                        <p className="text-xs text-sapphire-400">Sectors</p>
                                        <p className="text-2xl font-bold text-white">{portfolioStats.sectorCount}</p>
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
                                    <div className="p-2 rounded-lg bg-cyan-500/20"><Clock className="h-5 w-5 text-cyan-400" /></div>
                                    <div>
                                        <p className="text-xs text-sapphire-400">Avg Age</p>
                                        <p className="text-2xl font-bold text-white">{portfolioStats.avgAge}y</p>
                                    </div>
                                </div>
                            </SurfaceCard>
                            <SurfaceCard className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className={`p-2 rounded-lg ${portfolioStats.hasFlags ? 'bg-red-500/20' : 'bg-green-500/20'}`}>
                                        <Shield className={`h-5 w-5 ${portfolioStats.hasFlags ? 'text-red-400' : 'text-green-400'}`} />
                                    </div>
                                    <div>
                                        <p className="text-xs text-sapphire-400">Active</p>
                                        <p className="text-2xl font-bold text-white">{portfolioStats.status.active}</p>
                                    </div>
                                </div>
                            </SurfaceCard>
                        </div>

                        {/* Charts Row */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* Sector Breakdown */}
                            <SurfaceCard className="p-5">
                                <div className="flex items-center gap-2 mb-4">
                                    <PieChart className="h-5 w-5 accent-text-light" />
                                    <h3 className="font-semibold text-white">Sector Breakdown</h3>
                                </div>
                                <div className="space-y-3">
                                    {Object.entries(portfolioStats.sectors).map(([sector, count]) => (
                                        <div key={sector} className="flex items-center justify-between">
                                            <span className="text-sapphire-300">{sector}</span>
                                            <div className="flex items-center gap-3">
                                                <div className="w-24 h-2 bg-sapphire-800 rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full accent-bg rounded-full transition-all duration-500"
                                                        style={{ width: `${(count / portfolioStats.total) * 100}%` }}
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
                                    {(['Low', 'Medium', 'High'] as const).map((risk) => {
                                        const count = portfolioStats.risk[risk];
                                        const percentage = (count / portfolioStats.total) * 100;
                                        const colors = { Low: 'bg-green-500', Medium: 'bg-yellow-500', High: 'bg-red-500' };
                                        return (
                                            <div key={risk} className="flex-1 flex flex-col items-center justify-end">
                                                <span className="text-lg font-bold text-white mb-2">{count}</span>
                                                <div
                                                    className={`w-full ${colors[risk]} rounded-t-lg transition-all duration-500`}
                                                    style={{ height: `${Math.max(percentage, 10)}%` }}
                                                />
                                                <span className="text-xs text-sapphire-400 mt-2">{risk}</span>
                                            </div>
                                        );
                                    })}
                                </div>
                            </SurfaceCard>
                        </div>

                        {/* Info Note */}
                        <div className="mt-4 p-3 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-300 text-sm flex items-start gap-2">
                            <Info className="h-4 w-4 mt-0.5 flex-shrink-0" />
                            <span>
                                <strong>Data Source:</strong> UK Companies House Registry. Risk levels are calculated based on company status,
                                age, insolvency history, and outstanding charges. EIS eligibility is estimated based on age (&lt;7 years) and status.
                            </span>
                        </div>
                    </div>
                )}

                {/* Search Section */}
                <SurfaceCard className="p-6 mb-8">
                    <div className="flex gap-3">
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-sapphire-400" />
                            <input
                                type="text"
                                placeholder="Search company name, number, or sector..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                onKeyPress={handleKeyPress}
                                className="w-full pl-10 pr-4 py-3 rounded-xl bg-sapphire-800/50 border border-sapphire-700/50
                                           text-white placeholder-sapphire-400 focus:outline-none focus:ring-2 focus:ring-sapphire-500/50 text-lg"
                            />
                            {searchQuery && (
                                <button onClick={clearSearch} className="absolute right-3 top-1/2 -translate-y-1/2">
                                    <X className="h-4 w-4 text-sapphire-400 hover:text-white" />
                                </button>
                            )}
                        </div>
                        <button
                            onClick={handleSearch}
                            disabled={isSearching || !apiConfigured}
                            className="flex items-center gap-2 px-6 py-3 rounded-xl bg-sapphire-600 text-white font-medium
                                       hover:bg-sapphire-500 transition-all disabled:opacity-50"
                        >
                            {isSearching ? <Loader2 className="h-5 w-5 animate-spin" /> : <Search className="h-5 w-5" />}
                            <span>Search</span>
                        </button>
                    </div>
                    <p className="text-sm text-sapphire-500 mt-2">
                        💡 Click "Details" on any company to add it to your portfolio analysis
                    </p>
                </SurfaceCard>

                {/* Search Results */}
                {searchResults.length > 0 && (
                    <div className="mb-8">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-semibold text-white">Results for "{lastSearchQuery}" ({searchResults.length})</h2>
                            <button onClick={clearSearch} className="text-sm text-sapphire-400 hover:text-white flex items-center gap-1">
                                <X className="h-4 w-4" /> Clear
                            </button>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {searchResults.map((company) => (
                                <SurfaceCard key={company.company_number} className="p-4 hover:border-sapphire-600/50 transition-all">
                                    <div className="flex items-start justify-between mb-2">
                                        <div className="flex-1 min-w-0">
                                            <h3 className="font-semibold text-white truncate">{company.title}</h3>
                                            <p className="text-xs text-sapphire-400">#{company.company_number}</p>
                                        </div>
                                        {getStatusBadge(company.company_status)}
                                    </div>
                                    {company.address_snippet && (
                                        <p className="text-sm text-sapphire-300 mb-3 line-clamp-1">
                                            <MapPin className="h-3 w-3 inline mr-1" />{company.address_snippet}
                                        </p>
                                    )}
                                    <div className="flex items-center justify-between">
                                        <span className="text-xs text-sapphire-500">{company.company_type}</span>
                                        <button
                                            onClick={() => loadCompanyDetails(company.company_number)}
                                            disabled={loadingDetails.has(company.company_number) || selectedCompanies.some(c => c.company.company_number === company.company_number)}
                                            className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm transition-colors
                                                ${selectedCompanies.some(c => c.company.company_number === company.company_number)
                                                    ? 'bg-green-500/20 text-green-400'
                                                    : 'bg-sapphire-700/50 text-white hover:bg-sapphire-600/50'}`}
                                        >
                                            {loadingDetails.has(company.company_number) ? (
                                                <Loader2 className="h-3 w-3 animate-spin" />
                                            ) : selectedCompanies.some(c => c.company.company_number === company.company_number) ? (
                                                <CheckCircle2 className="h-3 w-3" />
                                            ) : (
                                                <ExternalLink className="h-3 w-3" />
                                            )}
                                            {selectedCompanies.some(c => c.company.company_number === company.company_number) ? 'Added' : 'Details'}
                                        </button>
                                    </div>
                                </SurfaceCard>
                            ))}
                        </div>
                    </div>
                )}

                {/* Initial Sector Companies (hidden when searching) */}
                {!searchResults.length && Object.keys(sectorData).length > 0 && !portfolioStats && (
                    <div className="mb-8">
                        {/* Initial KPI cards when no companies selected */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                            <SurfaceCard className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg accent-bg-subtle"><Building2 className="h-5 w-5 accent-text-light" /></div>
                                    <div>
                                        <p className="text-xs text-sapphire-400">Companies Available</p>
                                        <p className="text-2xl font-bold text-white">{totalSectorCompanies}</p>
                                    </div>
                                </div>
                            </SurfaceCard>
                            <SurfaceCard className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-blue-500/20"><PieChart className="h-5 w-5 text-blue-400" /></div>
                                    <div>
                                        <p className="text-xs text-sapphire-400">Sectors</p>
                                        <p className="text-2xl font-bold text-white">{Object.keys(sectorData).length}</p>
                                    </div>
                                </div>
                            </SurfaceCard>
                            <SurfaceCard className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-purple-500/20"><CheckCircle2 className="h-5 w-5 text-purple-400" /></div>
                                    <div>
                                        <p className="text-xs text-sapphire-400">Selected</p>
                                        <p className="text-2xl font-bold text-white">0</p>
                                    </div>
                                </div>
                            </SurfaceCard>
                            <SurfaceCard className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-emerald-500/20"><Database className="h-5 w-5 text-emerald-400" /></div>
                                    <div>
                                        <p className="text-xs text-sapphire-400">Data Source</p>
                                        <p className="text-lg font-bold text-white">Companies House</p>
                                    </div>
                                </div>
                            </SurfaceCard>
                        </div>

                        <h2 className="text-lg font-semibold text-white mb-4">Browse by Sector</h2>

                        <div className="space-y-4">
                            {Object.entries(sectorData).map(([sector, companies]) => (
                                <SurfaceCard key={sector} className="overflow-hidden">
                                    <button
                                        onClick={() => toggleSector(sector)}
                                        className="w-full flex items-center justify-between p-4 hover:bg-sapphire-800/30 transition-colors"
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 rounded-lg accent-bg-subtle">
                                                <TrendingUp className="h-5 w-5 accent-text-light" />
                                            </div>
                                            <div className="text-left">
                                                <h3 className="font-semibold text-white">{sector}</h3>
                                                <p className="text-sm text-sapphire-400">{companies.length} companies</p>
                                            </div>
                                        </div>
                                        {expandedSectors.has(sector) ? <ChevronUp className="h-5 w-5 text-sapphire-400" /> : <ChevronDown className="h-5 w-5 text-sapphire-400" />}
                                    </button>

                                    {expandedSectors.has(sector) && (
                                        <div className="border-t border-sapphire-700/30 p-4">
                                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                                                {companies.slice(0, 9).map((company) => (
                                                    <div key={company.company_number} className="p-3 rounded-lg bg-sapphire-800/30 hover:bg-sapphire-800/50 transition-colors">
                                                        <div className="flex items-start justify-between mb-1">
                                                            <h4 className="font-medium text-white text-sm truncate flex-1">{company.title}</h4>
                                                            {getStatusBadge(company.company_status)}
                                                        </div>
                                                        <p className="text-xs text-sapphire-400 mb-2">#{company.company_number}</p>
                                                        <button
                                                            onClick={() => loadCompanyDetails(company.company_number)}
                                                            disabled={loadingDetails.has(company.company_number)}
                                                            className="text-xs text-sapphire-400 hover:text-white flex items-center gap-1"
                                                        >
                                                            {loadingDetails.has(company.company_number) ? (
                                                                <Loader2 className="h-3 w-3 animate-spin" />
                                                            ) : (
                                                                <ExternalLink className="h-3 w-3" />
                                                            )}
                                                            Add to Portfolio
                                                        </button>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </SurfaceCard>
                            ))}
                        </div>
                    </div>
                )}

                {/* Selected Company Details */}
                {selectedCompanies.length > 0 && (
                    <div>
                        <h2 className="text-lg font-semibold text-white mb-4">Selected Companies ({selectedCompanies.length})</h2>

                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            {selectedCompanies.map((details) => {
                                const risk = getRiskLevel(details.company);
                                const eis = getEISEligibility(details.company);
                                const age = getCompanyAge(details.company.date_of_creation);

                                return (
                                    <SurfaceCard key={details.company.company_number} className="p-6 relative">
                                        <button
                                            onClick={() => removeCompany(details.company.company_number)}
                                            className="absolute top-4 right-4 text-sapphire-400 hover:text-white"
                                        >
                                            <X className="h-4 w-4" />
                                        </button>

                                        <div className="flex items-start justify-between mb-4 pr-6">
                                            <div>
                                                <h3 className="text-xl font-bold text-white">{details.company.company_name}</h3>
                                                <p className="text-sm text-sapphire-400">#{details.company.company_number} • {details.company.company_type}</p>
                                            </div>
                                            {getStatusBadge(details.company.company_status)}
                                        </div>

                                        <div className="grid grid-cols-4 gap-3 mb-4">
                                            <div className="text-center p-3 rounded-lg bg-sapphire-800/30">
                                                <p className="text-xs text-sapphire-400">Sector</p>
                                                <p className="text-sm font-semibold text-white">{getSectorFromSIC(details.company.sic_codes)}</p>
                                            </div>
                                            <div className="text-center p-3 rounded-lg bg-sapphire-800/30">
                                                <p className="text-xs text-sapphire-400">Age</p>
                                                <p className="text-sm font-semibold text-white">{age} yrs</p>
                                            </div>
                                            <div className="text-center p-3 rounded-lg bg-sapphire-800/30">
                                                <p className="text-xs text-sapphire-400">Directors</p>
                                                <p className="text-sm font-semibold text-white">{details.director_count}</p>
                                            </div>
                                            <div className={`text-center p-3 rounded-lg ${risk.level === 'Low' ? 'bg-green-500/20' : risk.level === 'High' ? 'bg-red-500/20' : 'bg-yellow-500/20'
                                                }`}>
                                                <p className="text-xs text-sapphire-400">Risk</p>
                                                <p className={`text-sm font-semibold ${risk.level === 'Low' ? 'text-green-400' : risk.level === 'High' ? 'text-red-400' : 'text-yellow-400'
                                                    }`}>{risk.level}</p>
                                            </div>
                                        </div>

                                        {/* EIS Eligibility */}
                                        <div className={`mb-4 p-3 rounded-lg ${eis.status === 'Potentially Eligible' ? 'bg-green-500/10 border border-green-500/30' :
                                                eis.status === 'Ineligible' ? 'bg-red-500/10 border border-red-500/30' :
                                                    'bg-yellow-500/10 border border-yellow-500/30'
                                            }`}>
                                            <p className={`text-sm font-medium ${eis.status === 'Potentially Eligible' ? 'text-green-400' :
                                                    eis.status === 'Ineligible' ? 'text-red-400' : 'text-yellow-400'
                                                }`}>
                                                EIS Status: {eis.status}
                                            </p>
                                        </div>

                                        {details.company.registered_office_address && (
                                            <div className="mb-4">
                                                <p className="text-xs text-sapphire-400 mb-1"><MapPin className="h-3 w-3 inline mr-1" />Registered Office</p>
                                                <p className="text-sm text-sapphire-200">
                                                    {details.company.registered_office_address.address_line_1}
                                                    {details.company.registered_office_address.locality && `, ${details.company.registered_office_address.locality}`}
                                                    {details.company.registered_office_address.postal_code && ` ${details.company.registered_office_address.postal_code}`}
                                                </p>
                                            </div>
                                        )}

                                        {details.directors?.length > 0 && (
                                            <div className="pt-3 border-t border-sapphire-700/30">
                                                <p className="text-xs text-sapphire-400 mb-2"><Users className="h-3 w-3 inline mr-1" />Directors</p>
                                                {details.directors.slice(0, 3).map((d, i) => (
                                                    <p key={i} className="text-sm text-sapphire-200">{d.name} <span className="text-sapphire-500">({d.officer_role})</span></p>
                                                ))}
                                            </div>
                                        )}

                                        <div className="mt-3 flex gap-2 flex-wrap">
                                            {details.company.has_insolvency_history && (
                                                <span className="px-2 py-1 rounded bg-red-500/20 text-red-400 text-xs">⚠️ Insolvency</span>
                                            )}
                                            {details.company.has_charges && (
                                                <span className="px-2 py-1 rounded bg-yellow-500/20 text-yellow-400 text-xs">📋 Charges</span>
                                            )}
                                            {!details.company.has_insolvency_history && !details.company.has_charges && (
                                                <span className="px-2 py-1 rounded bg-green-500/20 text-green-400 text-xs">✅ No Flags</span>
                                            )}
                                            {details.company.sic_codes?.length > 0 && (
                                                <span className="px-2 py-1 rounded bg-sapphire-700/50 text-sapphire-300 text-xs">
                                                    SIC: {details.company.sic_codes.join(', ')}
                                                </span>
                                            )}
                                        </div>
                                    </SurfaceCard>
                                );
                            })}
                        </div>
                    </div>
                )}

                {/* Empty State */}
                {!searchResults.length && !Object.keys(sectorData).length && !error && (
                    <div className="text-center py-16">
                        <Building2 className="h-16 w-16 text-sapphire-600 mx-auto mb-4" />
                        <h3 className="text-xl font-medium text-white mb-2">Loading Companies...</h3>
                        <p className="text-sapphire-400">Fetching data from Companies House registry</p>
                    </div>
                )}
            </main>
        </div>
    );
}
