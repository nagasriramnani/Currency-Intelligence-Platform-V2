'use client';

/**
 * AI Daily News Page
 * UK EIS Investment News powered by Tavily AI
 * 
 * Features:
 * - Real-time news from Tavily API
 * - Sector filtering (Technology, Healthcare, Cleantech, Fintech)
 * - EIS relevance scoring
 * - Smooth VC-grade animations
 */

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { EISHeader } from '@/components/EISHeader';
import {
    Newspaper,
    TrendingUp,
    Building2,
    Clock,
    ExternalLink,
    RefreshCw,
    Sparkles,
    Filter,
    Loader2,
    ArrowRight,
    Zap,
    Globe,
    AlertCircle,
    CheckCircle
} from 'lucide-react';
import { cn } from '@/lib/utils';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// News item interface
interface NewsItem {
    id: string;
    title: string;
    content: string;
    source: string;
    url: string;
    published_date?: string;
    sector: string;
    eis_relevance: 'high' | 'medium' | 'low';
    company_mentions?: string[];
}

// Sector tabs
const SECTORS = [
    { id: 'all', label: 'All Sectors', icon: Globe },
    { id: 'technology', label: 'Technology', icon: Zap },
    { id: 'healthcare', label: 'Healthcare', icon: Building2 },
    { id: 'cleantech', label: 'Clean Energy', icon: TrendingUp },
    { id: 'fintech', label: 'Fintech', icon: Sparkles },
];

// Animation variants
const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.1
        }
    }
};

const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
        opacity: 1,
        y: 0,
        transition: { duration: 0.4 }
    }
};

