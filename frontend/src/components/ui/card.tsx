"use client"

import * as React from "react"
import { motion, HTMLMotionProps } from "framer-motion"
import { cn } from "./button"

interface CardProps extends HTMLMotionProps<"div"> {
    variant?: "default" | "glass" | "gradient" | "glow" | "elevated"
    hover?: boolean
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
    ({ className, variant = "default", hover = true, children, ...props }, ref) => {
        const variants = {
            default: "bg-slate-900/80 border border-slate-800",
            glass: "bg-white/5 backdrop-blur-xl border border-white/10",
            gradient: "bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 border border-slate-700/50",
            glow: "bg-slate-900/90 border border-indigo-500/30 shadow-lg shadow-indigo-500/10",
            elevated: "bg-slate-900 border border-slate-800 shadow-2xl shadow-black/40",
        }

        return (
            <motion.div
                ref={ref}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, ease: "easeOut" }}
                whileHover={hover ? { scale: 1.01, y: -2 } : undefined}
                className={cn(
                    "rounded-xl p-6 transition-all duration-300",
                    variants[variant],
                    hover && "hover:border-slate-700 hover:shadow-xl",
                    className
                )}
                {...props}
            >
                {children}
            </motion.div>
        )
    }
)
Card.displayName = "Card"

const CardHeader = React.forwardRef<
    HTMLDivElement,
    React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
    <div
        ref={ref}
        className={cn("flex flex-col space-y-1.5 pb-4", className)}
        {...props}
    />
))
CardHeader.displayName = "CardHeader"

const CardTitle = React.forwardRef<
    HTMLParagraphElement,
    React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
    <h3
        ref={ref}
        className={cn("text-xl font-semibold leading-none tracking-tight text-white", className)}
        {...props}
    />
))
CardTitle.displayName = "CardTitle"

const CardDescription = React.forwardRef<
    HTMLParagraphElement,
    React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
    <p
        ref={ref}
        className={cn("text-sm text-slate-400", className)}
        {...props}
    />
))
CardDescription.displayName = "CardDescription"

const CardContent = React.forwardRef<
    HTMLDivElement,
    React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
    <div ref={ref} className={cn("pt-0", className)} {...props} />
))
CardContent.displayName = "CardContent"

const CardFooter = React.forwardRef<
    HTMLDivElement,
    React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
    <div
        ref={ref}
        className={cn("flex items-center pt-4 border-t border-slate-800", className)}
        {...props}
    />
))
CardFooter.displayName = "CardFooter"

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent }
