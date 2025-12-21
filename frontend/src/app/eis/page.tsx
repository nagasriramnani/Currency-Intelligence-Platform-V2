'use client';

/**
 * EIS Companies Dashboard
 * Monitors Enterprise Investment Scheme companies for Sapphire Capital Partners
 * Stage 1 deliverable for KTP project
 * 
 * NOW USES LIVE COMPANIES HOUSE API DATA
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
    Database
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

// API URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// SIC code to sector mapping (common business categories)
const sicToSector: Record<string, string> = {
    '62': 'Technology',
    '63': 'Technology',
    '72': 'Research & Development',
    '58': 'Media & Publishing',
    '61': 'Telecommunications',
    '64': 'Financial Services',
    '65': 'Financial Services',
    '66': 'Financial Services',
    '85': 'Education',
    '86': 'Healthcare',
    '21': 'Pharmaceuticals',
    '35': 'Energy',
    '01': 'Agriculture',
    '10': 'Food & Beverages',
    '41': 'Construction',
    '45': 'Automotive',
    '47': 'Retail',
};

function getSectorFromSIC(sicCodes: string[] | undefined): string {
    if (!sicCodes || sicCodes.length === 0) return 'Other';
    const firstTwo = sicCodes[0]?.substring(0, 2) || '';
    return sicToSector[firstTwo] || 'Other';
}

export default function EISPage() {
    const [isLoading, setIsLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<CompanySearchResult[]>([]);
    const [selectedCompanies, setSelectedCompanies] = useState<CompanyDetails[]>([]);
    const [isSearching, setIsSearching] = useState(false);
    const [isGeneratingNewsletter, setIsGeneratingNewsletter] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [apiConfigured, setApiConfigured] = useState(true);
    const [lastSearchQuery, setLastSearchQuery] = useState('');

    // Check API health on mount
    useEffect(() => {
        const checkHealth = async () => {
            try {
                const res = await fetch(`${API_BASE}/api/eis/health`);
                if (res.ok) {
                    const data = await res.json();
                    setApiConfigured(data.companies_house_configured);
                    if (!data.companies_house_configured) {
                        setError('Companies House API key not configured. Add COMPANIES_HOUSE_API_KEY to .env');
                    }
                }
            } catch (err) {
                setError('Failed to connect to backend. Please ensure the server is running.');
            } finally {
                setTimeout(() => setIsLoading(false), 1500);
            }
        };
        checkHealth();
    }, []);

    // Search companies from Companies House API
    const handleSearch = useCallback(async () => {
        if (!searchQuery.trim() || searchQuery.length < 2) {
            setError('Please enter at least 2 characters to search');
            return;
        }

        setIsSearching(true);
        setError(null);
        setLastSearchQuery(searchQuery);

        try {
            const res = await fetch(`${API_BASE}/api/eis/search?query=${encodeURIComponent(searchQuery)}&limit=20`);

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

    // Handle Enter key in search
    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            handleSearch();
        }
    };

    // Load company details
    const loadCompanyDetails = async (companyNumber: string) => {
        try {
            const res = await fetch(`${API_BASE}/api/eis/company/${companyNumber}`);
            if (res.ok) {
                const details: CompanyDetails = await res.json();
                // Add to selected companies if not already there
                setSelectedCompanies(prev => {
                    const exists = prev.some(c => c.company.company_number === companyNumber);
                    if (exists) return prev;
                    return [...prev, details];
                });
            }
        } catch (err) {
            console.error('Failed to load company details:', err);
        }
    };

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
            alert('Failed to generate newsletter');
        } finally {
            setIsGeneratingNewsletter(false);
        }
    };

    // Get status badge
    const getStatusBadge = (status: string) => {
        const isActive = status === 'active';
        return (
            <span className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-xs ${isActive
                    ? 'bg-green-500/20 text-green-400'
                    : 'bg-yellow-500/20 text-yellow-400'
                }`}>
                {isActive ? <CheckCircle2 className="h-3 w-3" /> : <Clock className="h-3 w-3" />}
                {status === 'active' ? 'Active' : status}
            </span>
        );
    };

    if (isLoading) {
        return <CampingLoader />;
    }

    return (
        <div className="min-h-screen bg-sapphire-950 text-white">
            {/* Header */}
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
                            Search Companies House for EIS-eligible companies
                        </p>
                    </div>

                    {/* API Status + Newsletter Button */}
                    <div className="flex items-center gap-3">
                        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm ${apiConfigured
                                ? 'bg-green-500/20 text-green-400'
                                : 'bg-red-500/20 text-red-400'
                            }`}>
                            <Database className="h-4 w-4" />
                            {apiConfigured ? 'API Connected' : 'API Not Configured'}
                        </div>

                        <button
                            onClick={handleDownloadNewsletter}
                            disabled={isGeneratingNewsletter || selectedCompanies.length === 0}
                            className="flex items-center gap-2 px-5 py-2.5 rounded-xl accent-bg text-white font-medium
                                       hover:opacity-90 transition-all duration-200 disabled:opacity-50"
                        >
                            {isGeneratingNewsletter ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                                <FileText className="h-4 w-4" />
                            )}
                            <span>Download Newsletter</span>
                            <Download className="h-4 w-4" />
                        </button>
                    </div>
                </div>

                {/* Error Banner */}
                {error && (
                    <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 flex items-center gap-3">
                        <AlertTriangle className="h-5 w-5 flex-shrink-0" />
                        <span>{error}</span>
                    </div>
                )}

                {/* Search Section */}
                <SurfaceCard className="p-6 mb-8">
                    <div className="flex items-center gap-2 mb-4">
                        <Search className="h-5 w-5 accent-text-light" />
                        <h2 className="font-semibold text-white">Search Companies House</h2>
                    </div>

                    <div className="flex gap-3">
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-sapphire-400" />
                            <input
                                type="text"
                                placeholder="Enter company name, number, or keyword..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                onKeyPress={handleKeyPress}
                                className="w-full pl-10 pr-4 py-3 rounded-xl bg-sapphire-800/50 border border-sapphire-700/50
                                           text-white placeholder-sapphire-400 focus:outline-none focus:ring-2 focus:ring-sapphire-500/50
                                           text-lg"
                            />
                        </div>
                        <button
                            onClick={handleSearch}
                            disabled={isSearching || !apiConfigured}
                            className="flex items-center gap-2 px-6 py-3 rounded-xl bg-sapphire-600 text-white font-medium
                                       hover:bg-sapphire-500 transition-all duration-200 disabled:opacity-50"
                        >
                            {isSearching ? (
                                <Loader2 className="h-5 w-5 animate-spin" />
                            ) : (
                                <Search className="h-5 w-5" />
                            )}
                            <span>Search</span>
                        </button>
                    </div>

                    <p className="text-sm text-sapphire-500 mt-3">
                        💡 Try searching: "tech startup", "fintech", "clean energy", or a specific company number
                    </p>
                </SurfaceCard>

                {/* Search Results */}
                {searchResults.length > 0 && (
                    <div className="mb-8">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-semibold text-white">
                                Search Results for "{lastSearchQuery}"
                            </h2>
                            <span className="text-sm text-sapphire-400">
                                {searchResults.length} companies found
                            </span>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {searchResults.map((company) => (
                                <SurfaceCard
                                    key={company.company_number}
                                    className="p-4 hover:border-sapphire-600/50 transition-all duration-300 cursor-pointer group"
                                >
                                    <div className="flex items-start justify-between mb-2">
                                        <div className="flex-1 min-w-0">
                                            <h3 className="font-semibold text-white truncate group-hover:accent-text-light transition-colors">
                                                {company.title}
                                            </h3>
                                            <p className="text-xs text-sapphire-400">#{company.company_number}</p>
                                        </div>
                                        {getStatusBadge(company.company_status)}
                                    </div>

                                    {company.address_snippet && (
                                        <p className="text-sm text-sapphire-300 mb-3 line-clamp-2">
                                            <MapPin className="h-3 w-3 inline mr-1" />
                                            {company.address_snippet}
                                        </p>
                                    )}

                                    <div className="flex items-center justify-between">
                                        <span className="text-xs text-sapphire-500">
                                            {company.company_type} • Est. {company.date_of_creation || 'N/A'}
                                        </span>
                                        <button
                                            onClick={() => loadCompanyDetails(company.company_number)}
                                            className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-sapphire-700/50 
                                                       text-sm text-white hover:bg-sapphire-600/50 transition-colors"
                                        >
                                            <ExternalLink className="h-3 w-3" />
                                            Details
                                        </button>
                                    </div>
                                </SurfaceCard>
                            ))}
                        </div>
                    </div>
                )}

                {/* Selected Companies (Detailed View) */}
                {selectedCompanies.length > 0 && (
                    <div>
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-semibold text-white">
                                Company Details ({selectedCompanies.length})
                            </h2>
                            <button
                                onClick={() => setSelectedCompanies([])}
                                className="text-sm text-sapphire-400 hover:text-white"
                            >
                                Clear all
                            </button>
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            {selectedCompanies.map((details) => (
                                <SurfaceCard
                                    key={details.company.company_number}
                                    className="p-6"
                                >
                                    {/* Company Header */}
                                    <div className="flex items-start justify-between mb-4">
                                        <div>
                                            <h3 className="text-xl font-bold text-white">
                                                {details.company.company_name}
                                            </h3>
                                            <p className="text-sm text-sapphire-400">
                                                #{details.company.company_number} • {details.company.company_type}
                                            </p>
                                        </div>
                                        {getStatusBadge(details.company.company_status)}
                                    </div>

                                    {/* Key Metrics */}
                                    <div className="grid grid-cols-3 gap-3 mb-4">
                                        <div className="text-center p-3 rounded-lg bg-sapphire-800/30">
                                            <p className="text-xs text-sapphire-400">Sector</p>
                                            <p className="text-sm font-semibold text-white">
                                                {getSectorFromSIC(details.company.sic_codes)}
                                            </p>
                                        </div>
                                        <div className="text-center p-3 rounded-lg bg-sapphire-800/30">
                                            <p className="text-xs text-sapphire-400">Directors</p>
                                            <p className="text-sm font-semibold text-white">
                                                {details.director_count}
                                            </p>
                                        </div>
                                        <div className="text-center p-3 rounded-lg bg-sapphire-800/30">
                                            <p className="text-xs text-sapphire-400">Founded</p>
                                            <p className="text-sm font-semibold text-white">
                                                {details.company.date_of_creation || 'N/A'}
                                            </p>
                                        </div>
                                    </div>

                                    {/* Address */}
                                    {details.company.registered_office_address && (
                                        <div className="mb-4">
                                            <div className="flex items-center gap-2 text-xs text-sapphire-400 mb-1">
                                                <MapPin className="h-3 w-3" />
                                                <span>Registered Office</span>
                                            </div>
                                            <p className="text-sm text-sapphire-200">
                                                {details.company.registered_office_address.address_line_1}
                                                {details.company.registered_office_address.locality &&
                                                    `, ${details.company.registered_office_address.locality}`}
                                                {details.company.registered_office_address.postal_code &&
                                                    ` ${details.company.registered_office_address.postal_code}`}
                                            </p>
                                        </div>
                                    )}

                                    {/* Directors */}
                                    {details.directors && details.directors.length > 0 && (
                                        <div className="pt-3 border-t border-sapphire-700/30">
                                            <div className="flex items-center gap-2 text-xs text-sapphire-400 mb-2">
                                                <Users className="h-3 w-3" />
                                                <span>Directors</span>
                                            </div>
                                            <div className="space-y-1">
                                                {details.directors.slice(0, 3).map((director, i) => (
                                                    <p key={i} className="text-sm text-sapphire-200">
                                                        {director.name}
                                                        <span className="text-sapphire-500 ml-2">
                                                            ({director.officer_role})
                                                        </span>
                                                    </p>
                                                ))}
                                                {details.directors.length > 3 && (
                                                    <p className="text-xs text-sapphire-500">
                                                        +{details.directors.length - 3} more
                                                    </p>
                                                )}
                                            </div>
                                        </div>
                                    )}

                                    {/* SIC Codes */}
                                    {details.company.sic_codes && details.company.sic_codes.length > 0 && (
                                        <div className="mt-3 pt-3 border-t border-sapphire-700/30">
                                            <p className="text-xs text-sapphire-500">
                                                SIC: {details.company.sic_codes.join(', ')}
                                            </p>
                                        </div>
                                    )}

                                    {/* Risk Flags */}
                                    <div className="mt-3 flex gap-2">
                                        {details.company.has_insolvency_history && (
                                            <span className="px-2 py-1 rounded bg-red-500/20 text-red-400 text-xs">
                                                ⚠️ Insolvency History
                                            </span>
                                        )}
                                        {details.company.has_charges && (
                                            <span className="px-2 py-1 rounded bg-yellow-500/20 text-yellow-400 text-xs">
                                                📋 Has Charges
                                            </span>
                                        )}
                                        {!details.company.has_insolvency_history && !details.company.has_charges && (
                                            <span className="px-2 py-1 rounded bg-green-500/20 text-green-400 text-xs">
                                                ✅ No Flags
                                            </span>
                                        )}
                                    </div>
                                </SurfaceCard>
                            ))}
                        </div>
                    </div>
                )}

                {/* Empty State */}
                {searchResults.length === 0 && selectedCompanies.length === 0 && !error && (
                    <div className="text-center py-16">
                        <Building2 className="h-16 w-16 text-sapphire-600 mx-auto mb-4" />
                        <h3 className="text-xl font-medium text-white mb-2">Search for Companies</h3>
                        <p className="text-sapphire-400 max-w-md mx-auto">
                            Use the search box above to find companies from the UK Companies House registry.
                            Search by company name, number, or keywords like "fintech" or "clean energy".
                        </p>
                    </div>
                )}
            </main>
        </div>
    );
}
