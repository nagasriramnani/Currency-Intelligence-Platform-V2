'use client';

/**
 * EIS Dashboard - Modern UI
 * Enterprise Investment Scheme fact-finding and assessment
 * 
 * Built with:
 * - shadcn-style UI components
 * - Framer Motion animations
 * - Glassmorphism and gradient effects
 * - Local AI Newsroom integration
 */

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Card,
    CardHeader,
    CardTitle,
    CardContent,
    Button,
    Badge,
    StatsCard,
    ScoreGauge,
    GatesDisplay,
    ScoreBreakdown,
    SearchInput,
    NewsletterModal,
    FadeIn,
    AnimatedList,
    AnimatedListItem,
    Tabs,
    TabsList,
    TabsTrigger,
    TabsContent,
    cn
} from '@/components/ui';
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
    Shield,
    Bell,
    Sparkles,
    Target,
    Filter,
    LayoutGrid,
    List,
    RefreshCw,
    ChevronRight,
    X
} from 'lucide-react';

// === TYPES ===
interface CompanyProfile {
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
        items: any[];
        director_count: number;
        total_count: number;
    };
    pscs: {
        items: any[];
        active_count: number;
    };
    charges: {
        items: any[];
        outstanding_count: number;
        has_outstanding: boolean;
    };
    filings: {
        items: any[];
        analysis: {
            has_share_allotments: boolean;
            share_allotment_count: number;
        };
    };
    eis_assessment: {
        score: number;
        max_score: number;
        percentage: number;
        status: string;
        status_description: string;
        factors: any[];
        flags: string[];
        recommendations: string[];
    };
    accounts?: {
        gross_assets?: number;
        employees?: number;
    };
}

interface SearchResult {
    company_number: string;
    title: string;
    company_status: string;
    date_of_creation?: string;
    address_snippet?: string;
}

