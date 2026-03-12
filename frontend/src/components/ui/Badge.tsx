interface BadgeProps {
  children: React.ReactNode;
  color?: string;
  className?: string;
}

export function Badge({ children, color = "#D4A853", className = "" }: BadgeProps) {
  return (
    <span
      className={`inline-block px-2 py-0.5 rounded text-[11px] font-semibold tracking-wide ${className}`}
      style={{
        backgroundColor: color + "18",
        color,
        border: `1px solid ${color}33`,
      }}
    >
      {children}
    </span>
  );
}
