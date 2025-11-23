import React from 'react';
import { SectionHeader } from '@/components/SectionHeader';
import { Settings, Bell, Database, User, Palette } from 'lucide-react';

export default function SettingsPage() {
    return (
        <main className="mx-auto max-w-[1000px] px-4 py-8 sm:px-6 lg:px-8 space-y-8">
            <div className="flex flex-col gap-2">
                <h1 className="text-3xl font-bold tracking-tight text-white">
                    System <span className="text-sapphire-400">Settings</span>
                </h1>
                <p className="text-sapphire-200">
                    Manage your preferences, notifications, and data connections.
                </p>
            </div>

            <div className="space-y-6">
                {/* General Settings */}
                <section className="glass-panel p-6 rounded-2xl space-y-6">
                    <SectionHeader
                        title="General Preferences"
                        icon={Palette}
                        description="Customize the look and feel of the dashboard"
                    />

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-sapphire-100">Default Currency</label>
                            <select className="w-full rounded-lg bg-sapphire-900/50 border border-sapphire-700/50 px-4 py-2 text-white focus:border-sapphire-500 focus:ring-1 focus:ring-sapphire-500 outline-none">
                                <option value="USD">USD (United States Dollar)</option>
                                <option value="EUR">EUR (Euro)</option>
                                <option value="GBP">GBP (British Pound)</option>
                            </select>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-sapphire-100">Theme Accent</label>
                            <div className="flex gap-3">
                                <button className="h-8 w-8 rounded-full bg-sapphire-500 ring-2 ring-white ring-offset-2 ring-offset-sapphire-950"></button>
                                <button className="h-8 w-8 rounded-full bg-emerald-500"></button>
                                <button className="h-8 w-8 rounded-full bg-violet-500"></button>
                                <button className="h-8 w-8 rounded-full bg-rose-500"></button>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Notifications */}
                <section className="glass-panel p-6 rounded-2xl space-y-6">
                    <SectionHeader
                        title="Notifications"
                        icon={Bell}
                        description="Configure alerts and delivery channels"
                    />

                    <div className="space-y-4">
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-sapphire-100">Slack Webhook URL</label>
                            <input
                                type="password"
                                placeholder="https://hooks.slack.com/services/..."
                                className="w-full rounded-lg bg-sapphire-900/50 border border-sapphire-700/50 px-4 py-2 text-white focus:border-sapphire-500 focus:ring-1 focus:ring-sapphire-500 outline-none placeholder:text-sapphire-700"
                            />
                        </div>

                        <div className="flex items-center justify-between py-2">
                            <div className="space-y-0.5">
                                <label className="text-sm font-medium text-sapphire-100">Volatility Alerts</label>
                                <p className="text-xs text-sapphire-400">Notify when volatility exceeds 2 standard deviations</p>
                            </div>
                            <div className="h-6 w-11 rounded-full bg-sapphire-500 relative cursor-pointer">
                                <div className="absolute right-1 top-1 h-4 w-4 rounded-full bg-white shadow-sm"></div>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Data Sources */}
                <section className="glass-panel p-6 rounded-2xl space-y-6">
                    <SectionHeader
                        title="Data Sources"
                        icon={Database}
                        description="Manage API keys and connections"
                    />

                    <div className="space-y-4">
                        <div className="p-4 rounded-xl bg-sapphire-900/30 border border-sapphire-800/50 flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="h-2 w-2 rounded-full bg-emerald-500"></div>
                                <div>
                                    <p className="text-sm font-medium text-white">Financial Modeling Prep</p>
                                    <p className="text-xs text-sapphire-400">Connected • Free Tier</p>
                                </div>
                            </div>
                            <button className="text-xs font-medium text-sapphire-300 hover:text-white">Configure</button>
                        </div>

                        <div className="p-4 rounded-xl bg-sapphire-900/30 border border-sapphire-800/50 flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="h-2 w-2 rounded-full bg-emerald-500"></div>
                                <div>
                                    <p className="text-sm font-medium text-white">U.S. Treasury Fiscal Data</p>
                                    <p className="text-xs text-sapphire-400">Connected • Public API</p>
                                </div>
                            </div>
                            <button className="text-xs font-medium text-sapphire-300 hover:text-white">Configure</button>
                        </div>
                    </div>
                </section>
            </div>
        </main>
    );
}
