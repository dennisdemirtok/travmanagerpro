"use client";

interface StatBarProps {
  value: number;
  max?: number;
  color?: string;
  label?: string;
  small?: boolean;
}

export function StatBar({ value, max = 100, color = "#D4A853", label, small = false }: StatBarProps) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="flex-1">
      {label && <div className="text-[11px] text-gray-500 mb-0.5">{label}</div>}
      <div className="flex items-center gap-2">
        <div className={`flex-1 bg-trav-border rounded-sm overflow-hidden ${small ? "h-1" : "h-1.5"}`}>
          <div
            className="h-full rounded-sm transition-all duration-500"
            style={{ width: `${pct}%`, backgroundColor: color }}
          />
        </div>
        <span className={`text-gray-400 tabular-nums min-w-[24px] text-right ${small ? "text-[11px]" : "text-xs"}`}>
          {Math.round(value)}
        </span>
      </div>
    </div>
  );
}
