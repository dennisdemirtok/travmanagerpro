"use client";

import { cn } from "@/lib/utils";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
}

export function Button({ children, variant = "primary", size = "md", className, ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "font-semibold rounded-lg transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center justify-center",
        variant === "primary" && "bg-gradient-to-b from-trav-gold to-trav-gold-dim text-trav-bg hover:from-trav-gold-bright hover:to-trav-gold shadow-sm active:scale-[0.98]",
        variant === "secondary" && "bg-trav-active border border-trav-border text-gray-300 hover:bg-trav-hover hover:border-trav-border-light active:scale-[0.98]",
        variant === "ghost" && "text-gray-400 hover:text-gray-200 hover:bg-trav-hover",
        variant === "danger" && "bg-red-600/90 text-white hover:bg-red-600 border border-red-500/30 active:scale-[0.98]",
        size === "sm" && "px-3 py-1.5 text-xs",
        size === "md" && "px-4 py-2 text-sm",
        size === "lg" && "px-6 py-2.5 text-sm",
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
