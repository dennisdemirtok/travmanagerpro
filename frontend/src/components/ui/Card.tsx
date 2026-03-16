"use client";

import { cn } from "@/lib/utils";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  hoverable?: boolean;
}

export function Card({ children, className, onClick, hoverable = false }: CardProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        "bg-trav-card border border-trav-border rounded-xl p-4 shadow-card transition-all duration-200",
        hoverable && "hover:bg-trav-card-hover hover:border-trav-border-light hover:shadow-card-hover cursor-pointer",
        onClick && "cursor-pointer hover:bg-trav-card-hover hover:border-trav-border-light hover:shadow-card-hover",
        className
      )}
    >
      {children}
    </div>
  );
}
