"use client"

import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "./button"

const badgeVariants = cva(
    "inline-flex items-center rounded-full px-3 py-1 text-xs font-medium transition-all duration-200",
    {
        variants: {
            variant: {
                default: "bg-slate-800 text-slate-200 border border-slate-700",
                success: "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30",
                warning: "bg-amber-500/15 text-amber-400 border border-amber-500/30",
                danger: "bg-red-500/15 text-red-400 border border-red-500/30",
                info: "bg-blue-500/15 text-blue-400 border border-blue-500/30",
                purple: "bg-purple-500/15 text-purple-400 border border-purple-500/30",
                gradient: "bg-gradient-to-r from-indigo-500/20 to-purple-500/20 text-indigo-300 border border-indigo-500/30",
                glow: "bg-cyan-500/15 text-cyan-400 border border-cyan-400/40 shadow-sm shadow-cyan-500/20",
                outline: "border-2 border-slate-600 text-slate-300 bg-transparent",
            },
            size: {
                sm: "px-2 py-0.5 text-[10px]",
                default: "px-3 py-1 text-xs",
                lg: "px-4 py-1.5 text-sm",
            }
        },
        defaultVariants: {
            variant: "default",
            size: "default",
        },
    }
)

export interface BadgeProps
    extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {
    pulse?: boolean
}

function Badge({ className, variant, size, pulse, children, ...props }: BadgeProps) {
    return (
        <div
            className={cn(
                badgeVariants({ variant, size }),
                pulse && "animate-pulse",
                className
            )}
            {...props}
        >
            {children}
        </div>
    )
}

export { Badge, badgeVariants }
