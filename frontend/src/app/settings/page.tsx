'use client';

import React, { useState, useEffect } from 'react';
import { NavBar } from '@/components/NavBar';
import { CampingLoader } from '@/components/CampingLoader';
import { useTheme, AccentColor } from '@/lib/ThemeContext';
import { cn } from '@/lib/utils';
import {
    Settings,
    Bell,
    Database,
    User,
    Palette,
    Shield,
    Key,
    Globe,
    Clock,
    CheckCircle2,
    AlertCircle,
    Copy,
    Eye,
    EyeOff,
    RefreshCw,
    ChevronRight,
    Zap,
    Mail,
    Smartphone,
} from 'lucide-react';

// Sidebar navigation items
const navItems = [
    { id: 'general', label: 'General', icon: Settings, description: 'Preferences & display' },
    { id: 'appearance', label: 'Appearance', icon: Palette, description: 'Theme & colors' },
    { id: 'notifications', label: 'Notifications', icon: Bell, description: 'Alerts & channels' },
    { id: 'api', label: 'API Keys', icon: Key, description: 'Manage access' },
    { id: 'data', label: 'Data Sources', icon: Database, description: 'Connections' },
    { id: 'security', label: 'Security', icon: Shield, description: 'Privacy & access' },
];

const accentOptions: { color: AccentColor; bg: string; name: string; preview: string }[] = [
    { color: 'sapphire', bg: 'bg-blue-500', name: 'Sapphire', preview: 'from-blue-600 to-blue-400' },
    { color: 'emerald', bg: 'bg-emerald-500', name: 'Emerald', preview: 'from-emerald-600 to-emerald-400' },
    { color: 'violet', bg: 'bg-violet-500', name: 'Violet', preview: 'from-violet-600 to-violet-400' },
    { color: 'rose', bg: 'bg-rose-500', name: 'Rose', preview: 'from-rose-600 to-rose-400' },
];

const currencies = [
    { code: 'USD', name: 'US Dollar', symbol: '$' },
    { code: 'EUR', name: 'Euro', symbol: '€' },
    { code: 'GBP', name: 'British Pound', symbol: '£' },
    { code: 'JPY', name: 'Japanese Yen', symbol: '¥' },
    { code: 'CHF', name: 'Swiss Franc', symbol: 'Fr' },
];

// Toggle Switch Component
function Toggle({ enabled, onChange }: { enabled: boolean; onChange: (val: boolean) => void }) {
    return (
        <button
            onClick={() => onChange(!enabled)}
            className={cn(
                'relative h-6 w-11 rounded-full transition-all duration-300',
                enabled ? 'accent-bg' : 'bg-sapphire-800'
            )}
        >
            <div
                className={cn(
                    'absolute top-1 h-4 w-4 rounded-full bg-white shadow-sm transition-all duration-300',
                    enabled ? 'right-1' : 'left-1'
                )}
            />
        </button>
    );
}

// Setting Row Component
function SettingRow({
    title,
    description,
    children,
}: {
    title: string;
    description?: string;
    children: React.ReactNode;
}) {
    return (
        <div className="flex items-center justify-between py-4 border-b border-sapphire-800/50 last:border-0">
            <div className="space-y-0.5">
                <p className="text-sm font-medium text-white">{title}</p>
                {description && <p className="text-xs text-sapphire-400">{description}</p>}
            </div>
            <div>{children}</div>
        </div>
    );
}

// Data Source Card
function DataSourceCard({
    name,
    status,
    tier,
    lastSync,
}: {
    name: string;
    status: 'connected' | 'disconnected' | 'error';
    tier: string;
    lastSync?: string;
}) {
    const statusConfig = {
        connected: { color: 'bg-emerald-500', text: 'Connected', textColor: 'text-emerald-400' },
        disconnected: { color: 'bg-gray-500', text: 'Disconnected', textColor: 'text-gray-400' },
        error: { color: 'bg-red-500', text: 'Error', textColor: 'text-red-400' },
    };

    return (
        <div className="group p-4 rounded-xl bg-sapphire-900/30 border border-sapphire-800/50 hover:bg-sapphire-800/40 hover:border-sapphire-700/50 transition-all duration-300">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-lg bg-sapphire-800/50 flex items-center justify-center">
                        <Database className="h-5 w-5 text-sapphire-400" />
                    </div>
                    <div>
                        <p className="text-sm font-medium text-white">{name}</p>
                        <div className="flex items-center gap-2 mt-0.5">
                            <div className={cn('h-2 w-2 rounded-full', statusConfig[status].color)} />
                            <span className={cn('text-xs', statusConfig[status].textColor)}>
                                {statusConfig[status].text}
                            </span>
                            <span className="text-xs text-sapphire-600">•</span>
                            <span className="text-xs text-sapphire-400">{tier}</span>
                        </div>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    {lastSync && (
                        <span className="text-xs text-sapphire-500">
                            <Clock className="h-3 w-3 inline mr-1" />
                            {lastSync}
                        </span>
                    )}
                    <button className="px-3 py-1.5 text-xs font-medium text-sapphire-300 hover:text-white hover:bg-sapphire-700/50 rounded-lg transition-all">
                        Configure
                    </button>
                </div>
            </div>
        </div>
    );
}

