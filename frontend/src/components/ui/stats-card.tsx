"use client"

import * as React from "react"
import { motion } from "framer-motion"
import { cn } from "./button"
import { LucideIcon } from "lucide-react"

interface StatsCardProps {
    title: string
    value: string | number
    subtitle?: string
    icon?: LucideIcon
    trend?: {
        value: number
        label?: string
        positive?: boolean
    }
    variant?: "default" | "success" | "warning" | "danger" | "purple" | "cyan"
    className?: string
    delay?: number
}

export function StatsCard({
    title,
    value,
    subtitle,
    icon: Icon,
    trend,
    variant = "default",
    className,
    delay = 0
}: StatsCardProps) {
    const variants = {
        default: {
            bg: "bg-slate-900/80",
            border: "border-slate-800",
            iconBg: "bg-slate-800",
            iconColor: "text-slate-400"
        },
        success: {
            bg: "bg-emerald-950/30",
            border: "border-emerald-800/50",
            iconBg: "bg-emerald-500/20",
            iconColor: "text-emerald-400"
        },
        warning: {
            bg: "bg-amber-950/30",
            border: "border-amber-800/50",
            iconBg: "bg-amber-500/20",
            iconColor: "text-amber-400"
        },
        danger: {
            bg: "bg-red-950/30",
            border: "border-red-800/50",
            iconBg: "bg-red-500/20",
            iconColor: "text-red-400"
        },
        purple: {
            bg: "bg-purple-950/30",
            border: "border-purple-800/50",
            iconBg: "bg-purple-500/20",
            iconColor: "text-purple-400"
        },
        cyan: {
            bg: "bg-cyan-950/30",
            border: "border-cyan-800/50",
            iconBg: "bg-cyan-500/20",
            iconColor: "text-cyan-400"
        }
    }

    const style = variants[variant]

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay, ease: "easeOut" }}
            className={cn(
                "relative overflow-hidden rounded-xl border p-6 transition-all duration-300 hover:shadow-lg",
                style.bg,
                style.border,
                className
            )}
        >
            {/* Background gradient */}
            <div className="absolute inset-0 bg-gradient-to-br from-white/[0.02] to-transparent" />

            <div className="relative flex items-start justify-between">
                <div className="flex-1">
                    <p className="text-sm font-medium text-slate-400">{title}</p>
                    <motion.p
                        className="mt-2 text-3xl font-bold text-white"
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.4, delay: delay + 0.2 }}
                    >
                        {value}
                    </motion.p>
                    {subtitle && (
                        <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
                    )}
                    {trend && (
                        <div className={cn(
                            "mt-2 inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                            trend.positive ? "bg-emerald-500/15 text-emerald-400" : "bg-red-500/15 text-red-400"
                        )}>
                            <span>{trend.positive ? "+" : ""}{trend.value}%</span>
                            {trend.label && <span className="ml-1 text-slate-500">{trend.label}</span>}
                        </div>
                    )}
                </div>
                {Icon && (
                    <div className={cn("rounded-lg p-3", style.iconBg)}>
                        <Icon className={cn("h-6 w-6", style.iconColor)} />
                    </div>
                )}
            </div>
        </motion.div>
    )
}
