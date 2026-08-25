"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatOre } from "@/lib/utils";
import { Card } from "@/components/ui/Card";

export function SeasonGoals() {
  const [showSummary, setShowSummary] = useState(false);

  const { data } = useQuery({ queryKey: ["season-goals"], queryFn: api.getSeasonGoals });
  const { data: summary } = useQuery({
    queryKey: ["season-summary"],
    queryFn: () => api.getSeasonSummary(),
    enabled: showSummary,
  });

  if (!data) return null;

  const goals: any[] = data.goals || [];
  const seasonProgress = Math.round((data.week_in_season / data.season_length) * 100);

  return (
    <Card>
      <div className="flex items-baseline justify-between mb-3">
        <div>
          <h3 className="text-sm font-semibold text-gray-200">
            Säsong {data.season_number} — mål
          </h3>
          <p className="text-[11px] text-gray-500 mt-0.5">
            Vecka {data.week_in_season} av {data.season_length} ·{" "}
            {data.completed}/{goals.length} mål klara
          </p>
        </div>
        <button
          onClick={() => setShowSummary((v) => !v)}
          className="text-[11px] text-trav-gold hover:underline"
        >
          {showSummary ? "Dölj sammanfattning" : "Din säsong →"}
        </button>
      </div>

      {/* Säsongens gång */}
      <div className="h-1 bg-trav-border rounded-full mb-4 overflow-hidden">
        <div
          className="h-full bg-trav-gold/60 rounded-full transition-all"
          style={{ width: `${Math.min(100, seasonProgress)}%` }}
        />
      </div>

      <div className="space-y-2.5">
        {goals.map((g) => (
          <div key={g.id}>
            <div className="flex items-baseline justify-between gap-2 mb-1">
              <span
                className={`text-xs font-medium ${
                  g.is_completed ? "text-green-400" : "text-gray-200"
                }`}
              >
                {g.is_completed && "✓ "}{g.title}
              </span>
              <span className="text-[10px] text-gray-500 tabular-nums shrink-0">
                {g.key === "earnings"
                  ? `${formatOre(g.progress * 100)} / ${formatOre(g.target * 100)}`
                  : `${g.progress} / ${g.target}`}
              </span>
            </div>
            <div className="h-1.5 bg-trav-border rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width: `${g.percent}%`,
                  backgroundColor: g.is_completed ? "#4ADE80" : "#D4A853",
                }}
              />
            </div>
            <p className="text-[10px] text-gray-600 mt-0.5">
              {g.description} · Belöning: <span className="text-trav-gold/80">{g.reward_text}</span>
            </p>
          </div>
        ))}
      </div>

      {/* Säsongssammanfattning */}
      {showSummary && summary && !summary.error && (
        <div className="mt-5 pt-4 border-t border-trav-border">
          <div className="section-label mb-2">
            Din säsong {summary.season_number} (vecka {summary.weeks[0]}–{summary.weeks[1]})
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
            <Stat label="Starter" value={summary.starts} />
            <Stat label="Segrar" value={summary.wins} accent="#4ADE80" />
            <Stat label="Segerprocent" value={`${summary.win_rate} %`} />
            <Stat label="Intjänat" value={formatOre(summary.earned)} accent="#D4A853" />
            <Stat label="Pallplatser" value={summary.wins + summary.seconds + summary.thirds} />
            <Stat label="Pallprocent" value={`${summary.podium_rate} %`} />
            <Stat label="Upptäckter" value={summary.discoveries} />
            <Stat label="Rykte" value={summary.reputation} />
          </div>

          {summary.best_race && (
            <p className="text-[11px] text-gray-400 mb-1">
              Bästa lopp: plats {summary.best_race.position} för{" "}
              <span className="text-trav-gold">{formatOre(summary.best_race.prize)}</span>{" "}
              (vecka {summary.best_race.game_week}) ·{" "}
              <a href={`/races/${summary.best_race.race_id}`} className="text-trav-gold hover:underline">
                se loppet
              </a>
            </p>
          )}

          {summary.form_curve?.length > 1 && (
            <div className="mt-3">
              <div className="text-[10px] text-gray-500 mb-1">Formkurva</div>
              <svg viewBox={`0 0 ${summary.form_curve.length * 10} 40`} className="w-full h-10">
                <polyline
                  fill="none"
                  stroke="#D4A853"
                  strokeWidth="1.5"
                  points={summary.form_curve
                    .map((v: number, i: number) => `${i * 10},${40 - (v / 100) * 40}`)
                    .join(" ")}
                />
              </svg>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

function Stat({ label, value, accent }: { label: string; value: any; accent?: string }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider text-gray-500">{label}</div>
      <div className="text-base font-bold tabular-nums" style={{ color: accent || "#E8E6E1" }}>
        {value}
      </div>
    </div>
  );
}