// News Card Component
function NewsCard({ news, index }: { news: NewsItem; index: number }) {
    const relevanceColors = {
        high: 'bg-green-500/10 text-green-400 border-green-500/30',
        medium: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
        low: 'bg-gray-500/10 text-gray-400 border-gray-500/30'
    };

    return (
        <motion.article
            variants={itemVariants}
            whileHover={{ scale: 1.01, y: -2 }}
            className="group relative bg-sapphire-900/50 backdrop-blur-sm border border-sapphire-700/50 rounded-2xl p-6 hover:border-sapphire-600/50 transition-all duration-300 hover:shadow-2xl hover:shadow-sapphire-500/10"
        >
            {/* Top Row: Source & Date */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-sapphire-400 bg-sapphire-800/50 px-2 py-1 rounded-md">
                        {news.source}
                    </span>
                    <span className={cn(
                        "text-xs font-medium px-2 py-1 rounded-md border",
                        relevanceColors[news.eis_relevance]
                    )}>
                        {news.eis_relevance === 'high' ? 'EIS Relevant' :
                            news.eis_relevance === 'medium' ? 'Possibly Relevant' : 'General'}
                    </span>
                </div>
                {news.published_date && (
                    <div className="flex items-center gap-1 text-xs text-sapphire-400">
                        <Clock className="h-3 w-3" />
                        {new Date(news.published_date).toLocaleDateString('en-GB', {
                            day: 'numeric',
                            month: 'short'
                        })}
                    </div>
                )}
            </div>

            {/* Title */}
            <h3 className="text-lg font-semibold text-white mb-3 group-hover:text-sapphire-300 transition-colors line-clamp-2">
                {news.title}
            </h3>

            {/* Content Preview */}
            <p className="text-sm text-sapphire-300 mb-4 line-clamp-3">
                {news.content}
            </p>

            {/* Company Mentions */}
            {news.company_mentions && news.company_mentions.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-4">
                    {news.company_mentions.slice(0, 3).map((company, i) => (
                        <span key={i} className="text-xs bg-sapphire-800/50 text-sapphire-200 px-2 py-1 rounded-md flex items-center gap-1">
                            <Building2 className="h-3 w-3" />
                            {company}
                        </span>
                    ))}
                </div>
            )}

            {/* Bottom Row: Sector & Link */}
            <div className="flex items-center justify-between">
                <span className="text-xs text-sapphire-500 capitalize">
                    {news.sector}
                </span>
                <a
                    href={news.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-xs font-medium text-sapphire-400 hover:text-white transition-colors"
                >
                    Read More
                    <ExternalLink className="h-3 w-3" />
                </a>
            </div>

            {/* Hover Glow Effect */}
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-sapphire-500/0 via-sapphire-500/5 to-purple-500/0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
        </motion.article>
    );
}

export default function AIDailyNewsPage() {
    const [news, setNews] = useState<NewsItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedSector, setSelectedSector] = useState('all');
    const [refreshing, setRefreshing] = useState(false);

    // Fetch news from backend
    const fetchNews = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);

            const response = await fetch(
                `${API_BASE}/api/eis/daily-news?sector=${selectedSector}`
            );

            if (!response.ok) {
                throw new Error('Failed to fetch news');
            }

            const data = await response.json();
            setNews(data.news || []);
        } catch (err) {
            console.error('Failed to fetch news:', err);
            setError('Unable to load AI news. Please try again.');
            // Set mock data for demo
            setNews(getMockNews());
        } finally {
            setLoading(false);
        }
    }, [selectedSector]);

    // Refresh handler
    const handleRefresh = async () => {
        setRefreshing(true);
        await fetchNews();
        setRefreshing(false);
    };

    useEffect(() => {
        fetchNews();
    }, [fetchNews]);

    // Filter news by sector
    const filteredNews = selectedSector === 'all'
        ? news
        : news.filter(n => n.sector.toLowerCase() === selectedSector);

    return (
        <div className="min-h-screen bg-sapphire-950 text-sapphire-100">
            {/* Background Ambience */}
            <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
                <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-purple-600/10 rounded-full blur-[150px] animate-pulse-slow" />
                <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-sapphire-500/10 rounded-full blur-[120px] animate-float" />
            </div>

            <div className="relative z-10">
                <EISHeader />

                <main className="container mx-auto px-4 py-8 max-w-6xl">
                    {/* Page Header */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5 }}
                        className="mb-8"
                    >
                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
                            <div>
                                <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                                    <Sparkles className="h-8 w-8 text-purple-400" />
                                    AI Daily News
                                </h1>
                                <p className="text-sapphire-300 mt-2">
                                    UK EIS investment opportunities powered by Tavily AI
                                </p>
                            </div>

                            <motion.button
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                                onClick={handleRefresh}
                                disabled={refreshing}
                                className={cn(
                                    "flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all",
                                    refreshing
                                        ? "bg-sapphire-800/50 text-sapphire-400 cursor-not-allowed"
                                        : "bg-gradient-to-r from-purple-600 to-sapphire-500 text-white hover:shadow-lg hover:shadow-purple-500/30"
                                )}
                            >
                                <RefreshCw className={cn("h-4 w-4", refreshing && "animate-spin")} />
                                {refreshing ? 'Refreshing...' : 'Refresh News'}
                            </motion.button>
                        </div>

                        {/* Sector Tabs */}
                        <div className="flex flex-wrap gap-2">
                            {SECTORS.map((sector) => {
                                const Icon = sector.icon;
                                const isActive = selectedSector === sector.id;

                                return (
                                    <motion.button
                                        key={sector.id}
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.98 }}
                                        onClick={() => setSelectedSector(sector.id)}
                                        className={cn(
                                            "flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200",
                                            isActive
                                                ? "bg-sapphire-700/80 text-white shadow-lg ring-1 ring-sapphire-600"
                                                : "bg-sapphire-800/50 text-sapphire-300 hover:bg-sapphire-700/50 hover:text-white"
                                        )}
                                    >
                                        <Icon className="h-4 w-4" />
                                        {sector.label}
                                    </motion.button>
                                );
                            })}
                        </div>
                    </motion.div>

                    {/* News Grid */}
                    {loading ? (
                        <div className="flex flex-col items-center justify-center py-20">
                            <motion.div
                                animate={{ rotate: 360 }}
                                transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                            >
                                <Sparkles className="h-12 w-12 text-purple-400" />
                            </motion.div>
                            <p className="mt-4 text-sapphire-300">Fetching AI-powered news...</p>
                        </div>
                    ) : error && filteredNews.length === 0 ? (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="flex flex-col items-center justify-center py-20 text-center"
                        >
                            <AlertCircle className="h-12 w-12 text-yellow-400 mb-4" />
                            <p className="text-sapphire-300">{error}</p>
                            <button
                                onClick={handleRefresh}
                                className="mt-4 px-4 py-2 bg-sapphire-700 text-white rounded-lg hover:bg-sapphire-600 transition-colors"
                            >
                                Try Again
                            </button>
                        </motion.div>
                    ) : (
                        <motion.div
                            variants={containerVariants}
                            initial="hidden"
                            animate="visible"
                            className="grid grid-cols-1 md:grid-cols-2 gap-6"
                        >
                            {filteredNews.map((item, index) => (
                                <NewsCard key={item.id} news={item} index={index} />
                            ))}
                        </motion.div>
                    )}

                    {/* Empty State */}
                    {!loading && filteredNews.length === 0 && !error && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="flex flex-col items-center justify-center py-20 text-center"
                        >
                            <Newspaper className="h-16 w-16 text-sapphire-600 mb-4" />
                            <h3 className="text-xl font-semibold text-white mb-2">No News Found</h3>
                            <p className="text-sapphire-400">
                                No news available for the selected sector. Try a different filter.
                            </p>
                        </motion.div>
                    )}

                    {/* Footer */}
                    <motion.footer
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.5 }}
                        className="mt-12 pt-8 border-t border-sapphire-800/50 text-center"
                    >
                        <p className="text-xs text-sapphire-500">
                            News powered by Tavily AI • Based on EIS heuristic scoring model • Updated in real-time
                        </p>
                        <p className="mt-2 text-xs text-sapphire-600">
                            © 2024 Sapphire Intelligence Platform
                        </p>
                    </motion.footer>
                </main>
            </div>
        </div>
    );
}

