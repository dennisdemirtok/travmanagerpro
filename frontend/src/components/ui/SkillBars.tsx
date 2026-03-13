"use client";

/**
 * XE-style skill rating bars (1-20 scale).
 * Shows filled/empty bar segments with color coding.
 */

interface SkillBarsProps {
  /** Rating on 1-20 scale */
  rating: number;
  /** Optional label text */
  label?: string;
  /** Compact mode for table rows */
  compact?: boolean;
}

function ratingColor(rating: number): string {
  if (rating >= 17) return "#4ADE80";   // Green - excellent
  if (rating >= 14) return "#D4A853";   // Gold - very good
  if (rating >= 11) return "#FB923C";   // Orange - decent
  if (rating >= 8) return "#F59E0B";    // Amber - below average
  return "#F87171";                      // Red - poor
}

export function SkillBars({ rating, label, compact = false }: SkillBarsProps) {
  const clamped = Math.max(1, Math.min(20, Math.round(rating)));
  const color = ratingColor(clamped);

  return (
    <div className={compact ? "flex items-center gap-1.5" : "flex items-center gap-2"}>
      {label && (
        <span className={`text-gray-500 ${compact ? "text-[10px] min-w-[32px]" : "text-xs min-w-[40px]"}`}>
          {label}
        </span>
      )}
      <div className="flex gap-[2px]">
        {Array.from({ length: 20 }, (_, i) => (
          <div
            key={i}
            className={`${compact ? "w-[5px] h-[10px]" : "w-[6px] h-[14px]"} rounded-[1px]`}
            style={{
              backgroundColor: i < clamped ? color : "rgba(255,255,255,0.08)",
            }}
          />
        ))}
      </div>
      <span
        className={`font-bold tabular-nums ${compact ? "text-[11px] min-w-[16px]" : "text-xs min-w-[20px]"}`}
        style={{ color }}
      >
        {clamped}
      </span>
    </div>
  );
}

/**
 * Calculate total skill rating (1-20) from the 7 core stats (each 1-100).
 */
export function calculateSkillRating(stats: {
  speed: number;
  endurance: number;
  mentality: number;
  start_ability: number;
  sprint_strength: number;
  balance: number;
  strength: number;
}): number {
  const avg =
    (stats.speed +
      stats.endurance +
      stats.mentality +
      stats.start_ability +
      stats.sprint_strength +
      stats.balance +
      stats.strength) /
    7;
  // Map 1-100 → 1-20
  return Math.max(1, Math.min(20, Math.round(avg / 5)));
}
