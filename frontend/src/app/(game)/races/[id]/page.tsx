"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { formatOre } from "@/lib/utils";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { RaceReplay } from "@/components/race/RaceReplay";

const WEATHER_LABELS: Record<string, string> = {
  clear: "Uppehåll",
  cloudy: "Mulet",
  rain: "Regn",
  heavy_rain: "Kraftigt regn",
  snow: "Snö",
  cold: "Kallt",
  hot: "Varmt",
  windy: "Blåsigt",
};

const SURFACE_LABELS: Record<string, string> = {
  dirt: "Grus",
  synthetic: "Syntet",
  winter: "Vinterbana",
};

const START_LABELS: Record<string, string> = {
  volt: "Voltstart",
  auto: "Autostart",
};

const GRADE_COLORS: Record<string, string> = {
  A: "#4ADE80", B: "#A3E635", C: "#E9C46A", D: "#FB923C", F: "#EF4444",
};

const VERDICT_COLORS: Record<string, string> = {
  good: "#4ADE80", ok: "#9AA0AE", bad: "#EF4444",
};

const VERDICT_MARKS: Record<string, string> = {
  good: "✓", ok: "~", bad: "✕",
};

const PHASE_ICONS: Record<string, string> = {
  opening: "🏁",
  middle: "🔄",
  backstretch: "🔜",
  sprint: "⚡",
};

const PHASE_COLORS: Record<string, string> = {
  opening: "border-blue-700/40 bg-blue-900/20",
  middle: "border-gray-600/40 bg-gray-800/20",
  backstretch: "border-orange-700/40 bg-orange-900/20",
  sprint: "border-yellow-600/40 bg-yellow-900/20",
};

