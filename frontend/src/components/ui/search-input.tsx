"use client"

import React, { useState, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "./button"
import { Search, X, Loader2 } from "lucide-react"

interface SearchInputProps {
    value: string
    onChange: (value: string) => void
    onSearch: () => void
    placeholder?: string
    loading?: boolean
    className?: string
}

export function SearchInput({
    value,
    onChange,
    onSearch,
    placeholder = "Search companies...",
    loading = false,
    className
}: SearchInputProps) {
    const [isFocused, setIsFocused] = useState(false)

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && value.trim()) {
            onSearch()
        }
    }

    return (
        <div className={cn("relative", className)}>
            <motion.div
                animate={{
                    boxShadow: isFocused
                        ? "0 0 0 2px rgba(99, 102, 241, 0.5), 0 4px 20px rgba(99, 102, 241, 0.15)"
                        : "0 0 0 1px rgba(51, 65, 85, 0.5)"
                }}
                transition={{ duration: 0.2 }}
                className="relative flex items-center rounded-xl bg-slate-900/80 backdrop-blur-sm overflow-hidden"
            >
                <div className="absolute inset-y-0 left-0 flex items-center pl-4 pointer-events-none">
                    <Search className="h-5 w-5 text-slate-500" />
                </div>

                <input
                    type="text"
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    onKeyPress={handleKeyPress}
                    onFocus={() => setIsFocused(true)}
                    onBlur={() => setIsFocused(false)}
                    placeholder={placeholder}
                    className={cn(
                        "w-full py-3.5 pl-12 pr-24 bg-transparent text-white placeholder-slate-500",
                        "focus:outline-none text-base"
                    )}
                />

                <AnimatePresence>
                    {value && (
                        <motion.button
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.8 }}
                            onClick={() => onChange("")}
                            className="absolute right-20 p-1 rounded-full hover:bg-slate-800 text-slate-500 hover:text-slate-300 transition-colors"
                        >
                            <X className="h-4 w-4" />
                        </motion.button>
                    )}
                </AnimatePresence>

                <button
                    onClick={onSearch}
                    disabled={!value.trim() || loading}
                    className={cn(
                        "absolute right-2 px-4 py-2 rounded-lg font-medium text-sm transition-all duration-200",
                        "bg-gradient-to-r from-indigo-500 to-purple-600 text-white",
                        "hover:from-indigo-600 hover:to-purple-700",
                        "disabled:opacity-50 disabled:cursor-not-allowed",
                        "shadow-lg shadow-indigo-500/25"
                    )}
                >
                    {loading ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                        "Search"
                    )}
                </button>
            </motion.div>

            {/* Keyboard hint */}
            <AnimatePresence>
                {isFocused && value && (
                    <motion.div
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 5 }}
                        className="absolute right-0 -bottom-6 text-xs text-slate-500"
                    >
                        Press Enter to search
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    )
}
