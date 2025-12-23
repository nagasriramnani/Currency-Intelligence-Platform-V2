"use client"

import React from "react"
import { motion } from "framer-motion"
import { cn } from "./button"
import { Badge } from "./badge"
import { ScoreGauge } from "./score-gauge"
import { Building2, MapPin, Calendar, Users, ExternalLink, Shield, AlertTriangle, CheckCircle2 } from "lucide-react"

interface EISCompanyCardProps {
    company: {
        company_number: string
        company_name: string
        company_status: string
        date_of_creation?: string
        jurisdiction: string
        registered_office_address?: Record<string, string>
        sic_codes?: string[]
    }
    assessment?: {
        score: number
        status: string
        flags?: string[]
    }
    isSelected?: boolean
    onClick?: () => void
    onViewDetails?: () => void
    delay?: number
}

export function EISCompanyCard({
    company,
    assessment,
    isSelected,
    onClick,
    onViewDetails,
    delay = 0
}: EISCompanyCardProps) {
    const getStatusBadge = () => {
        if (!assessment) return null

        if (assessment.status === "LIKELY_ELIGIBLE" || assessment.status === "Likely Eligible") {
            return <Badge variant="success">Likely Eligible</Badge>
        } else if (assessment.status === "GATED_OUT") {
            return <Badge variant="danger">Gated Out</Badge>
        } else {
            return <Badge variant="warning">Review Required</Badge>
        }
    }

    const formatAddress = () => {
        if (!company.registered_office_address) return "Address not available"
        const addr = company.registered_office_address
        return [addr.locality, addr.region, addr.postal_code].filter(Boolean).join(", ")
    }

    const getCompanyAge = () => {
        if (!company.date_of_creation) return null
        const created = new Date(company.date_of_creation)
        const now = new Date()
        const years = Math.floor((now.getTime() - created.getTime()) / (365.25 * 24 * 60 * 60 * 1000))
        return years
    }

    const age = getCompanyAge()

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay, ease: "easeOut" }}
            whileHover={{ scale: 1.01, y: -2 }}
            onClick={onClick}
            className={cn(
                "group relative overflow-hidden rounded-xl border p-5 transition-all duration-300 cursor-pointer",
                "bg-slate-900/80 hover:bg-slate-900",
                isSelected
                    ? "border-indigo-500 shadow-lg shadow-indigo-500/20"
                    : "border-slate-800 hover:border-slate-700"
            )}
        >
            {/* Background gradient */}
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

            <div className="relative flex items-start gap-4">
                {/* Score Gauge */}
                {assessment && (
                    <div className="flex-shrink-0">
                        <ScoreGauge
                            score={assessment.score}
                            size="sm"
                            showLabel={false}
                        />
                    </div>
                )}

                {/* Company Info */}
                <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-4">
                        <div>
                            <h3 className="font-semibold text-white truncate group-hover:text-indigo-300 transition-colors">
                                {company.company_name}
                            </h3>
                            <p className="text-sm text-slate-500 mt-0.5">
                                #{company.company_number}
                            </p>
                        </div>
                        {getStatusBadge()}
                    </div>

                    {/* Details */}
                    <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-slate-400">
                        <span className="inline-flex items-center gap-1.5">
                            <MapPin className="h-3.5 w-3.5" />
                            {formatAddress()}
                        </span>
                        {age !== null && (
                            <span className="inline-flex items-center gap-1.5">
                                <Calendar className="h-3.5 w-3.5" />
                                {age} years old
                            </span>
                        )}
                        {company.sic_codes && company.sic_codes.length > 0 && (
                            <span className="inline-flex items-center gap-1.5">
                                <Building2 className="h-3.5 w-3.5" />
                                SIC: {company.sic_codes[0]}
                            </span>
                        )}
                    </div>

                    {/* Flags */}
                    {assessment?.flags && assessment.flags.length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-2">
                            {assessment.flags.slice(0, 3).map((flag, i) => (
                                <span key={i} className="inline-flex items-center gap-1 text-xs text-amber-400">
                                    <AlertTriangle className="h-3 w-3" />
                                    {flag}
                                </span>
                            ))}
                        </div>
                    )}
                </div>

                {/* Action Button */}
                {onViewDetails && (
                    <button
                        onClick={(e) => {
                            e.stopPropagation()
                            onViewDetails()
                        }}
                        className="flex-shrink-0 p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                    >
                        <ExternalLink className="h-4 w-4" />
                    </button>
                )}
            </div>

            {/* Selection indicator */}
            {isSelected && (
                <motion.div
                    layoutId="company-selection"
                    className="absolute inset-0 rounded-xl ring-2 ring-indigo-500 ring-offset-2 ring-offset-slate-950 pointer-events-none"
                    initial={false}
                    transition={{ type: "spring", damping: 30, stiffness: 500 }}
                />
            )}
        </motion.div>
    )
}
