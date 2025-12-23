"use client"

import * as React from "react"
import { motion } from "framer-motion"
import { cn } from "./button"

interface ScoreGaugeProps {
    score: number
    maxScore?: number
    size?: "sm" | "md" | "lg"
    showLabel?: boolean
    label?: string
    className?: string
}

export function ScoreGauge({
    score,
    maxScore = 100,
    size = "md",
    showLabel = true,
    label = "EIS Score",
    className
}: ScoreGaugeProps) {
    const percentage = Math.min(100, Math.max(0, (score / maxScore) * 100))

    const getColor = () => {
        if (percentage >= 70) return { stroke: "#10b981", glow: "0 0 20px rgba(16, 185, 129, 0.5)" }
        if (percentage >= 50) return { stroke: "#f59e0b", glow: "0 0 20px rgba(245, 158, 11, 0.5)" }
        return { stroke: "#ef4444", glow: "0 0 20px rgba(239, 68, 68, 0.5)" }
    }

    const color = getColor()

    const sizes = {
        sm: { width: 80, strokeWidth: 6, fontSize: "text-lg" },
        md: { width: 120, strokeWidth: 8, fontSize: "text-2xl" },
        lg: { width: 160, strokeWidth: 10, fontSize: "text-4xl" },
    }

    const { width, strokeWidth, fontSize } = sizes[size]
    const radius = (width - strokeWidth) / 2
    const circumference = radius * 2 * Math.PI
    const offset = circumference - (percentage / 100) * circumference

    return (
        <div className={cn("flex flex-col items-center", className)}>
            <div className="relative" style={{ width, height: width }}>
                <svg width={width} height={width} className="-rotate-90">
                    {/* Background circle */}
                    <circle
                        cx={width / 2}
                        cy={width / 2}
                        r={radius}
                        fill="none"
                        stroke="rgba(51, 65, 85, 0.5)"
                        strokeWidth={strokeWidth}
                    />
                    {/* Animated progress circle */}
                    <motion.circle
                        cx={width / 2}
                        cy={width / 2}
                        r={radius}
                        fill="none"
                        stroke={color.stroke}
                        strokeWidth={strokeWidth}
                        strokeLinecap="round"
                        strokeDasharray={circumference}
                        initial={{ strokeDashoffset: circumference }}
                        animate={{ strokeDashoffset: offset }}
                        transition={{ duration: 1.2, ease: "easeOut" }}
                        style={{ filter: `drop-shadow(${color.glow})` }}
                    />
                </svg>
                {/* Center text */}
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <motion.span
                        className={cn("font-bold text-white", fontSize)}
                        initial={{ opacity: 0, scale: 0.5 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.5, delay: 0.5 }}
                    >
                        {score}
                    </motion.span>
                    <span className="text-xs text-slate-500">/{maxScore}</span>
                </div>
            </div>
            {showLabel && (
                <span className="mt-2 text-sm font-medium text-slate-400">{label}</span>
            )}
        </div>
    )
}
