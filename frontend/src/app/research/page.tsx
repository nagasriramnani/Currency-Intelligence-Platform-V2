'use client';

import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Building2,
    Search,
    Globe,
    MapPin,
    Briefcase,
    Download,
    Mail,
    CheckCircle2,
    Loader2,
    ChevronDown,
    ChevronUp,
    ExternalLink,
    Copy,
    Sparkles,
    TrendingUp,
    DollarSign,
    Newspaper,
    ArrowRight,
    AlertCircle
} from 'lucide-react';
import { EISHeader } from '@/components/EISHeader';

// === CONSTANTS ===
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// === TYPES ===
interface ResearchReport {
    company_name: string;
    company_url?: string;
    company_hq?: string;
    company_industry?: string;
    generated_at: string;
    research_time: number;
    company_overview: {
        business_description: string;
        leadership_team: string;
        target_market: string;
        key_differentiators: string;
        business_model: string;
    };
    industry_overview: {
        market_landscape: string;
        competition: string;
        competitive_advantages: string;
        market_challenges: string;
    };
    financial_overview: {
        funding_investment: string;
        revenue_model: string;
        financial_milestones: string;
    };
    news: Array<{
        title: string;
        content: string;
        url: string;
    }>;
    references: Array<{
        title: string;
        url: string;
    }>;
    stats: Record<string, string>;
    queries: Record<string, string[]>;
}

// === EXAMPLE COMPANIES ===
const EXAMPLE_COMPANIES = [
    { name: 'Spotify', url: 'spotify.com', hq: 'Stockholm, Sweden', industry: 'Music Streaming' },
    { name: 'Revolut', url: 'revolut.com', hq: 'London, UK', industry: 'Fintech' },
    { name: 'Notion', url: 'notion.so', hq: 'San Francisco, USA', industry: 'Productivity Software' },
    { name: 'Stripe', url: 'stripe.com', hq: 'San Francisco, USA', industry: 'Payments' }
];

