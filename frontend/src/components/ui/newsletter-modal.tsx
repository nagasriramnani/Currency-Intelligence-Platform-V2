"use client"

import React, { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import * as DialogPrimitive from "@radix-ui/react-dialog"
import { cn } from "./button"
import { Button } from "./button"
import { X, Mail, Bell, Check, Loader2, Zap } from "lucide-react"

interface NewsletterModalProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    onSubscribe: (email: string, frequency: string) => Promise<void>
}

export function NewsletterModal({ open, onOpenChange, onSubscribe }: NewsletterModalProps) {
    const [email, setEmail] = useState("")
    const [frequency, setFrequency] = useState("weekly")
    const [loading, setLoading] = useState(false)
    const [success, setSuccess] = useState(false)
    const [successMessage, setSuccessMessage] = useState("Subscribed!")

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!email) return

        setLoading(true)
        try {
            await onSubscribe(email, frequency)

            // Show appropriate success message
            if (frequency === 'now') {
                setSuccessMessage("Sample email sent!")
            } else {
                setSuccessMessage("Subscribed!")
            }

            setSuccess(true)
            setTimeout(() => {
                onOpenChange(false)
                setSuccess(false)
                setEmail("")
                setFrequency("weekly")
            }, 2000)
        } catch (err) {
            console.error(err)
            alert("Failed to subscribe. Please try again.")
        } finally {
            setLoading(false)
        }
    }

    const frequencies = [
        { value: "daily", label: "Daily", icon: null },
        { value: "weekly", label: "Weekly", icon: null },
        { value: "monthly", label: "Monthly", icon: null },
        { value: "now", label: "Now", icon: <Zap className="h-3 w-3" /> }
    ]

    return (
        <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
            <AnimatePresence>
                {open && (
                    <DialogPrimitive.Portal forceMount>
                        <DialogPrimitive.Overlay asChild>
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
                            />
                        </DialogPrimitive.Overlay>

                        <DialogPrimitive.Content asChild>
                            <motion.div
                                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                                animate={{ opacity: 1, scale: 1, y: 0 }}
                                exit={{ opacity: 0, scale: 0.95, y: 20 }}
                                transition={{ type: "spring", damping: 25, stiffness: 300 }}
                                className={cn(
                                    "fixed left-1/2 top-1/2 z-50 -translate-x-1/2 -translate-y-1/2",
                                    "w-full max-w-md max-h-[90vh] rounded-2xl",
                                    "bg-gradient-to-b from-slate-900 to-slate-950",
                                    "border border-slate-800 shadow-2xl shadow-black/40",
                                    "p-6 focus:outline-none overflow-y-auto"
                                )}
                            >
                                {/* Close button */}
                                <DialogPrimitive.Close className="absolute right-4 top-4 p-2 rounded-lg text-slate-500 hover:text-white hover:bg-slate-800 transition-colors">
                                    <X className="h-5 w-5" />
                                </DialogPrimitive.Close>

                                {/* Header */}
                                <div className="flex items-center gap-3 mb-6">
                                    <div className="p-3 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/30">
                                        <Bell className="h-6 w-6 text-indigo-400" />
                                    </div>
                                    <div>
                                        <DialogPrimitive.Title className="text-xl font-semibold text-white">
                                            Subscribe to EIS Alerts
                                        </DialogPrimitive.Title>
                                        <DialogPrimitive.Description className="text-sm text-slate-400 mt-0.5">
                                            Get AI-powered investment opportunities delivered to your inbox
                                        </DialogPrimitive.Description>
                                    </div>
                                </div>

                                <AnimatePresence mode="wait">
                                    {success ? (
                                        <motion.div
                                            key="success"
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            exit={{ opacity: 0, y: -10 }}
                                            className="flex flex-col items-center py-8"
                                        >
                                            <motion.div
                                                initial={{ scale: 0 }}
                                                animate={{ scale: 1 }}
                                                transition={{ type: "spring", damping: 15 }}
                                                className="p-4 rounded-full bg-emerald-500/20 mb-4"
                                            >
                                                <Check className="h-8 w-8 text-emerald-400" />
                                            </motion.div>
                                            <p className="text-lg font-medium text-white">{successMessage}</p>
                                            <p className="text-sm text-slate-400">Check your inbox</p>
                                        </motion.div>
                                    ) : (
                                        <motion.form
                                            key="form"
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            exit={{ opacity: 0 }}
                                            onSubmit={handleSubmit}
                                            className="space-y-5"
                                        >
                                            {/* Email Input */}
                                            <div>
                                                <label className="block text-sm font-medium text-slate-300 mb-2">
                                                    Email Address
                                                </label>
                                                <div className="relative">
                                                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-500" />
                                                    <input
                                                        type="email"
                                                        value={email}
                                                        onChange={(e) => setEmail(e.target.value)}
                                                        placeholder="you@example.com"
                                                        required
                                                        className={cn(
                                                            "w-full pl-11 pr-4 py-3 rounded-xl",
                                                            "bg-slate-800/50 border border-slate-700",
                                                            "text-white placeholder-slate-500",
                                                            "focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500",
                                                            "transition-all duration-200"
                                                        )}
                                                    />
                                                </div>
                                            </div>

                                            {/* Frequency Selection */}
                                            <div>
                                                <label className="block text-sm font-medium text-slate-300 mb-2">
                                                    Frequency
                                                </label>
                                                <div className="grid grid-cols-4 gap-2">
                                                    {frequencies.map((freq) => (
                                                        <button
                                                            key={freq.value}
                                                            type="button"
                                                            onClick={() => setFrequency(freq.value)}
                                                            className={cn(
                                                                "p-3 rounded-xl border text-center transition-all duration-200",
                                                                frequency === freq.value
                                                                    ? freq.value === 'now'
                                                                        ? "bg-amber-500/20 border-amber-500 text-amber-300"
                                                                        : "bg-indigo-500/20 border-indigo-500 text-indigo-300"
                                                                    : "bg-slate-800/50 border-slate-700 text-slate-400 hover:border-slate-600"
                                                            )}
                                                        >
                                                            <span className="flex items-center justify-center gap-1 text-sm font-medium">
                                                                {freq.icon}
                                                                {freq.label}
                                                            </span>
                                                        </button>
                                                    ))}
                                                </div>
                                                <p className="text-xs text-slate-500 mt-2">
                                                    {frequency === 'now'
                                                        ? "Send a sample newsletter to your email immediately"
                                                        : "Select when you want to receive updates"}
                                                </p>
                                            </div>

                                            {/* Submit Button */}
                                            <Button
                                                type="submit"
                                                loading={loading}
                                                className="w-full"
                                                size="lg"
                                            >
                                                {frequency === 'now' ? 'Send Sample Now' : 'Subscribe Now'}
                                            </Button>

                                            <p className="text-xs text-center text-slate-500">
                                                By subscribing, you agree to receive EIS investment updates.
                                                Unsubscribe anytime.
                                            </p>
                                        </motion.form>
                                    )}
                                </AnimatePresence>
                            </motion.div>
                        </DialogPrimitive.Content>
                    </DialogPrimitive.Portal>
                )}
            </AnimatePresence>
        </DialogPrimitive.Root>
    )
}
