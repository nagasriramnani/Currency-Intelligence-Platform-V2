"use client"

import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "./button"

interface AnimatedListProps {
    children: React.ReactNode
    className?: string
    staggerDelay?: number
}

export function AnimatedList({ children, className, staggerDelay = 0.1 }: AnimatedListProps) {
    return (
        <motion.div
            initial="hidden"
            animate="visible"
            variants={{
                hidden: { opacity: 0 },
                visible: {
                    opacity: 1,
                    transition: {
                        staggerChildren: staggerDelay
                    }
                }
            }}
            className={className}
        >
            {children}
        </motion.div>
    )
}

interface AnimatedListItemProps {
    children: React.ReactNode
    className?: string
}

export function AnimatedListItem({ children, className }: AnimatedListItemProps) {
    return (
        <motion.div
            variants={{
                hidden: { opacity: 0, x: -20 },
                visible: { opacity: 1, x: 0 }
            }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className={className}
        >
            {children}
        </motion.div>
    )
}

interface FadeInProps {
    children: React.ReactNode
    className?: string
    delay?: number
    direction?: "up" | "down" | "left" | "right"
}

export function FadeIn({ children, className, delay = 0, direction = "up" }: FadeInProps) {
    const directionOffset = {
        up: { y: 20 },
        down: { y: -20 },
        left: { x: 20 },
        right: { x: -20 }
    }

    return (
        <motion.div
            initial={{ opacity: 0, ...directionOffset[direction] }}
            animate={{ opacity: 1, x: 0, y: 0 }}
            transition={{ duration: 0.5, delay, ease: "easeOut" }}
            className={className}
        >
            {children}
        </motion.div>
    )
}

interface SlideInProps {
    children: React.ReactNode
    className?: string
    show?: boolean
    direction?: "left" | "right" | "top" | "bottom"
}

export function SlideIn({ children, className, show = true, direction = "right" }: SlideInProps) {
    const directionVariants = {
        left: { x: -300 },
        right: { x: 300 },
        top: { y: -300 },
        bottom: { y: 300 }
    }

    return (
        <AnimatePresence>
            {show && (
                <motion.div
                    initial={{ opacity: 0, ...directionVariants[direction] }}
                    animate={{ opacity: 1, x: 0, y: 0 }}
                    exit={{ opacity: 0, ...directionVariants[direction] }}
                    transition={{ type: "spring", damping: 25, stiffness: 300 }}
                    className={className}
                >
                    {children}
                </motion.div>
            )}
        </AnimatePresence>
    )
}

interface PulseProps {
    children: React.ReactNode
    className?: string
}

export function Pulse({ children, className }: PulseProps) {
    return (
        <motion.div
            animate={{ scale: [1, 1.02, 1] }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
            className={className}
        >
            {children}
        </motion.div>
    )
}
