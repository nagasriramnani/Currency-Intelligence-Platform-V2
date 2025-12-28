'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Send,
    Bot,
    User,
    ArrowLeft,
    Trash2,
    Loader2,
    AlertCircle,
    Sparkles,
    MessageSquare,
    Building2,
    TrendingUp,
    Newspaper,
    HelpCircle
} from 'lucide-react';
import Link from 'next/link';

interface Message {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: Date;
}

interface AdvisorStatus {
    available: boolean;
    model?: string;
    message?: string;
}

const EXAMPLE_QUESTIONS = [
    { icon: Building2, text: "What makes a company EIS eligible?", category: "EIS Rules" },
    { icon: TrendingUp, text: "Analyze my portfolio companies", category: "Portfolio" },
    { icon: Newspaper, text: "What's the latest in UK fintech?", category: "Sector News" },
    { icon: HelpCircle, text: "What is the capital of France?", category: "General" },
];

export default function AdvisorPage() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [status, setStatus] = useState<AdvisorStatus | null>(null);
    const [portfolio, setPortfolio] = useState<any[]>([]);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    // Check advisor status on mount
    useEffect(() => {
        checkStatus();
        loadPortfolio();

        // Add welcome message
        setMessages([{
            id: 'welcome',
            role: 'assistant',
            content: `👋 Welcome to the EIS Advisor!

I'm your AI assistant for Enterprise Investment Scheme questions. I can help you with:

📊 **EIS Eligibility** - Understanding the rules and scoring
🏢 **Company Analysis** - Analyzing companies for EIS qualification
📰 **Market News** - Latest UK startup and sector news
💼 **Portfolio Review** - Insights on your saved companies
❓ **General Questions** - I have general knowledge too!

What would you like to know?`,
            timestamp: new Date()
        }]);
    }, []);

    // Scroll to bottom on new messages
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const checkStatus = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/eis/advisor/status');
            const data = await response.json();
            setStatus(data);
        } catch (error) {
            setStatus({ available: false, message: 'Could not connect to backend' });
        }
    };

    const loadPortfolio = () => {
        try {
            const saved = localStorage.getItem('eis_portfolios');
            const selectedSlot = localStorage.getItem('eis_selected_slot') || '1';
            if (saved) {
                const portfolios = JSON.parse(saved);
                const currentPortfolio = portfolios[selectedSlot] || [];
                setPortfolio(currentPortfolio);
            }
        } catch (error) {
            console.error('Failed to load portfolio:', error);
        }
    };

    const sendMessage = async (question?: string) => {
        const messageText = question || input.trim();
        if (!messageText || isLoading) return;

        // Add user message
        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: messageText,
            timestamp: new Date()
        };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const response = await fetch('http://localhost:8000/api/eis/advisor/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: messageText,
                    portfolio: portfolio
                })
            });

            const data = await response.json();

            const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: data.response || 'Sorry, I could not generate a response.',
                timestamp: new Date()
            };
            setMessages(prev => [...prev, assistantMessage]);

            if (!data.available) {
                setStatus({ available: false, message: data.response });
            }
        } catch (error) {
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: '⚠️ Could not connect to the advisor. Please ensure the backend is running.',
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
            inputRef.current?.focus();
        }
    };

    const clearChat = async () => {
        try {
            await fetch('http://localhost:8000/api/eis/advisor/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: '',
                    portfolio: [],
                    clear_history: true
                })
            });
        } catch (error) {
            console.error('Failed to clear history:', error);
        }

        setMessages([{
            id: 'welcome-new',
            role: 'assistant',
            content: '🔄 Chat cleared. How can I help you?',
            timestamp: new Date()
        }]);
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
            {/* Header */}
            <header className="fixed top-0 left-0 right-0 z-50 bg-slate-900/80 backdrop-blur-xl border-b border-slate-800">
                <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link
                            href="/eis"
                            className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors"
                        >
                            <ArrowLeft className="h-5 w-5" />
                            <span>Back to EIS</span>
                        </Link>
                        <div className="h-6 w-px bg-slate-700" />
                        <div className="flex items-center gap-2">
                            <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500">
                                <Bot className="h-5 w-5 text-white" />
                            </div>
                            <div>
                                <h1 className="text-lg font-semibold text-white">EIS Advisor</h1>
                                <p className="text-xs text-slate-400">Powered by Ollama</p>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        {/* Status indicator */}
                        <div className="flex items-center gap-2">
                            <div className={`h-2 w-2 rounded-full ${status?.available ? 'bg-green-500' : 'bg-red-500'}`} />
                            <span className="text-sm text-slate-400">
                                {status?.available ? 'Online' : 'Offline'}
                            </span>
                        </div>

                        {/* Portfolio count */}
                        {portfolio.length > 0 && (
                            <div className="text-sm text-slate-400">
                                📊 {portfolio.length} companies loaded
                            </div>
                        )}

                        {/* Clear chat button */}
                        <button
                            onClick={clearChat}
                            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
                        >
                            <Trash2 className="h-4 w-4" />
                            <span className="text-sm">Clear</span>
                        </button>
                    </div>
                </div>
            </header>

            {/* Main Chat Area */}
            <main className="pt-20 pb-32 max-w-4xl mx-auto px-6">
                {/* Status Warning */}
                {!status?.available && status !== null && (
                    <motion.div
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mb-6 p-4 rounded-xl bg-amber-500/10 border border-amber-500/20"
                    >
                        <div className="flex items-start gap-3">
                            <AlertCircle className="h-5 w-5 text-amber-500 mt-0.5" />
                            <div>
                                <h3 className="font-medium text-amber-500">Ollama Not Available</h3>
                                <p className="text-sm text-amber-500/80 mt-1">
                                    Please ensure Ollama is running with llama3.2 model installed.
                                </p>
                                <code className="text-xs text-amber-400 bg-amber-500/10 px-2 py-1 rounded mt-2 inline-block">
                                    ollama pull llama3.2
                                </code>
                            </div>
                        </div>
                    </motion.div>
                )}

                {/* Messages */}
                <div className="space-y-6">
                    <AnimatePresence>
                        {messages.map((message) => (
                            <motion.div
                                key={message.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                className={`flex gap-4 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                            >
                                {message.role === 'assistant' && (
                                    <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                                        <Bot className="h-5 w-5 text-white" />
                                    </div>
                                )}

                                <div className={`max-w-[80%] rounded-2xl px-5 py-4 ${message.role === 'user'
                                        ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white'
                                        : 'bg-slate-800/80 text-slate-200 border border-slate-700/50'
                                    }`}>
                                    <div className="whitespace-pre-wrap text-sm leading-relaxed">
                                        {message.content}
                                    </div>
                                    <div className={`text-xs mt-2 ${message.role === 'user' ? 'text-blue-200' : 'text-slate-500'
                                        }`}>
                                        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                    </div>
                                </div>

                                {message.role === 'user' && (
                                    <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center">
                                        <User className="h-5 w-5 text-white" />
                                    </div>
                                )}
                            </motion.div>
                        ))}
                    </AnimatePresence>

                    {/* Loading indicator */}
                    {isLoading && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="flex gap-4"
                        >
                            <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                                <Bot className="h-5 w-5 text-white" />
                            </div>
                            <div className="bg-slate-800/80 rounded-2xl px-5 py-4 border border-slate-700/50">
                                <div className="flex items-center gap-2 text-slate-400">
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                    <span className="text-sm">Thinking...</span>
                                </div>
                            </div>
                        </motion.div>
                    )}

                    <div ref={messagesEndRef} />
                </div>

                {/* Example Questions (show when few messages) */}
                {messages.length <= 1 && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                        className="mt-8"
                    >
                        <p className="text-sm text-slate-500 mb-4">Try asking:</p>
                        <div className="grid grid-cols-2 gap-3">
                            {EXAMPLE_QUESTIONS.map((example, i) => (
                                <button
                                    key={i}
                                    onClick={() => sendMessage(example.text)}
                                    className="flex items-center gap-3 p-4 rounded-xl bg-slate-800/50 border border-slate-700/50 hover:bg-slate-800 hover:border-purple-500/30 transition-all text-left group"
                                >
                                    <div className="p-2 rounded-lg bg-slate-700/50 group-hover:bg-purple-500/20 transition-colors">
                                        <example.icon className="h-4 w-4 text-slate-400 group-hover:text-purple-400" />
                                    </div>
                                    <div>
                                        <p className="text-sm text-slate-300">{example.text}</p>
                                        <p className="text-xs text-slate-500">{example.category}</p>
                                    </div>
                                </button>
                            ))}
                        </div>
                    </motion.div>
                )}
            </main>

            {/* Input Area */}
            <div className="fixed bottom-0 left-0 right-0 bg-gradient-to-t from-slate-950 via-slate-950 to-transparent pt-8 pb-6">
                <div className="max-w-4xl mx-auto px-6">
                    <div className="flex items-center gap-3 p-2 rounded-2xl bg-slate-800/80 border border-slate-700/50 backdrop-blur-xl">
                        <div className="flex-shrink-0 pl-2">
                            <Sparkles className="h-5 w-5 text-purple-400" />
                        </div>
                        <input
                            ref={inputRef}
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder="Ask about EIS eligibility, companies, or anything else..."
                            className="flex-grow bg-transparent text-white placeholder-slate-500 text-sm py-3 outline-none"
                            disabled={isLoading}
                        />
                        <button
                            onClick={() => sendMessage()}
                            disabled={!input.trim() || isLoading}
                            className="flex-shrink-0 p-3 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                        >
                            {isLoading ? (
                                <Loader2 className="h-5 w-5 text-white animate-spin" />
                            ) : (
                                <Send className="h-5 w-5 text-white" />
                            )}
                        </button>
                    </div>
                    <p className="text-center text-xs text-slate-600 mt-3">
                        EIS Advisor can make mistakes. Verify important information.
                    </p>
                </div>
            </div>
        </div>
    );
}