// === COMPONENT ===
export default function ResearchAgentPage() {
    // Form state
    const [companyName, setCompanyName] = useState('');
    const [companyUrl, setCompanyUrl] = useState('');
    const [companyHq, setCompanyHq] = useState('');
    const [companyIndustry, setCompanyIndustry] = useState('');

    // Research state
    const [isResearching, setIsResearching] = useState(false);
    const [researchProgress, setResearchProgress] = useState('');
    const [report, setReport] = useState<ResearchReport | null>(null);
    const [error, setError] = useState<string | null>(null);

    // UI state
    const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['company', 'industry', 'financial', 'news']));
    const [showQueries, setShowQueries] = useState(false);
    const [isPdfLoading, setIsPdfLoading] = useState(false);
    const [isEmailSending, setIsEmailSending] = useState(false);
    const [emailAddress, setEmailAddress] = useState('');
    const [showEmailModal, setShowEmailModal] = useState(false);

    // Toggle section
    const toggleSection = (section: string) => {
        const newExpanded = new Set(expandedSections);
        if (newExpanded.has(section)) {
            newExpanded.delete(section);
        } else {
            newExpanded.add(section);
        }
        setExpandedSections(newExpanded);
    };

    // Fill example company
    const fillExample = (example: typeof EXAMPLE_COMPANIES[0]) => {
        setCompanyName(example.name);
        setCompanyUrl(example.url);
        setCompanyHq(example.hq);
        setCompanyIndustry(example.industry);
    };

    // Start research
    const startResearch = useCallback(async () => {
        if (!companyName.trim()) {
            setError('Please enter a company name');
            return;
        }

        setIsResearching(true);
        setError(null);
        setReport(null);
        setResearchProgress('Initializing research agent...');

        try {
            setResearchProgress('Generating research queries...');
            await new Promise(r => setTimeout(r, 500));

            setResearchProgress('Searching company information...');
            await new Promise(r => setTimeout(r, 300));

            const response = await fetch(`${API_BASE}/api/research/company`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    company_name: companyName,
                    company_url: companyUrl || null,
                    company_hq: companyHq || null,
                    company_industry: companyIndustry || null
                })
            });

            const data = await response.json();

            if (data.success && data.report) {
                setReport(data.report);
                setResearchProgress('Research completed successfully!');
            } else {
                setError(data.error || 'Research failed');
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Research failed');
        } finally {
            setIsResearching(false);
        }
    }, [companyName, companyUrl, companyHq, companyIndustry]);

    // Download PDF
    const downloadPdf = async () => {
        if (!report) return;

        setIsPdfLoading(true);
        try {
            const response = await fetch(`${API_BASE}/api/research/pdf`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(report)
            });

            const data = await response.json();

            if (data.success && data.pdf) {
                // Decode base64 and download
                const byteCharacters = atob(data.pdf);
                const byteNumbers = new Array(byteCharacters.length);
                for (let i = 0; i < byteCharacters.length; i++) {
                    byteNumbers[i] = byteCharacters.charCodeAt(i);
                }
                const byteArray = new Uint8Array(byteNumbers);
                const blob = new Blob([byteArray], { type: 'application/pdf' });

                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = data.filename || `${report.company_name}_Research_Report.pdf`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                window.URL.revokeObjectURL(url);
            } else {
                alert(data.error || 'PDF generation failed');
            }
        } catch (err) {
            alert('Failed to generate PDF');
        } finally {
            setIsPdfLoading(false);
        }
    };

    // Send email
    const sendEmail = async () => {
        if (!report || !emailAddress) return;

        setIsEmailSending(true);
        try {
            const response = await fetch(`${API_BASE}/api/research/email`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: emailAddress,
                    report: report
                })
            });

            const data = await response.json();

            if (data.success) {
                alert(`Report sent to ${emailAddress}!`);
                setShowEmailModal(false);
                setEmailAddress('');
            } else {
                alert(data.error || 'Email sending failed');
            }
        } catch (err) {
            alert('Failed to send email');
        } finally {
            setIsEmailSending(false);
        }
    };

    // Copy report text
    const copyReport = () => {
        if (!report) return;
        const text = `${report.company_name} Research Report\n\n` +
            `Company Overview:\n${report.company_overview.business_description}\n\n` +
            `Industry Overview:\n${report.industry_overview.market_landscape}\n\n` +
            `Financial Overview:\n${report.financial_overview.funding_investment}`;
        navigator.clipboard.writeText(text);
        alert('Report copied to clipboard!');
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-sapphire-900 via-sapphire-800 to-sapphire-900 text-white">
            {/* Sapphire Intelligence Header */}
            <EISHeader />

            {/* Main Content */}
            <main className="pt-24 pb-12 px-6">
                <div className="max-w-5xl mx-auto">
                    {/* Header */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-center mb-12"
                    >
                        <h1 className="text-4xl font-bold mb-4">Company Research Agent</h1>
                        <p className="text-lg text-slate-400">
                            Conduct in-depth company diligence powered by Tavily AI
                        </p>
                    </motion.div>

                    {/* Research Form */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-8 mb-8"
                    >
                        {/* Example Companies */}
                        <div className="mb-6">
                            <span className="text-sm text-slate-400 flex items-center gap-2 mb-3">
                                <Sparkles className="w-4 h-4" />
                                Try an example:
                            </span>
                            <div className="flex flex-wrap gap-2">
                                {EXAMPLE_COMPANIES.map((example) => (
                                    <button
                                        key={example.name}
                                        onClick={() => fillExample(example)}
                                        className="px-4 py-2 rounded-lg bg-indigo-500/20 hover:bg-indigo-500/30 
                                                 text-indigo-300 text-sm font-medium transition flex items-center gap-2"
                                    >
                                        {example.name}
                                        <ArrowRight className="w-3 h-3" />
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Form Grid */}
                        <div className="grid md:grid-cols-2 gap-6 mb-6">
                            {/* Company Name */}
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-2">
                                    Company Name *
                                </label>
                                <div className="relative">
                                    <Building2 className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                                    <input
                                        type="text"
                                        value={companyName}
                                        onChange={(e) => setCompanyName(e.target.value)}
                                        placeholder="Enter company name"
                                        className="w-full pl-12 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl
                                                 text-white placeholder-slate-500 focus:border-indigo-500 focus:ring-1 
                                                 focus:ring-indigo-500 transition"
                                    />
                                </div>
                            </div>

                            {/* Company URL */}
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-2">
                                    Company URL
                                </label>
                                <div className="relative">
                                    <Globe className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                                    <input
                                        type="text"
                                        value={companyUrl}
                                        onChange={(e) => setCompanyUrl(e.target.value)}
                                        placeholder="example.com"
                                        className="w-full pl-12 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl
                                                 text-white placeholder-slate-500 focus:border-indigo-500 focus:ring-1 
                                                 focus:ring-indigo-500 transition"
                                    />
                                </div>
                            </div>

                            {/* Company HQ */}
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-2">
                                    Company HQ
                                </label>
                                <div className="relative">
                                    <MapPin className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                                    <input
                                        type="text"
                                        value={companyHq}
                                        onChange={(e) => setCompanyHq(e.target.value)}
                                        placeholder="City, Country"
                                        className="w-full pl-12 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl
                                                 text-white placeholder-slate-500 focus:border-indigo-500 focus:ring-1 
                                                 focus:ring-indigo-500 transition"
                                    />
                                </div>
                            </div>

                            {/* Company Industry */}
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-2">
                                    Company Industry
                                </label>
                                <div className="relative">
                                    <Briefcase className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                                    <input
                                        type="text"
                                        value={companyIndustry}
                                        onChange={(e) => setCompanyIndustry(e.target.value)}
                                        placeholder="e.g. Technology, Healthcare"
                                        className="w-full pl-12 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl
                                                 text-white placeholder-slate-500 focus:border-indigo-500 focus:ring-1 
                                                 focus:ring-indigo-500 transition"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Submit Button */}
                        <button
                            onClick={startResearch}
                            disabled={isResearching || !companyName.trim()}
                            className="w-full py-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 
                                     hover:to-purple-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl 
                                     font-semibold text-lg transition flex items-center justify-center gap-3"
                        >
                            {isResearching ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    {researchProgress}
                                </>
                            ) : (
                                <>
                                    <Search className="w-5 h-5" />
                                    Start Research
                                </>
                            )}
                        </button>

                        {/* Error */}
                        {error && (
                            <div className="mt-4 p-4 bg-red-500/20 border border-red-500/30 rounded-xl flex items-center gap-3">
                                <AlertCircle className="w-5 h-5 text-red-400" />
                                <span className="text-red-300">{error}</span>
                            </div>
                        )}
                    </motion.div>

                    {/* Research Complete Indicator */}
                    {report && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="bg-emerald-500/20 border border-emerald-500/30 rounded-xl p-4 mb-8 flex items-center gap-3"
                        >
                            <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                            <div>
                                <p className="font-semibold text-emerald-300">Complete</p>
                                <p className="text-sm text-emerald-400/80">
                                    Research completed in {report.research_time?.toFixed(1)}s
                                </p>
                            </div>
                        </motion.div>
                    )}

                    {/* Report Display */}
                    <AnimatePresence>
                        {report && (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                className="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 overflow-hidden"
                            >
                                {/* Report Header */}
                                <div className="p-6 border-b border-white/10 flex items-center justify-between">
                                    <h2 className="text-2xl font-bold">{report.company_name} Research Report</h2>
                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={copyReport}
                                            className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition"
                                            title="Copy to clipboard"
                                        >
                                            <Copy className="w-5 h-5" />
                                        </button>
                                        <button
                                            onClick={downloadPdf}
                                            disabled={isPdfLoading}
                                            className="px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-black 
                                                     font-semibold transition flex items-center gap-2"
                                        >
                                            {isPdfLoading ? (
                                                <Loader2 className="w-4 h-4 animate-spin" />
                                            ) : (
                                                <Download className="w-4 h-4" />
                                            )}
                                            PDF
                                        </button>
                                        <button
                                            onClick={() => setShowEmailModal(true)}
                                            className="px-4 py-2 rounded-lg bg-indigo-500 hover:bg-indigo-400 
                                                     font-semibold transition flex items-center gap-2"
                                        >
                                            <Mail className="w-4 h-4" />
                                            Email
                                        </button>
                                    </div>
                                </div>

                                {/* Report Sections */}
                                <div className="p-6 space-y-4">
                                    {/* Company Overview */}
                                    <ReportSection
                                        title="Company Overview"
                                        icon={<Building2 className="w-5 h-5" />}
                                        isExpanded={expandedSections.has('company')}
                                        onToggle={() => toggleSection('company')}
                                    >
                                        <div className="space-y-4">
                                            <SubSection title="Business Description" content={report.company_overview.business_description} />
                                            <SubSection title="Leadership Team" content={report.company_overview.leadership_team} />
                                            <SubSection title="Target Market" content={report.company_overview.target_market} />
                                            <SubSection title="Key Differentiators" content={report.company_overview.key_differentiators} />
                                            <SubSection title="Business Model" content={report.company_overview.business_model} />
                                        </div>
                                    </ReportSection>

                                    {/* Industry Overview */}
                                    <ReportSection
                                        title="Industry Overview"
                                        icon={<TrendingUp className="w-5 h-5" />}
                                        isExpanded={expandedSections.has('industry')}
                                        onToggle={() => toggleSection('industry')}
                                    >
                                        <div className="space-y-4">
                                            <SubSection title="Market Landscape" content={report.industry_overview.market_landscape} />
                                            <SubSection title="Competition" content={report.industry_overview.competition} />
                                            <SubSection title="Competitive Advantages" content={report.industry_overview.competitive_advantages} />
                                            <SubSection title="Market Challenges" content={report.industry_overview.market_challenges} />
                                        </div>
                                    </ReportSection>

                                    {/* Financial Overview */}
                                    <ReportSection
                                        title="Financial Overview"
                                        icon={<DollarSign className="w-5 h-5" />}
                                        isExpanded={expandedSections.has('financial')}
                                        onToggle={() => toggleSection('financial')}
                                    >
                                        <div className="space-y-4">
                                            <SubSection title="Funding & Investment" content={report.financial_overview.funding_investment} />
                                            <SubSection title="Revenue Model" content={report.financial_overview.revenue_model} />
                                            <SubSection title="Financial Milestones" content={report.financial_overview.financial_milestones} />
                                        </div>
                                    </ReportSection>

                                    {/* News */}
                                    <ReportSection
                                        title="Recent News"
                                        icon={<Newspaper className="w-5 h-5" />}
                                        isExpanded={expandedSections.has('news')}
                                        onToggle={() => toggleSection('news')}
                                    >
                                        <div className="space-y-3">
                                            {report.news.map((item, idx) => (
                                                <div key={idx} className="p-4 bg-white/5 rounded-xl">
                                                    <h4 className="font-semibold text-white mb-2">{item.title}</h4>
                                                    <p className="text-sm text-slate-400">{item.content}</p>
                                                    {item.url && (
                                                        <a
                                                            href={item.url}
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                            className="inline-flex items-center gap-1 text-xs text-indigo-400 mt-2 hover:underline"
                                                        >
                                                            Read more <ExternalLink className="w-3 h-3" />
                                                        </a>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    </ReportSection>

                                    {/* References */}
                                    <div className="mt-6 pt-6 border-t border-white/10">
                                        <h3 className="text-lg font-semibold mb-4">References</h3>
                                        <ul className="space-y-2">
                                            {report.references.slice(0, 10).map((ref, idx) => (
                                                <li key={idx}>
                                                    <a
                                                        href={ref.url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="text-sm text-indigo-400 hover:underline flex items-center gap-2"
                                                    >
                                                        <ExternalLink className="w-3 h-3" />
                                                        {ref.title}
                                                    </a>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>

                                    {/* Research Stats */}
                                    <div className="mt-6 pt-6 border-t border-white/10">
                                        <button
                                            onClick={() => setShowQueries(!showQueries)}
                                            className="flex items-center gap-2 text-slate-400 hover:text-white transition"
                                        >
                                            {showQueries ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                                            View Research Queries & Stats
                                        </button>

                                        {showQueries && (
                                            <motion.div
                                                initial={{ opacity: 0, height: 0 }}
                                                animate={{ opacity: 1, height: 'auto' }}
                                                className="mt-4 grid md:grid-cols-2 gap-4"
                                            >
                                                {/* Stats */}
                                                <div className="p-4 bg-white/5 rounded-xl">
                                                    <h4 className="font-semibold mb-3">Curation Stats</h4>
                                                    <div className="grid grid-cols-2 gap-3">
                                                        {Object.entries(report.stats || {}).map(([key, value]) => (
                                                            <div key={key} className="p-3 bg-white/5 rounded-lg">
                                                                <p className="text-xs text-slate-400 capitalize">{key}</p>
                                                                <p className="text-sm font-semibold text-indigo-400">{value}</p>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>

                                                {/* Queries */}
                                                <div className="p-4 bg-white/5 rounded-xl">
                                                    <h4 className="font-semibold mb-3">Generated Queries</h4>
                                                    <div className="space-y-3 max-h-60 overflow-y-auto">
                                                        {Object.entries(report.queries || {}).map(([category, queries]) => (
                                                            <div key={category}>
                                                                <p className="text-xs text-indigo-400 uppercase mb-1">{category}</p>
                                                                <ul className="text-xs text-slate-400 space-y-1">
                                                                    {(queries as string[]).map((q, i) => (
                                                                        <li key={i} className="truncate">{q}</li>
                                                                    ))}
                                                                </ul>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            </motion.div>
                                        )}
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </main>

            {/* Email Modal */}
            <AnimatePresence>
                {showEmailModal && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-6"
                        onClick={() => setShowEmailModal(false)}
                    >
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            className="bg-slate-800 rounded-2xl p-6 w-full max-w-md border border-white/10"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <h3 className="text-xl font-bold mb-4">Send Report via Email</h3>
                            <input
                                type="email"
                                value={emailAddress}
                                onChange={(e) => setEmailAddress(e.target.value)}
                                placeholder="recipient@example.com"
                                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl mb-4
                                         text-white placeholder-slate-500 focus:border-indigo-500"
                            />
                            <div className="flex gap-3">
                                <button
                                    onClick={() => setShowEmailModal(false)}
                                    className="flex-1 py-3 bg-white/10 hover:bg-white/20 rounded-xl font-semibold transition"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={sendEmail}
                                    disabled={isEmailSending || !emailAddress}
                                    className="flex-1 py-3 bg-indigo-500 hover:bg-indigo-400 disabled:opacity-50 
                                             rounded-xl font-semibold transition flex items-center justify-center gap-2"
                                >
                                    {isEmailSending ? (
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                    ) : (
                                        <Mail className="w-4 h-4" />
                                    )}
                                    Send
                                </button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

// === SUB-COMPONENTS ===

function ReportSection({
    title,
    icon,
    isExpanded,
    onToggle,
    children
}: {
    title: string;
    icon: React.ReactNode;
    isExpanded: boolean;
    onToggle: () => void;
    children: React.ReactNode;
}) {
    return (
        <div className="border border-white/10 rounded-xl overflow-hidden">
            <button
                onClick={onToggle}
                className="w-full p-4 flex items-center justify-between bg-white/5 hover:bg-white/10 transition"
            >
                <div className="flex items-center gap-3">
                    <div className="text-indigo-400">{icon}</div>
                    <h3 className="text-lg font-semibold">{title}</h3>
                </div>
                {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
            </button>
            <AnimatePresence>
                {isExpanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="px-4 pb-4"
                    >
                        {children}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

function SubSection({ title, content }: { title: string; content: string }) {
    if (!content || content.length < 10) return null;

    return (
        <div className="mt-4">
            <h4 className="text-sm font-semibold text-indigo-300 mb-2">{title}</h4>
            <p className="text-sm text-slate-300 leading-relaxed">{content}</p>
        </div>
    );
}