// === CONSTANTS ===
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function EISDashboard() {
    // State
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
    const [selectedCompany, setSelectedCompany] = useState<CompanyProfile | null>(null);
    const [loading, setLoading] = useState(false);
    const [searchLoading, setSearchLoading] = useState(false);
    const [newsletterOpen, setNewsletterOpen] = useState(false);
    const [activeTab, setActiveTab] = useState('overview');
    const [recentSearches, setRecentSearches] = useState<string[]>([]);
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('list');

    // Search companies
    const handleSearch = useCallback(async () => {
        if (!searchQuery.trim()) return;

        setSearchLoading(true);
        try {
            const response = await fetch(
                `${API_BASE}/api/companies/search?q=${encodeURIComponent(searchQuery)}`
            );
            const data = await response.json();
            setSearchResults(data.items || []);

            // Add to recent searches
            setRecentSearches(prev => {
                const updated = [searchQuery, ...prev.filter(s => s !== searchQuery)].slice(0, 5);
                return updated;
            });
        } catch (error) {
            console.error('Search failed:', error);
            setSearchResults([]);
        } finally {
            setSearchLoading(false);
        }
    }, [searchQuery]);

    // Load company details
    const loadCompanyDetails = useCallback(async (companyNumber: string) => {
        setLoading(true);
        setSelectedCompany(null);

        try {
            const response = await fetch(
                `${API_BASE}/api/eis/company/${companyNumber}/full-profile`
            );
            const data = await response.json();
            setSelectedCompany(data);
        } catch (error) {
            console.error('Failed to load company:', error);
        } finally {
            setLoading(false);
        }
    }, []);

    // Newsletter subscription
    const handleSubscribe = async (email: string, frequency: string) => {
        // TODO: Implement API call
        await new Promise(resolve => setTimeout(resolve, 1000));
        console.log('Subscribed:', email, frequency);
    };

    // Format gates for display
    const formatGates = (assessment: any) => {
        if (!assessment?.factors) return [];

        return [
            {
                name: 'Status Gate',
                passed: assessment.factors.some((f: any) =>
                    f.factor.includes('Status') && f.points > 0
                ),
                reason: assessment.status === 'Likely Eligible' ? 'Company is active' : 'Status check required'
            },
            {
                name: 'SIC Gate',
                passed: !assessment.flags?.some((f: string) => f.includes('SIC') || f.includes('sector')),
                reason: assessment.flags?.find((f: string) => f.includes('SIC')) || 'Eligible sector'
            },
            {
                name: 'Independence Gate',
                passed: !assessment.flags?.some((f: string) => f.includes('corporate') || f.includes('control')),
                reason: 'No corporate majority control detected'
            }
        ];
    };

    // Format score breakdown
    const formatScoreBreakdown = (factors: any[]) => {
        if (!factors) return [];

        return factors.map(f => ({
            factor: f.factor,
            points: f.points,
            maxPoints: f.max_points,
            rationale: f.rationale
        }));
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
            {/* Background Effects */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-0 left-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl" />
                <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />
            </div>

            {/* Header */}
            <header className="relative border-b border-slate-800/50 backdrop-blur-xl bg-slate-900/30">
                <div className="max-w-7xl mx-auto px-6 py-6">
                    <div className="flex items-center justify-between">
                        <FadeIn>
                            <div className="flex items-center gap-4">
                                <div className="p-3 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/30">
                                    <Shield className="h-7 w-7 text-indigo-400" />
                                </div>
                                <div>
                                    <h1 className="text-2xl font-bold text-white">
                                        EIS Investment Scanner
                                    </h1>
                                    <p className="text-sm text-slate-400">
                                        AI-Powered Enterprise Investment Scheme Analysis
                                    </p>
                                </div>
                            </div>
                        </FadeIn>

                        <FadeIn delay={0.1}>
                            <div className="flex items-center gap-3">
                                <Button
                                    variant="ghost"
                                    onClick={() => setNewsletterOpen(true)}
                                >
                                    <Bell className="h-4 w-4 mr-2" />
                                    Subscribe
                                </Button>
                                <Button variant="glow">
                                    <Sparkles className="h-4 w-4 mr-2" />
                                    AI Newsroom
                                </Button>
                            </div>
                        </FadeIn>
                    </div>

                    {/* Search Bar */}
                    <FadeIn delay={0.2} className="mt-6">
                        <SearchInput
                            value={searchQuery}
                            onChange={setSearchQuery}
                            onSearch={handleSearch}
                            placeholder="Search UK companies by name or number..."
                            loading={searchLoading}
                            className="max-w-2xl"
                        />
                    </FadeIn>

                    {/* Recent Searches */}
                    <AnimatePresence>
                        {recentSearches.length > 0 && !searchQuery && (
                            <motion.div
                                initial={{ opacity: 0, y: -10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                className="mt-4 flex items-center gap-2"
                            >
                                <span className="text-xs text-slate-500">Recent:</span>
                                {recentSearches.map((query, i) => (
                                    <button
                                        key={i}
                                        onClick={() => {
                                            setSearchQuery(query);
                                            handleSearch();
                                        }}
                                        className="px-3 py-1 text-xs rounded-full bg-slate-800/50 text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                                    >
                                        {query}
                                    </button>
                                ))}
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </header>

            <main className="relative max-w-7xl mx-auto px-6 py-8">
                <div className="flex gap-8">
                    {/* Left Panel - Search Results */}
                    <div className="w-96 flex-shrink-0">
                        <div className="sticky top-8">
                            {/* Results Header */}
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-lg font-semibold text-white">
                                    {searchResults.length > 0
                                        ? `${searchResults.length} Companies Found`
                                        : 'Search Results'
                                    }
                                </h2>
                                <div className="flex items-center gap-1">
                                    <button
                                        onClick={() => setViewMode('list')}
                                        className={cn(
                                            "p-2 rounded-lg transition-colors",
                                            viewMode === 'list'
                                                ? "bg-slate-800 text-white"
                                                : "text-slate-500 hover:text-white"
                                        )}
                                    >
                                        <List className="h-4 w-4" />
                                    </button>
                                    <button
                                        onClick={() => setViewMode('grid')}
                                        className={cn(
                                            "p-2 rounded-lg transition-colors",
                                            viewMode === 'grid'
                                                ? "bg-slate-800 text-white"
                                                : "text-slate-500 hover:text-white"
                                        )}
                                    >
                                        <LayoutGrid className="h-4 w-4" />
                                    </button>
                                </div>
                            </div>

                            {/* Results List */}
                            <div className="space-y-3 max-h-[calc(100vh-300px)] overflow-y-auto pr-2">
                                <AnimatePresence mode="popLayout">
                                    {searchResults.map((result, index) => (
                                        <motion.div
                                            key={result.company_number}
                                            initial={{ opacity: 0, x: -20 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            exit={{ opacity: 0, x: 20 }}
                                            transition={{ delay: index * 0.05 }}
                                            onClick={() => loadCompanyDetails(result.company_number)}
                                            className={cn(
                                                "p-4 rounded-xl border cursor-pointer transition-all duration-200",
                                                "hover:bg-slate-800/50",
                                                selectedCompany?.company.company_number === result.company_number
                                                    ? "border-indigo-500 bg-indigo-500/10"
                                                    : "border-slate-800 bg-slate-900/50"
                                            )}
                                        >
                                            <div className="flex items-start justify-between">
                                                <div>
                                                    <p className="font-medium text-white truncate">
                                                        {result.title}
                                                    </p>
                                                    <p className="text-sm text-slate-500 mt-1">
                                                        #{result.company_number}
                                                    </p>
                                                </div>
                                                <Badge
                                                    variant={result.company_status === 'active' ? 'success' : 'warning'}
                                                    size="sm"
                                                >
                                                    {result.company_status}
                                                </Badge>
                                            </div>
                                            {result.address_snippet && (
                                                <p className="text-xs text-slate-500 mt-2 flex items-center gap-1">
                                                    <MapPin className="h-3 w-3" />
                                                    {result.address_snippet}
                                                </p>
                                            )}
                                        </motion.div>
                                    ))}
                                </AnimatePresence>

                                {searchResults.length === 0 && !searchLoading && (
                                    <div className="text-center py-12">
                                        <Search className="h-12 w-12 text-slate-700 mx-auto mb-4" />
                                        <p className="text-slate-500">
                                            Search for companies to analyze
                                        </p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Right Panel - Company Details */}
                    <div className="flex-1 min-w-0">
                        <AnimatePresence mode="wait">
                            {loading ? (
                                <motion.div
                                    key="loading"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    className="flex items-center justify-center h-96"
                                >
                                    <div className="text-center">
                                        <Loader2 className="h-12 w-12 text-indigo-500 animate-spin mx-auto mb-4" />
                                        <p className="text-slate-400">Analyzing company...</p>
                                    </div>
                                </motion.div>
                            ) : selectedCompany ? (
                                <CompanyDetails
                                    key={selectedCompany.company.company_number}
                                    company={selectedCompany}
                                    formatGates={formatGates}
                                    formatScoreBreakdown={formatScoreBreakdown}
                                />
                            ) : (
                                <motion.div
                                    key="empty"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    className="flex items-center justify-center h-96"
                                >
                                    <div className="text-center">
                                        <Building2 className="h-16 w-16 text-slate-700 mx-auto mb-4" />
                                        <h3 className="text-xl font-semibold text-slate-400">
                                            Select a Company
                                        </h3>
                                        <p className="text-slate-500 mt-2">
                                            Search and select a company to view EIS analysis
                                        </p>
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                </div>
            </main>

            {/* Newsletter Modal */}
            <NewsletterModal
                open={newsletterOpen}
                onOpenChange={setNewsletterOpen}
                onSubscribe={handleSubscribe}
            />
        </div>
    );
}

// Company Details Component
function CompanyDetails({
    company,
    formatGates,
    formatScoreBreakdown
}: {
    company: CompanyProfile;
    formatGates: (assessment: any) => any[];
    formatScoreBreakdown: (factors: any[]) => any[];
}) {
    const { company: co, eis_assessment, officers, pscs, filings } = company;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="space-y-6"
        >
            {/* Company Header */}
            <Card variant="gradient">
                <CardContent>
                    <div className="flex items-start justify-between">
                        <div className="flex items-start gap-4">
                            <ScoreGauge
                                score={eis_assessment.score}
                                maxScore={eis_assessment.max_score}
                                size="lg"
                                label="EIS Score"
                            />
                            <div>
                                <h2 className="text-2xl font-bold text-white">
                                    {co.company_name}
                                </h2>
                                <p className="text-slate-400 mt-1">
                                    #{co.company_number} • {co.jurisdiction}
                                </p>
                                <div className="flex items-center gap-3 mt-3">
                                    <Badge
                                        variant={
                                            eis_assessment.status === 'Likely Eligible'
                                                ? 'success'
                                                : eis_assessment.status === 'Gated Out'
                                                    ? 'danger'
                                                    : 'warning'
                                        }
                                    >
                                        {eis_assessment.status}
                                    </Badge>
                                    <Badge variant="outline">
                                        {co.company_status}
                                    </Badge>
                                </div>
                            </div>
                        </div>
                        <Button variant="outline">
                            <Download className="h-4 w-4 mr-2" />
                            Export Report
                        </Button>
                    </div>
                </CardContent>
            </Card>

            {/* Stats Grid */}
            <div className="grid grid-cols-4 gap-4">
                <StatsCard
                    title="Directors"
                    value={officers.director_count || 0}
                    icon={Users}
                    variant="purple"
                    delay={0.1}
                />
                <StatsCard
                    title="PSCs"
                    value={pscs.active_count || 0}
                    icon={Shield}
                    variant="cyan"
                    delay={0.2}
                />
                <StatsCard
                    title="Share Allotments"
                    value={filings.analysis?.share_allotment_count || 0}
                    icon={TrendingUp}
                    variant="success"
                    delay={0.3}
                />
                <StatsCard
                    title="Age (Years)"
                    value={co.date_of_creation
                        ? Math.floor((Date.now() - new Date(co.date_of_creation).getTime()) / (365.25 * 24 * 60 * 60 * 1000))
                        : '-'
                    }
                    icon={Clock}
                    variant="default"
                    delay={0.4}
                />
            </div>

            {/* Gates Display */}
            <Card variant="glass" hover={false}>
                <CardContent>
                    <GatesDisplay gates={formatGates(eis_assessment)} />
                </CardContent>
            </Card>

            {/* Score Breakdown */}
            <Card variant="glass" hover={false}>
                <CardContent>
                    <ScoreBreakdown breakdown={formatScoreBreakdown(eis_assessment.factors)} />
                </CardContent>
            </Card>

            {/* Flags & Recommendations */}
            {(eis_assessment.flags?.length > 0 || eis_assessment.recommendations?.length > 0) && (
                <div className="grid grid-cols-2 gap-4">
                    {eis_assessment.flags?.length > 0 && (
                        <Card variant="default" hover={false}>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2 text-amber-400">
                                    <AlertTriangle className="h-5 w-5" />
                                    Risk Flags
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <ul className="space-y-2">
                                    {eis_assessment.flags.map((flag, i) => (
                                        <li key={i} className="text-sm text-slate-400 flex items-start gap-2">
                                            <span className="h-1.5 w-1.5 rounded-full bg-amber-500 mt-2 flex-shrink-0" />
                                            {flag}
                                        </li>
                                    ))}
                                </ul>
                            </CardContent>
                        </Card>
                    )}
                    {eis_assessment.recommendations?.length > 0 && (
                        <Card variant="default" hover={false}>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2 text-emerald-400">
                                    <CheckCircle2 className="h-5 w-5" />
                                    Recommendations
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <ul className="space-y-2">
                                    {eis_assessment.recommendations.map((rec, i) => (
                                        <li key={i} className="text-sm text-slate-400 flex items-start gap-2">
                                            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 mt-2 flex-shrink-0" />
                                            {rec}
                                        </li>
                                    ))}
                                </ul>
                            </CardContent>
                        </Card>
                    )}
                </div>
            )}
        </motion.div>
    );
}
