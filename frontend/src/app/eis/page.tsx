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
import { EISHeader } from '@/components/EISHeader';
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
    X,
    Plus,
    Check,
    FolderPlus,
    DollarSign,
    Banknote,
    Save,
    FolderOpen,
    Bot,
    ChevronDown
} from 'lucide-react';
import Link from 'next/link';

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
        // Age warning fields for 7-year rule
        age_warning?: 'kic_required' | 'condition_check_required' | 'age_limit_exceeded' | null;
        age_exceeded?: boolean;
        company_age_years?: number | null;
    };
    accounts?: {
        gross_assets?: number;
        employees?: number;
    };
    financial_data?: {
        revenue?: string;
        revenue_source?: string;
        last_updated?: string;
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
    const [viewMode, setViewMode] = useState<'portfolio' | 'search'>('portfolio');

    // Portfolio state
    const [portfolioCompanies, setPortfolioCompanies] = useState<any[]>([]);
    const [portfolioLoading, setPortfolioLoading] = useState(true);
    const [portfolioStats, setPortfolioStats] = useState({
        likelyEligible: 0,
        reviewRequired: 0,
        avgScore: 0,
        total: 0
    });

    // User's manually added portfolio companies
    const [myPortfolio, setMyPortfolio] = useState<Set<string>>(new Set());

    // Portfolio save slots (1-5)
    const [savedPortfolios, setSavedPortfolios] = useState<{ [key: string]: any[] }>({});
    const [selectedSlot, setSelectedSlot] = useState<string>('1');
    const [showSlotDropdown, setShowSlotDropdown] = useState(false);

    // Add company to portfolio
    const addToPortfolio = (companyNumber: string, companyName: string) => {
        if (myPortfolio.has(companyNumber)) {
            // Remove from portfolio
            const newPortfolio = new Set(myPortfolio);
            newPortfolio.delete(companyNumber);
            setMyPortfolio(newPortfolio);
        } else {
            // Add to portfolio
            setMyPortfolio(prev => new Set([...prev, companyNumber]));
            // Also add to portfolioCompanies for display
            if (selectedCompany && !portfolioCompanies.find(c => c.company_number === companyNumber)) {
                setPortfolioCompanies(prev => [...prev, {
                    company_number: companyNumber,
                    company_name: companyName,
                    eis_assessment: selectedCompany.eis_assessment,
                    sic_codes: selectedCompany.company?.sic_codes || []
                }]);
                // Update stats
                setPortfolioStats(prev => ({
                    ...prev,
                    total: prev.total + 1,
                    likelyEligible: selectedCompany.eis_assessment?.status?.includes('Eligible')
                        ? prev.likelyEligible + 1
                        : prev.likelyEligible,
                    reviewRequired: selectedCompany.eis_assessment?.status?.includes('Review')
                        ? prev.reviewRequired + 1
                        : prev.reviewRequired
                }));
            }
        }
    };

    // Check if company is in portfolio
    const isInPortfolio = (companyNumber: string) => {
        return myPortfolio.has(companyNumber) || portfolioCompanies.some(c => c.company_number === companyNumber);
    };

    // Load portfolio from localStorage on mount
    useEffect(() => {
        try {
            // Load saved portfolios
            const saved = localStorage.getItem('eis_portfolios');
            if (saved) {
                const portfolios = JSON.parse(saved);
                setSavedPortfolios(portfolios);

                // Load last selected slot
                const lastSlot = localStorage.getItem('eis_selected_slot') || '1';
                setSelectedSlot(lastSlot);

                // Load portfolio from last slot
                const slotData = portfolios[lastSlot] || [];
                if (slotData.length > 0) {
                    setPortfolioCompanies(slotData);
                    setMyPortfolio(new Set(slotData.map((c: any) => c.company_number)));

                    // Calculate stats
                    const eligible = slotData.filter((c: any) => c.eis_assessment?.status?.includes('Eligible')).length;
                    const review = slotData.filter((c: any) => c.eis_assessment?.status?.includes('Review')).length;
                    const avgScore = slotData.length > 0
                        ? slotData.reduce((sum: number, c: any) => sum + (c.eis_assessment?.score || 0), 0) / slotData.length
                        : 0;

                    setPortfolioStats({
                        likelyEligible: eligible,
                        reviewRequired: review,
                        avgScore: Math.round(avgScore),
                        total: slotData.length
                    });
                }
            }
        } catch (error) {
            console.error('Failed to load portfolio from localStorage:', error);
        }
        setPortfolioLoading(false);
    }, []);

    // Save portfolio to slot
    const savePortfolio = (slot: string) => {
        const portfolioData = portfolioCompanies.map(c => ({
            company_number: c.company_number,
            company_name: c.company_name,
            eis_assessment: c.eis_assessment,
            sic_codes: c.sic_codes || []
        }));

        const updated = { ...savedPortfolios, [slot]: portfolioData };
        setSavedPortfolios(updated);
        localStorage.setItem('eis_portfolios', JSON.stringify(updated));
        localStorage.setItem('eis_selected_slot', slot);
        setSelectedSlot(slot);
    };

    // Load portfolio from slot
    const loadPortfolioFromSlot = (slot: string) => {
        const slotData = savedPortfolios[slot] || [];
        setPortfolioCompanies(slotData);
        setMyPortfolio(new Set(slotData.map((c: any) => c.company_number)));
        setSelectedSlot(slot);
        localStorage.setItem('eis_selected_slot', slot);
        setShowSlotDropdown(false);

        // Recalculate stats
        const eligible = slotData.filter((c: any) => c.eis_assessment?.status?.includes('Eligible')).length;
        const review = slotData.filter((c: any) => c.eis_assessment?.status?.includes('Review')).length;
        const avgScore = slotData.length > 0
            ? slotData.reduce((sum: number, c: any) => sum + (c.eis_assessment?.score || 0), 0) / slotData.length
            : 0;

        setPortfolioStats({
            likelyEligible: eligible,
            reviewRequired: review,
            avgScore: Math.round(avgScore),
            total: slotData.length
        });
    };

    // Get slot display name
    const getSlotName = (slot: string) => {
        const count = (savedPortfolios[slot] || []).length;
        return `Portfolio ${slot} (${count})`;
    };

    // Search companies
    const handleSearch = useCallback(async () => {
        if (!searchQuery.trim()) return;

        setSearchLoading(true);
        try {
            const response = await fetch(
                `${API_BASE}/api/eis/search?query=${encodeURIComponent(searchQuery)}&limit=30`
            );
            const data = await response.json();
            // Handle both formats: items array or direct array
            const results = data.items || data.results || data || [];
            setSearchResults(Array.isArray(results) ? results : []);

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

    // Newsletter subscription - REAL API
    const handleSubscribe = async (email: string, frequency: string) => {
        // First, always subscribe the email
        const subscribeResponse = await fetch(`${API_BASE}/api/eis/automation/subscribers`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, frequency })
        });
        if (!subscribeResponse.ok) {
            throw new Error('Failed to subscribe');
        }

        // If frequency is 'now', also send an immediate email with portfolio data
        if (frequency === 'now') {
            console.log('=== SENDING EMAIL NOW ===');
            console.log('Portfolio companies:', portfolioCompanies);

            // Format portfolio companies for the API - match actual data structure
            const portfolioData = (portfolioCompanies || []).map(c => {
                console.log('Processing company:', c);
                // portfolioCompanies stores data directly, not nested under c.company
                return {
                    company_number: c?.company_number || '',
                    company_name: c?.company_name || 'Unknown',
                    eis_score: c?.eis_assessment?.score || 0,
                    eis_status: c?.eis_assessment?.status || 'Unknown',
                    sic_codes: c?.sic_codes || []
                };
            });

            console.log('Formatted portfolio data:', portfolioData);

            const sendResponse = await fetch(`${API_BASE}/api/eis/automation/send-email`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email,
                    portfolio_companies: portfolioData
                })
            });

            console.log('Send email response status:', sendResponse.status);

            if (!sendResponse.ok) {
                const errorData = await sendResponse.json().catch(() => ({}));
                console.error('Send email error:', errorData);
                throw new Error(errorData.detail || 'Failed to send email');
            }

            console.log('Email sent successfully!');
        }
    };

    // Export Portfolio Report as PDF
    const exportPortfolioReport = async () => {
        try {
            if (portfolioCompanies.length === 0) {
                alert('No companies in portfolio to export');
                return;
            }

            // Format companies for the API - send full company data
            const companiesForReport = portfolioCompanies.map(c => ({
                company_number: c.company_number,
                company_name: c.company_name,
                company_status: c.company_status || 'active',
                date_of_creation: c.date_of_creation,
                sic_codes: c.sic_codes || [],
                registered_office_address: c.registered_office_address || {},
                eis_score: c.eis_assessment?.score || 0,
                eis_status: c.eis_assessment?.status || 'Unknown'
            }));

            const response = await fetch(`${API_BASE}/api/eis/newsletter`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(companiesForReport)  // Send array directly, not wrapped in object
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `EIS_Portfolio_Report_${new Date().toISOString().split('T')[0]}.pdf`;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
            } else {
                const errorData = await response.json().catch(() => ({}));
                alert(`Failed to generate report: ${errorData.detail || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Export failed:', error);
            alert('Failed to export report');
        }
    };

    // Generate AI News Summary (AI Newsroom)
    const [aiNewsroomLoading, setAiNewsroomLoading] = useState(false);
    const [aiNewsSummary, setAiNewsSummary] = useState<string | null>(null);
    const [aiNewsOpen, setAiNewsOpen] = useState(false);

    const generateAiNews = async () => {
        if (!selectedCompany) {
            alert('Please select a company first');
            return;
        }
        setAiNewsroomLoading(true);
        setAiNewsOpen(true);
        try {
            // This would call the newsroom pipeline
            const response = await fetch(`${API_BASE}/api/eis/company/${selectedCompany.company.company_number}/news`);
            if (response.ok) {
                const data = await response.json();
                setAiNewsSummary(data.summary || data.content || 'No news available');
            } else {
                setAiNewsSummary('AI summary generation not available. The Mistral 7B model is required on the backend.');
            }
        } catch (error) {
            setAiNewsSummary('Failed to generate AI summary. Please ensure the backend is running.');
        } finally {
            setAiNewsroomLoading(false);
        }
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

            {/* Navigation Header */}
            <EISHeader />

            {/* Sub-Header */}
            <header className="relative border-b border-slate-800/50 backdrop-blur-xl bg-slate-900/30">
                <div className="max-w-[1800px] mx-auto px-6 py-6">
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
                                {/* Portfolio Slot Selector */}
                                <div className="relative z-[200]">
                                    <button
                                        onClick={() => setShowSlotDropdown(!showSlotDropdown)}
                                        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 border border-slate-600 hover:border-indigo-500/50 transition-colors text-sm text-slate-200"
                                    >
                                        <FolderOpen className="h-4 w-4 text-indigo-400" />
                                        <span className="font-medium">{getSlotName(selectedSlot)}</span>
                                        <ChevronDown className={`h-4 w-4 text-slate-400 transition-transform ${showSlotDropdown ? 'rotate-180' : ''}`} />
                                    </button>

                                    {showSlotDropdown && (
                                        <>
                                            {/* Backdrop to close dropdown */}
                                            <div
                                                className="fixed inset-0 z-[150]"
                                                onClick={() => setShowSlotDropdown(false)}
                                            />
                                            {/* Dropdown Menu */}
                                            <div className="absolute top-full left-0 mt-2 w-52 bg-slate-800 border border-slate-600 rounded-xl shadow-2xl z-[200] overflow-hidden">
                                                <div className="bg-gradient-to-b from-slate-700/50 to-transparent px-3 py-2 border-b border-slate-700">
                                                    <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Select Portfolio</span>
                                                </div>
                                                {['1', '2', '3', '4', '5'].map(slot => (
                                                    <button
                                                        key={slot}
                                                        onClick={() => loadPortfolioFromSlot(slot)}
                                                        className={`w-full text-left px-4 py-2.5 text-sm transition-colors flex items-center justify-between ${selectedSlot === slot
                                                            ? 'bg-indigo-500/20 text-indigo-300 border-l-2 border-indigo-500'
                                                            : 'text-slate-300 hover:bg-slate-700/50'
                                                            }`}
                                                    >
                                                        <span>{getSlotName(slot)}</span>
                                                        {selectedSlot === slot && (
                                                            <Check className="h-4 w-4 text-indigo-400" />
                                                        )}
                                                    </button>
                                                ))}
                                            </div>
                                        </>
                                    )}
                                </div>

                                {/* Save Portfolio Button */}
                                <Button
                                    variant="outline"
                                    onClick={() => savePortfolio(selectedSlot)}
                                    title={`Save to ${getSlotName(selectedSlot)}`}
                                >
                                    <Save className="h-4 w-4 mr-2" />
                                    Save
                                </Button>

                                <div className="h-6 w-px bg-slate-700" />

                                <Button
                                    variant="outline"
                                    onClick={exportPortfolioReport}
                                >
                                    <Download className="h-4 w-4 mr-2" />
                                    Export Report
                                </Button>
                                <Button
                                    variant="ghost"
                                    onClick={() => setNewsletterOpen(true)}
                                >
                                    <Bell className="h-4 w-4 mr-2" />
                                    Subscribe
                                </Button>
                                <Button
                                    variant="glow"
                                    onClick={generateAiNews}
                                    loading={aiNewsroomLoading}
                                >
                                    <Sparkles className="h-4 w-4 mr-2" />
                                    AI Newsroom
                                </Button>

                                <div className="h-6 w-px bg-slate-700" />

                                {/* EIS Advisor Button */}
                                <Link href="/advisor">
                                    <Button variant="glow" className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500">
                                        <Bot className="h-4 w-4 mr-2" />
                                        EIS Advisor
                                    </Button>
                                </Link>
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

            <main className="relative max-w-[1800px] mx-auto px-6 py-8">
                <div className="flex gap-6">
                    {/* Left Panel - Portfolio / Search Results - EXPANDED */}
                    <div className="w-[450px] flex-shrink-0">
                        <div className="sticky top-8">
                            {/* Mode Toggle */}
                            <div className="flex items-center gap-2 mb-4 p-1 bg-slate-900/80 rounded-xl border border-slate-800">
                                <button
                                    onClick={() => setViewMode('portfolio')}
                                    className={cn(
                                        "flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-all",
                                        viewMode === 'portfolio'
                                            ? "bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg"
                                            : "text-slate-400 hover:text-white"
                                    )}
                                >
                                    Portfolio ({portfolioCompanies.length})
                                </button>
                                <button
                                    onClick={() => setViewMode('search')}
                                    className={cn(
                                        "flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-all",
                                        viewMode === 'search'
                                            ? "bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg"
                                            : "text-slate-400 hover:text-white"
                                    )}
                                >
                                    Search ({searchResults.length})
                                </button>
                            </div>

                            {/* Portfolio Stats (only in portfolio mode) */}
                            {viewMode === 'portfolio' && !portfolioLoading && (
                                <div className="grid grid-cols-2 gap-2 mb-4">
                                    <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg">
                                        <p className="text-2xl font-bold text-emerald-400">{portfolioStats.likelyEligible}</p>
                                        <p className="text-xs text-slate-400">Likely Eligible</p>
                                    </div>
                                    <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                                        <p className="text-2xl font-bold text-amber-400">{portfolioStats.reviewRequired}</p>
                                        <p className="text-xs text-slate-400">Review Required</p>
                                    </div>
                                    <div className="p-3 bg-indigo-500/10 border border-indigo-500/30 rounded-lg">
                                        <p className="text-2xl font-bold text-indigo-400">{portfolioStats.avgScore}</p>
                                        <p className="text-xs text-slate-400">Avg Score</p>
                                    </div>
                                    <div className="p-3 bg-slate-800/50 border border-slate-700 rounded-lg">
                                        <p className="text-2xl font-bold text-white">{portfolioStats.total}</p>
                                        <p className="text-xs text-slate-400">Total</p>
                                    </div>
                                </div>
                            )}

                            {/* Companies List */}
                            <div className="space-y-3 max-h-[calc(100vh-400px)] overflow-y-auto pr-2">
                                <AnimatePresence mode="popLayout">
                                    {viewMode === 'portfolio' ? (
                                        portfolioLoading ? (
                                            <div className="flex items-center justify-center py-12">
                                                <Loader2 className="h-8 w-8 text-indigo-500 animate-spin" />
                                            </div>
                                        ) : (
                                            portfolioCompanies.map((company, index) => (
                                                <motion.div
                                                    key={company.company_number}
                                                    initial={{ opacity: 0, x: -20 }}
                                                    animate={{ opacity: 1, x: 0 }}
                                                    exit={{ opacity: 0, x: 20 }}
                                                    transition={{ delay: index * 0.03 }}
                                                    onClick={() => loadCompanyDetails(company.company_number)}
                                                    className={cn(
                                                        "p-4 rounded-xl border cursor-pointer transition-all duration-200",
                                                        "hover:bg-slate-800/50",
                                                        selectedCompany?.company.company_number === company.company_number
                                                            ? "border-indigo-500 bg-indigo-500/10"
                                                            : "border-slate-800 bg-slate-900/50"
                                                    )}
                                                >
                                                    <div className="flex items-start justify-between">
                                                        <div className="flex-1 min-w-0">
                                                            <p className="font-medium text-white truncate">
                                                                {company.company_name}
                                                            </p>
                                                            <p className="text-sm text-slate-500 mt-1">
                                                                #{company.company_number}
                                                            </p>
                                                        </div>
                                                        <div className="flex flex-col items-end gap-1">
                                                            <Badge
                                                                variant={company.eis_assessment?.status?.includes('Eligible') ? 'success' : 'warning'}
                                                                size="sm"
                                                            >
                                                                {company.eis_assessment?.score || 0}/100
                                                            </Badge>
                                                        </div>
                                                    </div>
                                                </motion.div>
                                            ))
                                        )
                                    ) : (
                                        searchResults.length > 0 ? (
                                            searchResults.map((result, index) => (
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
                                            ))
                                        ) : (
                                            <div className="text-center py-12">
                                                <Search className="h-12 w-12 text-slate-700 mx-auto mb-4" />
                                                <p className="text-slate-500">
                                                    Search for companies to analyze
                                                </p>
                                            </div>
                                        )
                                    )}
                                </AnimatePresence>
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
                                    addToPortfolio={addToPortfolio}
                                    isInPortfolio={isInPortfolio}
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

            {/* AI Newsroom Modal */}
            <AnimatePresence>
                {aiNewsOpen && (
                    <>
                        {/* Backdrop */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setAiNewsOpen(false)}
                            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
                        />
                        {/* Modal */}
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.95, y: 20 }}
                            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-lg max-h-[80vh] rounded-2xl bg-gradient-to-b from-slate-900 to-slate-950 border border-slate-800 shadow-2xl p-6 overflow-y-auto"
                        >
                            <button
                                onClick={() => setAiNewsOpen(false)}
                                className="absolute right-4 top-4 p-2 rounded-lg text-slate-500 hover:text-white hover:bg-slate-800"
                            >
                                <X className="h-5 w-5" />
                            </button>
                            <div className="flex items-center gap-3 mb-4">
                                <div className="p-3 rounded-xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-purple-500/30">
                                    <Sparkles className="h-6 w-6 text-purple-400" />
                                </div>
                                <div>
                                    <h3 className="text-xl font-semibold text-white">AI Newsroom</h3>
                                    <p className="text-sm text-slate-400">
                                        {selectedCompany?.company.company_name || 'Company'} News Summary
                                    </p>
                                </div>
                            </div>
                            <div className="bg-slate-800/50 rounded-xl p-4 min-h-[150px]">
                                {aiNewsroomLoading ? (
                                    <div className="flex items-center justify-center h-full py-8">
                                        <Loader2 className="h-8 w-8 text-purple-500 animate-spin" />
                                    </div>
                                ) : (
                                    <p className="text-slate-300 leading-relaxed">
                                        {aiNewsSummary || 'No news summary available.'}
                                    </p>
                                )}
                            </div>
                            <p className="text-xs text-slate-500 mt-4 text-center">
                                Powered by Mistral 7B AI Analyst
                            </p>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </div>
    );
}

// Company Details Component
function CompanyDetails({
    company,
    formatGates,
    formatScoreBreakdown,
    addToPortfolio,
    isInPortfolio
}: {
    company: CompanyProfile;
    formatGates: (assessment: any) => any[];
    formatScoreBreakdown: (factors: any[]) => any[];
    addToPortfolio: (companyNumber: string, companyName: string) => void;
    isInPortfolio: (companyNumber: string) => boolean;
}) {
    const { company: co, eis_assessment, officers, pscs, filings } = company;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="space-y-6"
        >
            {/* Age Warning Banner - Prominent display for >7 year companies */}
            {eis_assessment.age_warning && (
                <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`p-4 rounded-xl border ${eis_assessment.age_exceeded
                        ? 'bg-red-500/10 border-red-500/30'
                        : 'bg-amber-500/10 border-amber-500/30'
                        }`}
                >
                    <div className="flex items-start gap-3">
                        <AlertTriangle className={`h-5 w-5 mt-0.5 flex-shrink-0 ${eis_assessment.age_exceeded ? 'text-red-400' : 'text-amber-400'
                            }`} />
                        <div>
                            <h3 className={`font-semibold ${eis_assessment.age_exceeded ? 'text-red-400' : 'text-amber-400'
                                }`}>
                                {eis_assessment.age_warning === 'kic_required' && 'Age Warning: KIC Verification Required'}
                                {eis_assessment.age_warning === 'condition_check_required' && 'Age Warning: Exceeds 7-Year Limit'}
                                {eis_assessment.age_warning === 'age_limit_exceeded' && 'Age Limit Exceeded: >10 Years Old'}
                            </h3>
                            <p className="text-sm text-slate-400 mt-1">
                                {eis_assessment.age_warning === 'kic_required' &&
                                    `Company is ${eis_assessment.company_age_years || '>7'} years old. May qualify under Knowledge-Intensive Company (KIC) exception (10-year limit). Verify KIC status.`}
                                {eis_assessment.age_warning === 'condition_check_required' &&
                                    `Company is ${eis_assessment.company_age_years || '>7'} years old. Standard EIS requires <7 years. Check for Condition A (prior EIS/SEIS funding) or Condition C (new business activity >50% turnover).`}
                                {eis_assessment.age_warning === 'age_limit_exceeded' &&
                                    `Company is ${eis_assessment.company_age_years || '>10'} years old - exceeds even KIC 10-year limit. Only Condition A (follow-on funding) or Condition C (new market) may apply.`}
                            </p>
                        </div>
                    </div>
                </motion.div>
            )}

            {/* Company Header */}
            <Card variant="gradient">
                <CardContent>
                    <div className="flex items-start justify-between">
                        <div className="flex items-start gap-4">
                            <ScoreGauge
                                score={eis_assessment.score}
                                maxScore={100}
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
                                <div className="flex items-center gap-3 mt-3 flex-wrap">
                                    {/* Check if ANY factor score is 0 or EIS score < 50 - show Not Eligible */}
                                    {(() => {
                                        const hasZeroFactor = eis_assessment.factors?.some((f: any) =>
                                            (f.score <= 0 || f.value <= 0)
                                        );
                                        const hasAgeWarning = eis_assessment.age_warning || eis_assessment.age_exceeded;
                                        const isNotEligible = eis_assessment.score < 50 || hasZeroFactor || eis_assessment.age_exceeded;

                                        return (
                                            <Badge
                                                variant={
                                                    isNotEligible
                                                        ? 'danger'
                                                        : hasAgeWarning
                                                            ? 'warning'
                                                            : eis_assessment.status === 'Likely Eligible'
                                                                ? 'success'
                                                                : eis_assessment.status === 'Gated Out'
                                                                    ? 'danger'
                                                                    : 'warning'
                                                }
                                            >
                                                {isNotEligible ? 'Likely Not Eligible' : hasAgeWarning ? 'Requires Verification' : eis_assessment.status}
                                            </Badge>
                                        );
                                    })()}

                                    {/* Age Warning Badge */}
                                    {eis_assessment.age_warning && (
                                        <Badge variant="warning" className="bg-amber-500/20 text-amber-400 border-amber-500/30">
                                            {eis_assessment.age_warning === 'kic_required' && '⚠️ KIC Verification Required'}
                                            {eis_assessment.age_warning === 'condition_check_required' && '🚨 Age >7 Years - Condition A/C Check'}
                                            {eis_assessment.age_warning === 'age_limit_exceeded' && '🚨 Age Limit Exceeded (>10 Years)'}
                                        </Badge>
                                    )}

                                    <Badge variant="outline">
                                        {co.company_status}
                                    </Badge>
                                </div>
                            </div>
                        </div>
                        <div className="flex flex-col items-end gap-2">
                            <Button
                                variant={isInPortfolio(co.company_number) ? "default" : "outline"}
                                onClick={() => addToPortfolio(co.company_number, co.company_name)}
                                className={isInPortfolio(co.company_number)
                                    ? "bg-emerald-600 hover:bg-emerald-700 text-white"
                                    : ""}
                            >
                                {isInPortfolio(co.company_number) ? (
                                    <>
                                        <Check className="h-4 w-4 mr-2" />
                                        In Portfolio
                                    </>
                                ) : (
                                    <>
                                        <FolderPlus className="h-4 w-4 mr-2" />
                                        Add to Portfolio
                                    </>
                                )}
                            </Button>
                            {/* Eligibility Warning - Show when Company Age factor score is 0 or EIS score < 50 */}
                            {(eis_assessment.score < 50 ||
                                eis_assessment.factors?.some((f: any) =>
                                    (f.name?.toLowerCase().includes('age') || f.factor?.toLowerCase().includes('age')) &&
                                    (f.score <= 0 || f.value <= 0)
                                )) && (
                                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-500/20 border border-red-500/30">
                                        <AlertTriangle className="h-4 w-4 text-red-400" />
                                        <span className="text-xs font-medium text-red-400">Likely Not Eligible</span>
                                    </div>
                                )}
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Stats Grid - Responsive with wrapping */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
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
                    title="Allotments"
                    value={filings.analysis?.share_allotment_count || 0}
                    icon={TrendingUp}
                    variant="success"
                    delay={0.3}
                />
                <StatsCard
                    title="Age"
                    value={co.date_of_creation
                        ? `${Math.floor((Date.now() - new Date(co.date_of_creation).getTime()) / (365.25 * 24 * 60 * 60 * 1000))}y`
                        : '-'
                    }
                    icon={Clock}
                    variant="default"
                    delay={0.4}
                />
                <StatsCard
                    title="Revenue"
                    value={
                        company.financial_data?.revenue
                            ? company.financial_data.revenue
                            : company.accounts?.gross_assets
                                ? `£${(company.accounts.gross_assets / 1000000).toFixed(1)}M`
                                : 'N/A'
                    }
                    icon={Banknote}
                    variant="warning"
                    delay={0.5}
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