// API Key Row
function APIKeyRow({ name, keyPreview, created }: { name: string; keyPreview: string; created: string }) {
    const [visible, setVisible] = useState(false);
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="group p-4 rounded-xl bg-sapphire-900/30 border border-sapphire-800/50 hover:bg-sapphire-800/40 transition-all duration-300">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-lg bg-sapphire-800/50 flex items-center justify-center">
                        <Key className="h-5 w-5 text-sapphire-400" />
                    </div>
                    <div>
                        <p className="text-sm font-medium text-white">{name}</p>
                        <div className="flex items-center gap-2 mt-1">
                            <code className="text-xs font-mono text-sapphire-400 bg-sapphire-900/50 px-2 py-0.5 rounded">
                                {visible ? keyPreview : '••••••••••••••••'}
                            </code>
                        </div>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-xs text-sapphire-500">Created {created}</span>
                    <button
                        onClick={() => setVisible(!visible)}
                        className="p-2 text-sapphire-400 hover:text-white hover:bg-sapphire-700/50 rounded-lg transition-all"
                    >
                        {visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                    <button
                        onClick={handleCopy}
                        className="p-2 text-sapphire-400 hover:text-white hover:bg-sapphire-700/50 rounded-lg transition-all"
                    >
                        {copied ? <CheckCircle2 className="h-4 w-4 text-emerald-400" /> : <Copy className="h-4 w-4" />}
                    </button>
                </div>
            </div>
        </div>
    );
}

