'use client';

/**
 * EIS Companies Dashboard
 * Monitors Enterprise Investment Scheme companies for Sapphire Capital Partners
 * Stage 1 deliverable for KTP project
 * 
 * Features:
 * - Initial display of top companies by sector
 * - Live search from Companies House API
 * - Company details with directors, SIC codes, risk flags
 * - Newsletter download
 */

import React, { useState, useEffect, useCallback } from 'react';
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
    PieChart,
    RefreshCw,
    Database,
    X,
    ChevronDown,
    ChevronUp
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
const sicToSector: Record<string, string> = {
    '62': 'Technology', '63': 'Technology', '72': 'R&D',
    '58': 'Media', '61': 'Telecoms', '64': 'Finance',
    '65': 'Finance', '66': 'Finance', '85': 'Education',
    '86': 'Healthcare', '21': 'Pharma', '35': 'Energy',
    '01': 'Agriculture', '10': 'Food', '41': 'Construction',
};

function getSectorFromSIC(sicCodes: string[] | undefined): string {
    if (!sicCodes?.length) return 'Other';
    return sicToSector[sicCodes[0]?.substring(0, 2)] || 'Other';
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

    // Load initial sector data
    useEffect(() => {
        const fetchInitialData = async () => {
            try {
                // Check API health
                const healthRes = await fetch(`${API_BASE}/api/eis/health`);
                if (healthRes.ok) {
                    const healthData = await healthRes.json();
                    setApiConfigured(healthData.companies_house_configured);
                }

                // Fetch sector companies
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

    // Handle Enter key
    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') handleSearch();
    };

    // Clear search
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
        setIsGeneratingNewsletter(true);
        try {
            let response;

            if (selectedCompanies.length > 0) {
                // Use POST with selected company data for real newsletter
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

                response = await fetch(`${API_BASE}/api/eis/newsletter`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(companies)
                });
            } else {
                // Fallback to sample data
                response = await fetch(`${API_BASE}/api/eis/newsletter`);
            }

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
            alert(err.message || 'Failed to generate newsletter. Please select companies first.');
        } finally {
            setIsGeneratingNewsletter(false);
        }
    };

    // Toggle sector
    const toggleSector = (sector: string) => {
        setExpandedSectors(prev => {
            const next = new Set(prev);
            if (next.has(sector)) next.delete(sector);
            else next.add(sector);
            return next;
        });
    };

    // Status badge
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

    // Calculate summary stats
    const totalSectorCompanies = Object.values(sectorData).reduce((sum, arr) => sum + arr.length, 0);
    const sectorCount = Object.keys(sectorData).length;

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
                            Browse companies by sector or search the Companies House registry
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
                            disabled={isGeneratingNewsletter}
                            className="flex items-center gap-2 px-5 py-2.5 rounded-xl accent-bg text-white font-medium
                                       hover:opacity-90 transition-all duration-200 disabled:opacity-50"
                        >
                            {isGeneratingNewsletter ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
                            <span>Download Newsletter</span>
                            <Download className="h-4 w-4" />
                        </button>
                    </div>
                </div>

                {/* KPI Summary */}
                {!searchResults.length && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                        <SurfaceCard className="p-4">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg accent-bg-subtle"><Building2 className="h-5 w-5 accent-text-light" /></div>
                                <div>
                                    <p className="text-xs text-sapphire-400">Companies Loaded</p>
                                    <p className="text-2xl font-bold text-white">{totalSectorCompanies}</p>
                                </div>
                            </div>
                        </SurfaceCard>
                        <SurfaceCard className="p-4">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-blue-500/20"><PieChart className="h-5 w-5 text-blue-400" /></div>
                                <div>
                                    <p className="text-xs text-sapphire-400">Sectors</p>
                                    <p className="text-2xl font-bold text-white">{sectorCount}</p>
                                </div>
                            </div>
                        </SurfaceCard>
                        <SurfaceCard className="p-4">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-green-500/20"><CheckCircle2 className="h-5 w-5 text-green-400" /></div>
                                <div>
                                    <p className="text-xs text-sapphire-400">Selected</p>
                                    <p className="text-2xl font-bold text-white">{selectedCompanies.length}</p>
                                </div>
                            </div>
                        </SurfaceCard>
                        <SurfaceCard className="p-4">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-purple-500/20"><TrendingUp className="h-5 w-5 text-purple-400" /></div>
                                <div>
                                    <p className="text-xs text-sapphire-400">Data Source</p>
                                    <p className="text-lg font-bold text-white">Companies House</p>
                                </div>
                            </div>
                        </SurfaceCard>
                    </div>
                )}

                {/* Error Banner */}
                {error && (
                    <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 flex items-center gap-3">
                        <AlertTriangle className="h-5 w-5 flex-shrink-0" />
                        <span>{error}</span>
                        <button onClick={() => setError(null)} className="ml-auto"><X className="h-4 w-4" /></button>
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
                </SurfaceCard>

                {/* Search Results (replaces sector view when searching) */}
                {searchResults.length > 0 && (
                    <div className="mb-8">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-semibold text-white">
                                Results for "{lastSearchQuery}" ({searchResults.length})
                            </h2>
                            <button onClick={clearSearch} className="text-sm text-sapphire-400 hover:text-white flex items-center gap-1">
                                <X className="h-4 w-4" /> Clear search
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
                                            disabled={loadingDetails.has(company.company_number)}
                                            className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-sapphire-700/50 
                                                       text-sm text-white hover:bg-sapphire-600/50 disabled:opacity-50"
                                        >
                                            {loadingDetails.has(company.company_number) ? (
                                                <Loader2 className="h-3 w-3 animate-spin" />
                                            ) : (
                                                <ExternalLink className="h-3 w-3" />
                                            )}
                                            Details
                                        </button>
                                    </div>
                                </SurfaceCard>
                            ))}
                        </div>
                    </div>
                )}

                {/* Initial Sector Companies (hidden when searching) */}
                {!searchResults.length && Object.keys(sectorData).length > 0 && (
                    <div className="mb-8">
                        <h2 className="text-lg font-semibold text-white mb-4">Browse by Sector</h2>

                        <div className="space-y-4">
                            {Object.entries(sectorData).map(([sector, companies]) => (
                                <SurfaceCard key={sector} className="overflow-hidden">
                                    {/* Sector Header */}
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
                                        {expandedSectors.has(sector) ? (
                                            <ChevronUp className="h-5 w-5 text-sapphire-400" />
                                        ) : (
                                            <ChevronDown className="h-5 w-5 text-sapphire-400" />
                                        )}
                                    </button>

                                    {/* Sector Companies */}
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
                                                            View Details
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
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-semibold text-white">Company Details ({selectedCompanies.length})</h2>
                            <button onClick={() => setSelectedCompanies([])} className="text-sm text-sapphire-400 hover:text-white">Clear all</button>
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            {selectedCompanies.map((details) => (
                                <SurfaceCard key={details.company.company_number} className="p-6">
                                    <div className="flex items-start justify-between mb-4">
                                        <div>
                                            <h3 className="text-xl font-bold text-white">{details.company.company_name}</h3>
                                            <p className="text-sm text-sapphire-400">#{details.company.company_number} • {details.company.company_type}</p>
                                        </div>
                                        {getStatusBadge(details.company.company_status)}
                                    </div>

                                    <div className="grid grid-cols-3 gap-3 mb-4">
                                        <div className="text-center p-3 rounded-lg bg-sapphire-800/30">
                                            <p className="text-xs text-sapphire-400">Sector</p>
                                            <p className="text-sm font-semibold text-white">{getSectorFromSIC(details.company.sic_codes)}</p>
                                        </div>
                                        <div className="text-center p-3 rounded-lg bg-sapphire-800/30">
                                            <p className="text-xs text-sapphire-400">Directors</p>
                                            <p className="text-sm font-semibold text-white">{details.director_count}</p>
                                        </div>
                                        <div className="text-center p-3 rounded-lg bg-sapphire-800/30">
                                            <p className="text-xs text-sapphire-400">Founded</p>
                                            <p className="text-sm font-semibold text-white">{details.company.date_of_creation || 'N/A'}</p>
                                        </div>
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
                            ))}
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