export default function RaceResultPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { data, isLoading, error } = useQuery({
    queryKey: ["race-result", id],
    queryFn: () => api.getRaceResult(id),
  });

  const [view, setView] = useState<"result" | "replay">("result");

  if (isLoading) return <div className="text-gray-500">Laddar...</div>;
  if (error) return <div className="text-red-400">Kunde inte ladda resultat</div>;
  if (!data) return <div className="text-gray-500">Inget resultat</div>;

  const finishers = data.finishers || [];
  const disqualified = data.disqualified || [];
  const allEvents = data.events || [];
  const snapshots = data.snapshots || [];
  const commentary = data.commentary || [];
  const tactical = data.tactical || {};
  const tacticalList: any[] = Object.entries(tactical).map(([hid, rev]: any) => ({ hid, ...rev }));
  const hasReplay = snapshots.length > 0;

  // Separate narrative events from technical events
  const narrativeEvents = allEvents.filter((e: any) => e.type === "narrative");
  const technicalEvents = allEvents.filter((e: any) => e.type !== "narrative");
  const gallopEvents = technicalEvents.filter((e: any) => e.type?.includes("gallop"));
  const otherEvents = technicalEvents.filter((e: any) => !e.type?.includes("gallop"));

  // Build header info
  const weatherLabel = WEATHER_LABELS[data.weather] || data.weather || "";
  const surfaceLabel = SURFACE_LABELS[data.surface] || data.surface || "";
  const startLabel = START_LABELS[data.start_method] || data.start_method || "";
  const tempStr = data.temperature != null ? `${data.temperature}°C` : "";
  const weekStr = data.game_week ? `V${data.game_week}` : "";
  const dayStr = data.day_name || "";

  return (
    <div className="space-y-6">
      {/* Race header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-200">{data.race_name}</h2>
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1 mt-1">
            <span className="text-sm text-trav-gold font-medium">
              {data.distance}m {startLabel}
            </span>
            <span className="text-gray-600">•</span>
            <span className="text-sm text-gray-300">{data.track}</span>
            {data.track_city && (
              <span className="text-sm text-gray-500">({data.track_city})</span>
            )}
            {(dayStr || weekStr) && (
              <>
                <span className="text-gray-600">•</span>
                <span className="text-sm text-gray-400">
                  {dayStr} {weekStr}
                </span>
              </>
            )}
          </div>
          {(surfaceLabel || weatherLabel || tempStr) && (
            <div className="flex items-center gap-2 mt-1">
              {surfaceLabel && (
                <span className="text-xs px-2 py-0.5 rounded bg-trav-bg border border-trav-border text-gray-400">
                  {surfaceLabel}
                </span>
              )}
              {weatherLabel && (
                <span className="text-xs px-2 py-0.5 rounded bg-trav-bg border border-trav-border text-gray-400">
                  {weatherLabel} {tempStr}
                </span>
              )}
            </div>
          )}
        </div>

        {hasReplay && (
          <div className="flex gap-1 bg-trav-active border border-trav-border rounded-lg p-0.5">
            <button
              onClick={() => setView("result")}
              className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                view === "result"
                  ? "bg-trav-gold text-trav-bg"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              Resultat
            </button>
            <button
              onClick={() => setView("replay")}
              className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                view === "replay"
                  ? "bg-trav-gold text-trav-bg"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              Se loppet
            </button>
          </div>
        )}
      </div>

      {/* Race Replay */}
      {view === "replay" && hasReplay && (
        <Card>
          <RaceReplay
            snapshots={snapshots}
            finishers={finishers}
            distance={data.distance}
            raceName={data.race_name}
            events={technicalEvents}
            commentary={commentary}
          />
        </Card>
      )}

      {/* Results View */}
      {view === "result" && (
        <>
          {/* Taktiskt facit — varför gick det som det gick? */}
          {tacticalList.length > 0 && (
            <div className="space-y-3">
              {tacticalList.map((rev) => (
                <Card key={rev.hid}>
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div>
                      <h3 className="text-sm font-semibold text-gray-200">
                        Taktiskt facit — {rev.horse_name}
                      </h3>
                      <p className="text-[11px] text-gray-500 mt-0.5">
                        Placering {rev.finish_position || "—"}/{rev.field_size} ·
                        {" "}energi i mål {rev.energy_at_finish} ·
                        {" "}instängd i {rev.boxed_steps} lägen ·
                        {" "}{rev.gallop_incidents} galopp
                      </p>
                    </div>
                    <div className="text-right shrink-0">
                      <div
                        className="text-2xl font-bold leading-none"
                        style={{ color: GRADE_COLORS[rev.grade] || "#9AA0AE" }}
                      >
                        {rev.grade}
                      </div>
                      <div className="text-[10px] text-gray-500 tabular-nums mt-0.5">
                        {rev.total_points}/{rev.max_points} p
                      </div>
                    </div>
                  </div>
                  <p className="text-xs text-gray-400 mb-3">{rev.grade_text}</p>
                  <div className="space-y-1.5">
                    {rev.items.map((it: any, i: number) => (
                      <div
                        key={i}
                        className="flex items-start gap-2.5 py-1.5 border-b border-trav-border/40 last:border-0"
                      >
                        <span
                          className="text-xs font-bold w-5 shrink-0 pt-0.5"
                          style={{ color: VERDICT_COLORS[it.verdict] }}
                        >
                          {VERDICT_MARKS[it.verdict]}
                        </span>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-baseline gap-2 flex-wrap">
                            <span className="text-xs text-gray-500">{it.label}:</span>
                            <span className="text-xs font-semibold text-gray-200">{it.value}</span>
                            <span
                              className="text-[10px] tabular-nums"
                              style={{ color: VERDICT_COLORS[it.verdict] }}
                            >
                              {it.points > 0 ? "+" : ""}{it.points}
                            </span>
                          </div>
                          <p className="text-[11px] text-gray-400 mt-0.5">{it.comment}</p>
                          {it.optimal && (
                            <p className="text-[11px] text-trav-gold/80 mt-0.5">
                              Bättre val: {it.optimal}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              ))}
            </div>
          )}

          {/* Results Table */}
          <Card>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-500 text-xs border-b border-trav-border">
                  <th className="text-left py-2 w-12">#</th>
                  <th className="text-left py-2">Häst</th>
                  <th className="text-left py-2">Kusk</th>
                  <th className="text-right py-2">Km-tid</th>
                  <th className="text-right py-2">Pris</th>
                </tr>
              </thead>
              <tbody>
                {finishers.map((f: any, i: number) => (
                  <tr
                    key={i}
                    className={`border-b border-trav-border/50 ${
                      !f.is_npc ? "bg-trav-gold/5" : ""
                    }`}
                  >
                    <td className="py-2.5 font-bold text-gray-300">
                      {f.position}
                    </td>
                    <td className="py-2.5">
                      <span
                        className={`cursor-pointer hover:underline ${
                          !f.is_npc
                            ? "text-trav-gold font-semibold"
                            : "text-gray-300 hover:text-trav-gold"
                        }`}
                        onClick={() => router.push(`/horse/${f.horse_id}`)}
                      >
                        {f.horse_name}
                      </span>
                      {!f.is_npc && (
                        <Badge color="#D4A853" className="ml-2">
                          Du
                        </Badge>
                      )}
                    </td>
                    <td className="py-2.5 text-gray-400">{f.driver_name}</td>
                    <td className="py-2.5 text-right text-gray-300 tabular-nums">
                      {f.km_time}
                    </td>
                    <td className="py-2.5 text-right text-trav-gold">
                      {f.prize_money > 0 ? formatOre(f.prize_money) : "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>

          {/* Race Narrative */}
          {narrativeEvents.length > 0 && (
            <Card>
              <h3 className="text-sm font-semibold text-gray-300 mb-3">
                Loppberättelse
              </h3>
              <div className="space-y-2">
                {narrativeEvents.map((e: any, i: number) => {
                  const phase = e.data?.phase || "middle";
                  const phaseLabel = e.data?.phase_label || "";
                  const colorClass = PHASE_COLORS[phase] || PHASE_COLORS.middle;
                  const icon = PHASE_ICONS[phase] || "📍";

                  return (
                    <div
                      key={i}
                      className={`rounded-lg border p-3 ${colorClass}`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm">{icon}</span>
                        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
                          {phaseLabel}
                        </span>
                        <span className="text-[10px] text-gray-600">
                          {e.distance}m
                        </span>
                      </div>
                      <p className="text-sm text-gray-200 leading-relaxed">
                        {e.text}
                      </p>
                      {e.data?.positions && e.data.positions.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-2">
                          {e.data.positions.map((p: any, j: number) => (
                            <span
                              key={j}
                              className={`text-[10px] px-1.5 py-0.5 rounded border ${
                                j === 0
                                  ? "border-trav-gold/40 text-trav-gold bg-trav-gold/10"
                                  : "border-trav-border text-gray-500"
                              }`}
                            >
                              {p.pos}. {p.horse}
                              {p.gap > 0 ? ` (+${p.gap.toFixed(0)}m)` : ""}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </Card>
          )}

          {/* Gallop incidents */}
          {gallopEvents.length > 0 && (
            <Card>
              <h3 className="text-sm font-semibold text-red-400 mb-2">
                Galopphändelser
              </h3>
              {gallopEvents.map((e: any, i: number) => (
                <div key={i} className="flex items-start gap-2 text-xs py-1.5 border-b border-trav-border/30 last:border-0">
                  <span className="text-red-400 font-medium whitespace-nowrap">
                    {e.distance}m
                  </span>
                  <span className="text-gray-300">{e.text}</span>
                  <span className="text-[10px] text-gray-600 ml-auto whitespace-nowrap">
                    {e.type === "gallop_minor" && "Liten"}
                    {e.type === "gallop_major" && "Stor"}
                    {e.type === "gallop_dq" && "Disk"}
                  </span>
                </div>
              ))}
            </Card>
          )}

          {/* Other events */}
          {otherEvents.length > 0 && (
            <Card>
              <h3 className="text-sm font-semibold text-gray-300 mb-2">
                Övriga händelser
              </h3>
              {otherEvents.map((e: any, i: number) => (
                <div key={i} className="text-xs text-gray-400 py-1 border-b border-trav-border/30 last:border-0">
                  <span className="text-yellow-400 font-medium">{e.distance}m</span>{" "}
                  {e.text}
                </div>
              ))}
            </Card>
          )}

          {/* Disqualified */}
          {disqualified.length > 0 && (
            <Card>
              <h3 className="text-sm font-semibold text-red-400 mb-2">
                Diskvalificerade
              </h3>
              {disqualified.map((d: any, i: number) => (
                <div key={i} className="text-sm text-gray-400">
                  {d.horse} - {d.reason}
                </div>
              ))}
            </Card>
          )}
        </>
      )}
    </div>
  );
}