export default function SettingsPage() {
    const { accentColor, setAccentColor } = useTheme();
    const [activeSection, setActiveSection] = useState('general');
    const [showLoader, setShowLoader] = useState(true);

    // Settings state
    const [defaultCurrency, setDefaultCurrency] = useState('USD');
    const [timezone, setTimezone] = useState('America/New_York');
    const [volatilityAlerts, setVolatilityAlerts] = useState(true);
    const [emailAlerts, setEmailAlerts] = useState(false);
    const [pushAlerts, setPushAlerts] = useState(true);
    const [dailyDigest, setDailyDigest] = useState(true);
    const [twoFactor, setTwoFactor] = useState(false);

    useEffect(() => {
        const timer = setTimeout(() => setShowLoader(false), 3500);
        return () => clearTimeout(timer);
    }, []);

    if (showLoader) {
        return <CampingLoader />;
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-sapphire-950 via-sapphire-900 to-sapphire-950">
            <NavBar />

            <main className="container mx-auto px-4 py-8">
                {/* Page Header */}
                <div className="mb-8 animate-fade-in-up">
                    <h1 className="text-3xl font-bold tracking-tight text-white">
                        Settings
                    </h1>
                    <p className="text-sapphire-300 mt-1">
                        Manage your account preferences and platform configuration
                    </p>
                </div>

                {/* Main Layout - Sidebar + Content */}
                <div className="flex gap-8">
                    {/* Sidebar Navigation */}
                    <aside className="w-64 flex-shrink-0 animate-fade-in-up">
                        <nav className="sticky top-8 space-y-1">
                            {navItems.map((item) => (
                                <button
                                    key={item.id}
                                    onClick={() => setActiveSection(item.id)}
                                    className={cn(
                                        'w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-all duration-300 group',
                                        activeSection === item.id
                                            ? 'accent-bg-subtle text-white shadow-lg accent-glow-sm'
                                            : 'text-sapphire-300 hover:bg-sapphire-800/30 hover:text-white'
                                    )}
                                >
                                    <div
                                        className={cn(
                                            'h-9 w-9 rounded-lg flex items-center justify-center transition-all',
                                            activeSection === item.id
                                                ? 'accent-bg text-white'
                                                : 'bg-sapphire-800/50 text-sapphire-400 group-hover:bg-sapphire-700/50'
                                        )}
                                    >
                                        <item.icon className="h-5 w-5" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="font-medium text-sm">{item.label}</p>
                                        <p className="text-xs text-sapphire-500 truncate">{item.description}</p>
                                    </div>
                                    <ChevronRight
                                        className={cn(
                                            'h-4 w-4 transition-all',
                                            activeSection === item.id ? 'opacity-100' : 'opacity-0 group-hover:opacity-50'
                                        )}
                                    />
                                </button>
                            ))}
                        </nav>
                    </aside>

                    {/* Content Area */}
                    <div className="flex-1 min-w-0 animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
                        <div className="glass-panel rounded-2xl p-8 space-y-8">
                            {/* General Settings */}
                            {activeSection === 'general' && (
                                <div className="space-y-6">
                                    <div className="border-b border-sapphire-800/50 pb-4">
                                        <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                                            <Settings className="h-5 w-5 text-sapphire-400" />
                                            General Settings
                                        </h2>
                                        <p className="text-sm text-sapphire-400 mt-1">
                                            Configure your default preferences
                                        </p>
                                    </div>

                                    <SettingRow title="Default Currency" description="Base currency for all calculations">
                                        <select
                                            value={defaultCurrency}
                                            onChange={(e) => setDefaultCurrency(e.target.value)}
                                            className="px-4 py-2 rounded-lg bg-sapphire-800/50 border border-sapphire-700/50 text-white text-sm focus:border-sapphire-500 focus:ring-1 focus:ring-sapphire-500 outline-none cursor-pointer"
                                        >
                                            {currencies.map((c) => (
                                                <option key={c.code} value={c.code} className="bg-sapphire-900">
                                                    {c.symbol} {c.code} - {c.name}
                                                </option>
                                            ))}
                                        </select>
                                    </SettingRow>

                                    <SettingRow title="Timezone" description="For scheduled reports and alerts">
                                        <select
                                            value={timezone}
                                            onChange={(e) => setTimezone(e.target.value)}
                                            className="px-4 py-2 rounded-lg bg-sapphire-800/50 border border-sapphire-700/50 text-white text-sm focus:border-sapphire-500 focus:ring-1 focus:ring-sapphire-500 outline-none cursor-pointer"
                                        >
                                            <option value="America/New_York" className="bg-sapphire-900">Eastern Time (ET)</option>
                                            <option value="America/Chicago" className="bg-sapphire-900">Central Time (CT)</option>
                                            <option value="America/Los_Angeles" className="bg-sapphire-900">Pacific Time (PT)</option>
                                            <option value="Europe/London" className="bg-sapphire-900">London (GMT)</option>
                                            <option value="Europe/Paris" className="bg-sapphire-900">Central European (CET)</option>
                                            <option value="Asia/Tokyo" className="bg-sapphire-900">Japan (JST)</option>
                                        </select>
                                    </SettingRow>

                                    <SettingRow title="Language" description="Interface language">
                                        <select className="px-4 py-2 rounded-lg bg-sapphire-800/50 border border-sapphire-700/50 text-white text-sm focus:border-sapphire-500 outline-none cursor-pointer">
                                            <option className="bg-sapphire-900">English (US)</option>
                                            <option className="bg-sapphire-900">English (UK)</option>
                                            <option className="bg-sapphire-900">Español</option>
                                            <option className="bg-sapphire-900">Français</option>
                                            <option className="bg-sapphire-900">Deutsch</option>
                                        </select>
                                    </SettingRow>
                                </div>
                            )}

                            {/* Appearance Settings */}
                            {activeSection === 'appearance' && (
                                <div className="space-y-6">
                                    <div className="border-b border-sapphire-800/50 pb-4">
                                        <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                                            <Palette className="h-5 w-5 text-sapphire-400" />
                                            Appearance
                                        </h2>
                                        <p className="text-sm text-sapphire-400 mt-1">
                                            Customize the look and feel
                                        </p>
                                    </div>

                                    <div className="space-y-4">
                                        <p className="text-sm font-medium text-white">Theme Accent Color</p>
                                        <div className="grid grid-cols-2 gap-4">
                                            {accentOptions.map((option) => (
                                                <button
                                                    key={option.color}
                                                    onClick={() => setAccentColor(option.color)}
                                                    className={cn(
                                                        'p-4 rounded-xl border-2 transition-all duration-300 group',
                                                        accentColor === option.color
                                                            ? 'border-white bg-sapphire-800/50'
                                                            : 'border-sapphire-700/50 hover:border-sapphire-600 bg-sapphire-900/30'
                                                    )}
                                                >
                                                    <div className="flex items-center gap-3">
                                                        <div
                                                            className={cn(
                                                                'h-10 w-10 rounded-lg bg-gradient-to-br',
                                                                option.preview
                                                            )}
                                                        />
                                                        <div className="text-left">
                                                            <p className="text-sm font-medium text-white">{option.name}</p>
                                                            <p className="text-xs text-sapphire-400">
                                                                {accentColor === option.color ? 'Active' : 'Click to apply'}
                                                            </p>
                                                        </div>
                                                        {accentColor === option.color && (
                                                            <CheckCircle2 className="h-5 w-5 text-emerald-400 ml-auto" />
                                                        )}
                                                    </div>
                                                </button>
                                            ))}
                                        </div>
                                    </div>

                                    <SettingRow title="Compact Mode" description="Reduce spacing for more data density">
                                        <Toggle enabled={false} onChange={() => { }} />
                                    </SettingRow>

                                    <SettingRow title="Animations" description="Enable micro-animations and transitions">
                                        <Toggle enabled={true} onChange={() => { }} />
                                    </SettingRow>
                                </div>
                            )}

                            {/* Notifications */}
                            {activeSection === 'notifications' && (
                                <div className="space-y-6">
                                    <div className="border-b border-sapphire-800/50 pb-4">
                                        <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                                            <Bell className="h-5 w-5 text-sapphire-400" />
                                            Notifications
                                        </h2>
                                        <p className="text-sm text-sapphire-400 mt-1">
                                            Configure alerts and delivery preferences
                                        </p>
                                    </div>

                                    <div className="space-y-2">
                                        <p className="text-sm font-medium text-white">Alert Types</p>
                                        <div className="space-y-1">
                                            <SettingRow
                                                title="Volatility Alerts"
                                                description="When volatility exceeds 2 standard deviations"
                                            >
                                                <Toggle enabled={volatilityAlerts} onChange={setVolatilityAlerts} />
                                            </SettingRow>
                                            <SettingRow
                                                title="Price Alerts"
                                                description="When currencies hit target prices"
                                            >
                                                <Toggle enabled={true} onChange={() => { }} />
                                            </SettingRow>
                                            <SettingRow
                                                title="Forecast Updates"
                                                description="When new forecasts are generated"
                                            >
                                                <Toggle enabled={true} onChange={() => { }} />
                                            </SettingRow>
                                        </div>
                                    </div>

                                    <div className="space-y-2">
                                        <p className="text-sm font-medium text-white">Delivery Channels</p>
                                        <div className="space-y-1">
                                            <SettingRow title="Email Notifications" description="Send to your registered email">
                                                <Toggle enabled={emailAlerts} onChange={setEmailAlerts} />
                                            </SettingRow>
                                            <SettingRow title="Push Notifications" description="Browser notifications">
                                                <Toggle enabled={pushAlerts} onChange={setPushAlerts} />
                                            </SettingRow>
                                            <SettingRow title="Daily Digest" description="Summary email at 8:00 AM">
                                                <Toggle enabled={dailyDigest} onChange={setDailyDigest} />
                                            </SettingRow>
                                        </div>
                                    </div>

                                    <div className="space-y-3">
                                        <p className="text-sm font-medium text-white">Slack Integration</p>
                                        <div className="flex gap-3">
                                            <input
                                                type="password"
                                                placeholder="https://hooks.slack.com/services/..."
                                                className="flex-1 px-4 py-2.5 rounded-lg bg-sapphire-900/50 border border-sapphire-700/50 text-white text-sm focus:border-sapphire-500 focus:ring-1 focus:ring-sapphire-500 outline-none placeholder:text-sapphire-600"
                                            />
                                            <button className="px-4 py-2.5 accent-bg hover:opacity-90 text-white text-sm font-medium rounded-lg transition-all">
                                                Test
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* API Keys */}
                            {activeSection === 'api' && (
                                <div className="space-y-6">
                                    <div className="border-b border-sapphire-800/50 pb-4 flex items-center justify-between">
                                        <div>
                                            <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                                                <Key className="h-5 w-5 text-sapphire-400" />
                                                API Keys
                                            </h2>
                                            <p className="text-sm text-sapphire-400 mt-1">
                                                Manage your API access tokens
                                            </p>
                                        </div>
                                        <button className="px-4 py-2 accent-bg hover:opacity-90 text-white text-sm font-medium rounded-lg transition-all flex items-center gap-2">
                                            <Zap className="h-4 w-4" />
                                            Generate New Key
                                        </button>
                                    </div>

                                    <div className="space-y-3">
                                        <APIKeyRow
                                            name="FMP API Key"
                                            keyPreview="feR1xfEjL8WCnhCA2rUfqylekBsAphGp"
                                            created="Dec 14, 2025"
                                        />
                                        <APIKeyRow
                                            name="Slack Webhook URL"
                                            keyPreview="T09UZQP59C1/B09V19GAJ0H/qW7z8E..."
                                            created="Dec 14, 2025"
                                        />
                                        <APIKeyRow
                                            name="Supabase URL"
                                            keyPreview="https://eepxywpskwjijxbroeoi.supabase.co"
                                            created="Dec 14, 2025"
                                        />
                                        <APIKeyRow
                                            name="Supabase Anon Key"
                                            keyPreview="eyJhbGciOiJIUzI1NiIsInR5cCI6..."
                                            created="Dec 14, 2025"
                                        />
                                    </div>

                                    <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20">
                                        <div className="flex gap-3">
                                            <AlertCircle className="h-5 w-5 text-amber-400 flex-shrink-0 mt-0.5" />
                                            <div>
                                                <p className="text-sm font-medium text-amber-300">Security Notice</p>
                                                <p className="text-xs text-amber-200/70 mt-1">
                                                    Keep your API keys secure. Never share them or commit them to version control.
                                                    Rotate keys regularly for enhanced security.
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Data Sources */}
                            {activeSection === 'data' && (
                                <div className="space-y-6">
                                    <div className="border-b border-sapphire-800/50 pb-4">
                                        <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                                            <Database className="h-5 w-5 text-sapphire-400" />
                                            Data Sources
                                        </h2>
                                        <p className="text-sm text-sapphire-400 mt-1">
                                            Manage external data connections
                                        </p>
                                    </div>

                                    <div className="space-y-3">
                                        <DataSourceCard
                                            name="Financial Modeling Prep"
                                            status="connected"
                                            tier="Free Tier"
                                            lastSync="2 min ago"
                                        />
                                        <DataSourceCard
                                            name="U.S. Treasury Fiscal Data"
                                            status="connected"
                                            tier="Public API"
                                            lastSync="5 min ago"
                                        />
                                    </div>

                                    <button className="w-full py-3 border-2 border-dashed border-sapphire-700/50 rounded-xl text-sapphire-400 hover:text-white hover:border-sapphire-600 transition-all flex items-center justify-center gap-2">
                                        <Globe className="h-4 w-4" />
                                        Add New Data Source
                                    </button>
                                </div>
                            )}

                            {/* Security */}
                            {activeSection === 'security' && (
                                <div className="space-y-6">
                                    <div className="border-b border-sapphire-800/50 pb-4">
                                        <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                                            <Shield className="h-5 w-5 text-sapphire-400" />
                                            Security
                                        </h2>
                                        <p className="text-sm text-sapphire-400 mt-1">
                                            Protect your account
                                        </p>
                                    </div>

                                    <SettingRow
                                        title="Two-Factor Authentication"
                                        description="Add an extra layer of security"
                                    >
                                        <Toggle enabled={twoFactor} onChange={setTwoFactor} />
                                    </SettingRow>

                                    <SettingRow
                                        title="Session Timeout"
                                        description="Auto-logout after inactivity"
                                    >
                                        <select className="px-4 py-2 rounded-lg bg-sapphire-800/50 border border-sapphire-700/50 text-white text-sm focus:border-sapphire-500 outline-none cursor-pointer">
                                            <option className="bg-sapphire-900">15 minutes</option>
                                            <option className="bg-sapphire-900">30 minutes</option>
                                            <option className="bg-sapphire-900">1 hour</option>
                                            <option className="bg-sapphire-900">4 hours</option>
                                        </select>
                                    </SettingRow>

                                    <div className="space-y-3">
                                        <p className="text-sm font-medium text-white">Recent Activity</p>
                                        <div className="space-y-2">
                                            {[
                                                { action: 'Login from Chrome on Windows', time: '2 hours ago', ip: '192.168.1.1' },
                                                { action: 'API key generated', time: '3 days ago', ip: '192.168.1.1' },
                                                { action: 'Password changed', time: '1 week ago', ip: '10.0.0.5' },
                                            ].map((activity, i) => (
                                                <div key={i} className="flex items-center justify-between py-2 text-sm">
                                                    <span className="text-sapphire-200">{activity.action}</span>
                                                    <div className="flex items-center gap-4 text-sapphire-500">
                                                        <span>{activity.time}</span>
                                                        <code className="text-xs bg-sapphire-900/50 px-2 py-0.5 rounded">
                                                            {activity.ip}
                                                        </code>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    <button className="px-4 py-2.5 bg-danger/10 hover:bg-danger/20 text-danger text-sm font-medium rounded-lg transition-all border border-danger/20">
                                        Sign Out All Devices
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
