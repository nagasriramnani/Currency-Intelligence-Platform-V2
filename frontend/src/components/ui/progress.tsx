"use client"

import * as React from "react"
import * as ProgressPrimitive from "@radix-ui/react-progress"
import { motion } from "framer-motion"
import { cn } from "./button"

interface ProgressProps extends React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root> {
    indicatorClassName?: string
    variant?: "default" | "success" | "warning" | "danger" | "gradient"
    showValue?: boolean
    animated?: boolean
}

const Progress = React.forwardRef<
    React.ElementRef<typeof ProgressPrimitive.Root>,
    ProgressProps
>(({ className, value, indicatorClassName, variant = "default", showValue, animated = true, ...props }, ref) => {
    const variants = {
        default: "bg-indigo-500",
        success: "bg-gradient-to-r from-emerald-500 to-teal-500",
        warning: "bg-gradient-to-r from-amber-500 to-orange-500",
        danger: "bg-gradient-to-r from-red-500 to-rose-500",
        gradient: "bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500",
    }

    return (
        <div className="relative">
            <ProgressPrimitive.Root
                ref={ref}
                className={cn(
                    "relative h-3 w-full overflow-hidden rounded-full bg-slate-800/80",
                    className
                )}
                {...props}
            >
                <motion.div
                    initial={animated ? { width: 0 } : undefined}
                    animate={{ width: `${value || 0}%` }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                    className={cn(
                        "h-full rounded-full shadow-lg transition-all",
                        variants[variant],
                        indicatorClassName
                    )}
                    style={{ width: animated ? undefined : `${value || 0}%` }}
                />
            </ProgressPrimitive.Root>
            {showValue && (
                <span className="absolute right-0 top-0 -translate-y-full mb-1 text-xs text-slate-400">
                    {value}%
                </span>
            )}
        </div>
    )
})
Progress.displayName = ProgressPrimitive.Root.displayName

export { Progress }
