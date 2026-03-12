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
        "font-semibold rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed",
        variant === "primary" && "bg-trav-gold text-trav-bg hover:bg-trav-gold-bright",
        variant === "secondary" && "bg-trav-active border border-trav-border text-gray-300 hover:bg-trav-hover",
        variant === "ghost" && "text-gray-400 hover:text-gray-200 hover:bg-trav-hover",
        variant === "danger" && "bg-red-600 text-white hover:bg-red-700",
        size === "sm" && "px-3 py-1.5 text-sm",
        size === "md" && "px-4 py-2 text-sm",
        size === "lg" && "px-6 py-3 text-base",
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
