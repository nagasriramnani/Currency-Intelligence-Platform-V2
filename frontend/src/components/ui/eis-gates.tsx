"use client"

import React from "react"
import { motion } from "framer-motion"
import { cn } from "./button"
import { CheckCircle2, XCircle, AlertTriangle } from "lucide-react"

interface Gate {
    name: string
    passed: boolean
    reason?: string
}

interface GatesDisplayProps {
    gates: Gate[]
    className?: string
}

export function GatesDisplay({ gates, className }: GatesDisplayProps) {
    return (
        <div className={cn("space-y-3", className)}>
            <h4 className="text-sm font-medium text-slate-400 uppercase tracking-wider">
                Eligibility Gates
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {gates.map((gate, index) => (
                    <motion.div
                        key={gate.name}
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.3, delay: index * 0.1 }}
                        className={cn(
                            "relative overflow-hidden rounded-lg border p-4 transition-all duration-300",
                            gate.passed
                                ? "bg-emerald-950/30 border-emerald-800/50"
                                : "bg-red-950/30 border-red-800/50"
                        )}
                    >
                        <div className="flex items-start gap-3">
                            <div className={cn(
                                "flex-shrink-0 p-1.5 rounded-full",
                                gate.passed ? "bg-emerald-500/20" : "bg-red-500/20"
                            )}>
                                {gate.passed ? (
                                    <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                                ) : (
                                    <XCircle className="h-4 w-4 text-red-400" />
                                )}
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className={cn(
                                    "font-medium text-sm",
                                    gate.passed ? "text-emerald-300" : "text-red-300"
                                )}>
                                    {gate.name}
                                </p>
                                {gate.reason && (
                                    <p className="text-xs text-slate-500 mt-1 truncate">
                                        {gate.reason}
                                    </p>
                                )}
                            </div>
                        </div>

                        {/* Subtle background glow */}
                        <div className={cn(
                            "absolute inset-0 opacity-20 pointer-events-none",
                            gate.passed
                                ? "bg-gradient-to-r from-emerald-500/10 to-transparent"
                                : "bg-gradient-to-r from-red-500/10 to-transparent"
                        )} />
                    </motion.div>
                ))}
            </div>
        </div>
    )
}

interface ScoreBreakdownProps {
    breakdown: {
        factor: string
        points: number
        maxPoints: number
        rationale?: string
    }[]
    className?: string
}

export function ScoreBreakdown({ breakdown, className }: ScoreBreakdownProps) {
    return (
        <div className={cn("space-y-4", className)}>
            <h4 className="text-sm font-medium text-slate-400 uppercase tracking-wider">
                Score Breakdown
            </h4>
            <div className="space-y-3">
                {breakdown.map((factor, index) => {
                    const percentage = (factor.points / factor.maxPoints) * 100

                    return (
                        <motion.div
                            key={factor.factor}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.3, delay: index * 0.05 }}
                            className="group"
                        >
                            <div className="flex items-center justify-between mb-1.5">
                                <span className="text-sm text-slate-300">{factor.factor}</span>
                                <span className="text-sm font-medium text-white">
                                    {factor.points}/{factor.maxPoints}
                                </span>
                            </div>
                            <div className="relative h-2 bg-slate-800 rounded-full overflow-hidden">
                                <motion.div
                                    className={cn(
                                        "absolute inset-y-0 left-0 rounded-full",
                                        percentage >= 70
                                            ? "bg-gradient-to-r from-emerald-500 to-teal-500"
                                            : percentage >= 40
                                                ? "bg-gradient-to-r from-amber-500 to-orange-500"
                                                : "bg-gradient-to-r from-red-500 to-rose-500"
                                    )}
                                    initial={{ width: 0 }}
                                    animate={{ width: `${percentage}%` }}
                                    transition={{ duration: 0.8, delay: index * 0.1, ease: "easeOut" }}
                                />
                            </div>
                            {factor.rationale && (
                                <p className="text-xs text-slate-500 mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                    {factor.rationale}
                                </p>
                            )}
                        </motion.div>
                    )
                })}
            </div>
        </div>
    )
}