// Mock news for demo when API is unavailable
function getMockNews(): NewsItem[] {
    return [
        {
            id: '1',
            title: 'UK Fintech Startup Raises £15M Series A for AI-Powered Banking',
            content: 'A London-based fintech company has secured £15 million in Series A funding to expand its AI-driven banking platform. The investment was led by prominent VC firms...',
            source: 'TechCrunch',
            url: 'https://techcrunch.com',
            published_date: new Date().toISOString(),
            sector: 'fintech',
            eis_relevance: 'high',
            company_mentions: ['NeoBank Labs', 'Index Ventures']
        },
        {
            id: '2',
            title: 'Healthcare AI Company Expands UK Operations with EIS Funding',
            content: 'MediTech AI, a healthcare technology company, has received significant EIS investment to scale its diagnostic platform across NHS trusts...',
            source: 'Sifted',
            url: 'https://sifted.eu',
            published_date: new Date(Date.now() - 86400000).toISOString(),
            sector: 'healthcare',
            eis_relevance: 'high',
            company_mentions: ['MediTech AI']
        },
        {
            id: '3',
            title: 'Clean Energy Startup Launches Grid-Scale Battery Storage Solution',
            content: 'British cleantech company GreenGrid has unveiled its next-generation battery storage technology, attracting attention from institutional investors...',
            source: 'BusinessGreen',
            url: 'https://businessgreen.com',
            published_date: new Date(Date.now() - 172800000).toISOString(),
            sector: 'cleantech',
            eis_relevance: 'medium',
            company_mentions: ['GreenGrid Ltd']
        },
        {
            id: '4',
            title: 'SaaS Platform Secures SEIS Investment for UK SME Market',
            content: 'CloudOps, a Manchester-based SaaS company, has completed a seed round backed by SEIS investors. The platform helps SMEs automate operations...',
            source: 'UKTech News',
            url: 'https://uktech.news',
            published_date: new Date(Date.now() - 259200000).toISOString(),
            sector: 'technology',
            eis_relevance: 'high',
            company_mentions: ['CloudOps', 'Seedcamp']
        },
        {
            id: '5',
            title: 'UK Government Announces Enhanced EIS Tax Relief for Deep Tech',
            content: 'HMRC has confirmed enhanced tax relief rates for Enterprise Investment Scheme investments in qualifying deep technology companies...',
            source: 'Gov.uk',
            url: 'https://gov.uk',
            published_date: new Date(Date.now() - 345600000).toISOString(),
            sector: 'technology',
            eis_relevance: 'high',
            company_mentions: []
        },
        {
            id: '6',
            title: 'Biotech Firm Advances Clinical Trials with Fresh Funding',
            content: 'Cambridge-based biotech company GenomeCure has progressed to Phase 2 clinical trials following a successful £8M funding round from EIS-eligible investors...',
            source: 'BioPharma Reporter',
            url: 'https://biopharma-reporter.com',
            published_date: new Date(Date.now() - 432000000).toISOString(),
            sector: 'healthcare',
            eis_relevance: 'high',
            company_mentions: ['GenomeCure']
        }
    ];
}
