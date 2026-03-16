interface BadgeProps {
  children: React.ReactNode;
  color?: string;
  className?: string;
  size?: "sm" | "md";
}

export function Badge({ children, color = "#D4A853", className = "", size = "sm" }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-md font-semibold tracking-wide ${
        size === "sm" ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-1 text-[11px]"
      } ${className}`}
      style={{
        backgroundColor: color + "15",
        color,
        border: `1px solid ${color}25`,
      }}
    >
      {children}
    </span>
  );
}
