"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { formatOre } from "@/lib/utils";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { StatBar } from "@/components/ui/StatBar";
import { Button } from "@/components/ui/Button";

type Tab = "results" | "seasons" | "pedigree";

export default function HorseProfilePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("results");

  const { data, isLoading, error } = useQuery({
    queryKey: ["horse-profile", id],
    queryFn: () => api.getHorseProfile(id),
  });

  const { data: pedigree } = useQuery({
    queryKey: ["pedigree", id],
    queryFn: () => api.getPedigree(id),
    enabled: tab === "pedigree",
  });

  if (isLoading) return <div className="text-gray-500">Laddar hästprofil...</div>;
  if (error) return <div className="text-red-400">Kunde inte ladda hästen</div>;
  if (!data) return <div className="text-gray-500">Hästen hittades inte</div>;

  const h = data;
  const genderLabel = h.gender === "stallion" ? "Hingst" : h.gender === "mare" ? "Sto" : "Valack";
  const ageYears = h.age_years ?? Math.floor((h.age_weeks || 0) / 16);
  const winPct = h.total_starts > 0 ? ((h.total_wins / h.total_starts) * 100).toFixed(0) : "0";
  const placePct = h.total_starts > 0 ? (((h.total_wins + h.total_seconds + h.total_thirds) / h.total_starts) * 100).toFixed(0) : "0";

  // Group race history by season (every 32 weeks = 1 season year)
  const raceHistory = h.race_history || [];
  const seasonMap: Record<number, any[]> = {};
  for (const r of raceHistory) {
    const season = Math.floor((r.game_week - 1) / 32) + 1;
    if (!seasonMap[season]) seasonMap[season] = [];
    seasonMap[season].push(r);
  }

  const TABS: { key: Tab; label: string }[] = [
    { key: "results", label: "Tävlingsresultat" },
    { key: "seasons", label: "Säsongsöversikt" },
    { key: "pedigree", label: "Härstamning" },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-bold text-trav-gold">{h.name}</h2>
            <Badge color="#6B7280">{genderLabel}</Badge>
            <Badge color={h.status === "ready" ? "#22c55e" : "#ef4444"}>{h.status}</Badge>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            {ageYears} år | {h.stable_name} | {h.bloodline || "Okänd blodlinje"} | Optimaldistans: {h.distance_optimum}m
          </p>
        </div>
        <button onClick={() => router.back()} className="text-sm text-gray-500 hover:text-gray-300">
          ← Tillbaka
        </button>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Stats */}
        <Card>
          <h3 className="text-sm font-semibold text-gray-300 mb-3">Egenskaper</h3>
          <div className="space-y-2">
            {[
              { label: "Fart", value: h.speed },
              { label: "Uthållighet", value: h.endurance },
              { label: "Mentalitet", value: h.mentality },
              { label: "Startförmåga", value: h.start_ability },
              { label: "Spurtstyrka", value: h.sprint_strength },
              { label: "Balans", value: h.balance },
              { label: "Styrka", value: h.strength },
            ].map((s) => (
              <div key={s.label} className="flex items-center gap-3">
                <span className="text-xs text-gray-500 w-24">{s.label}</span>
                <div className="flex-1">
                  <StatBar value={s.value} max={100} />
                </div>
                <span className="text-sm font-semibold text-gray-200 w-8 text-right">{s.value}</span>
              </div>
            ))}
          </div>

          <div className="mt-4 pt-3 border-t border-trav-border">
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-500">Form</span>
                <span className="text-gray-300">{h.form}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Kondition</span>
                <span className="text-gray-300">{h.condition}</span>
              </div>
            </div>
          </div>

          {/* Special traits */}
          {h.special_traits && h.special_traits.length > 0 && (
            <div className="mt-3 pt-3 border-t border-trav-border">
              <div className="text-xs text-gray-500 mb-1">Speciella egenskaper</div>
              <div className="flex flex-wrap gap-1">
                {h.special_traits.map((t: string) => (
                  <span key={t} className="text-[10px] px-2 py-0.5 rounded bg-purple-900/30 text-purple-300 border border-purple-700/30">
                    {TRAIT_LABELS[t] || t}
                  </span>
                ))}
              </div>
            </div>
          )}
        </Card>

        {/* Career stats */}
        <Card>
          <h3 className="text-sm font-semibold text-gray-300 mb-3">Karriär</h3>
          <div className="grid grid-cols-2 gap-y-3 gap-x-6 text-sm">
            <div>
              <div className="text-xs text-gray-500">Starter</div>
              <div className="text-lg font-bold text-gray-200">{h.total_starts}</div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Segrar</div>
              <div className="text-lg font-bold text-green-400">{h.total_wins}</div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Andraplatser</div>
              <div className="text-gray-300">{h.total_seconds}</div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Tredjeplatser</div>
              <div className="text-gray-300">{h.total_thirds}</div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Diskvalificeringar</div>
              <div className="text-red-400">{h.total_dq}</div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Bästa km-tid</div>
              <div className="text-trav-gold font-semibold">{h.best_km_time || "-"}</div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Vinstprocent</div>
              <div className="text-gray-300">{winPct}%</div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Platsprocent</div>
              <div className="text-gray-300">{placePct}%</div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-trav-border">
            <div className="text-xs text-gray-500">Totalt intjänat</div>
            <div className="text-xl font-bold text-trav-gold">{formatOre(h.total_earnings)}</div>
          </div>
        </Card>
      </div>

      {/* Tab bar */}
      <div className="flex gap-2 border-b border-trav-border pb-0">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === t.key
                ? "border-trav-gold text-trav-gold"
                : "border-transparent text-gray-500 hover:text-gray-300"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === "results" && (
        <Card>
          {raceHistory.length === 0 ? (
            <p className="text-xs text-gray-500">Inga lopp registrerade</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-500 text-xs border-b border-trav-border">
                  <th className="text-left py-2">Lopp</th>
                  <th className="text-left py-2">Bana</th>
                  <th className="text-center py-2">Dist</th>
                  <th className="text-center py-2">Spår</th>
                  <th className="text-center py-2">Res</th>
                  <th className="text-right py-2">Km-tid</th>
                  <th className="text-left py-2">Kusk</th>
                  <th className="text-right py-2">Pris</th>
                  <th className="text-right py-2">Vecka</th>
                </tr>
              </thead>
              <tbody>
                {raceHistory.map((r: any, i: number) => (
                  <tr
                    key={i}
                    className="border-b border-trav-border/50 hover:bg-trav-hover cursor-pointer"
                    onClick={() => router.push(`/races/${r.race_id}`)}
                  >
                    <td className="py-2 text-gray-300">{r.race_name}</td>
                    <td className="py-2 text-gray-400 text-xs">{r.track_name || "-"}</td>
                    <td className="py-2 text-center text-gray-400">{r.distance}m</td>
                    <td className="py-2 text-center text-gray-400">{r.post_position || "-"}</td>
                    <td className="py-2 text-center">
                      <span
                        className={`font-bold ${
                          r.position === 1
                            ? "text-trav-gold"
                            : r.position <= 3
                            ? "text-green-400"
                            : "text-gray-400"
                        }`}
                      >
                        {r.position}
                      </span>
                    </td>
                    <td className="py-2 text-right text-gray-300 tabular-nums">{r.km_time}</td>
                    <td className="py-2 text-gray-400 text-xs">{r.driver_name || "-"}</td>
                    <td className="py-2 text-right text-trav-gold">
                      {r.prize > 0 ? formatOre(r.prize) : "-"}
                    </td>
                    <td className="py-2 text-right text-gray-500">V{r.game_week}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      )}

      {tab === "seasons" && (
        <Card>
          {Object.keys(seasonMap).length === 0 ? (
            <p className="text-xs text-gray-500">Inga säsonger registrerade</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-500 text-xs border-b border-trav-border">
                  <th className="text-left py-2">Säsong</th>
                  <th className="text-center py-2">Starter</th>
                  <th className="text-center py-2">1:a</th>
                  <th className="text-center py-2">2:a</th>
                  <th className="text-center py-2">3:a</th>
                  <th className="text-right py-2">Intjänat</th>
                  <th className="text-right py-2">Rekord</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(seasonMap)
                  .sort(([a], [b]) => Number(b) - Number(a))
                  .map(([season, races]) => {
                    const wins = races.filter((r: any) => r.position === 1).length;
                    const seconds = races.filter((r: any) => r.position === 2).length;
                    const thirds = races.filter((r: any) => r.position === 3).length;
                    const earnings = races.reduce((sum: number, r: any) => sum + (r.prize || 0), 0);
                    const bestTime = races
                      .filter((r: any) => r.km_time && r.km_time !== "-")
                      .map((r: any) => r.km_time)
                      .sort()[0] || "-";
                    return (
                      <tr key={season} className="border-b border-trav-border/50">
                        <td className="py-2 text-gray-300 font-medium">Säsong {season}</td>
                        <td className="py-2 text-center text-gray-300">{races.length}</td>
                        <td className="py-2 text-center text-trav-gold font-bold">{wins}</td>
                        <td className="py-2 text-center text-gray-300">{seconds}</td>
                        <td className="py-2 text-center text-gray-300">{thirds}</td>
                        <td className="py-2 text-right text-trav-gold">{formatOre(earnings)}</td>
                        <td className="py-2 text-right text-gray-300 tabular-nums">{bestTime}</td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          )}
        </Card>
      )}

      {tab === "pedigree" && (
        <Card>
          <h3 className="text-sm font-semibold text-gray-300 mb-4">Stamtavla (3 generationer)</h3>
          {!pedigree ? (
            <p className="text-xs text-gray-500">Laddar härstamning...</p>
          ) : !pedigree.sire_name && !pedigree.dam_name ? (
            <p className="text-xs text-gray-500">Ingen härstamning registrerad</p>
          ) : (
            <div className="flex gap-2 text-xs">
              {/* Generation 1: Horse */}
              <div className="flex flex-col justify-center">
                <PedigreeBox name={h.name} origin="" highlight />
              </div>

              {/* Generation 2: Parents */}
              <div className="flex flex-col justify-around">
                <PedigreeBox name={pedigree.sire_name || "Okänd"} origin={pedigree.sire_origin} gender="stallion" />
                <PedigreeBox name={pedigree.dam_name || "Okänd"} origin={pedigree.dam_origin} gender="mare" />
              </div>

              {/* Generation 3: Grandparents */}
              <div className="flex flex-col justify-around gap-1">
                <PedigreeBox name={pedigree.sire_sire_name || "Okänd"} origin="" gender="stallion" small />
                <PedigreeBox name={pedigree.sire_dam_name || "Okänd"} origin="" gender="mare" small />
                <PedigreeBox name={pedigree.dam_sire_name || "Okänd"} origin="" gender="stallion" small />
                <PedigreeBox name={pedigree.dam_dam_name || "Okänd"} origin="" gender="mare" small />
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

function PedigreeBox({
  name,
  origin,
  gender,
  highlight,
  small,
}: {
  name: string;
  origin?: string;
  gender?: string;
  highlight?: boolean;
  small?: boolean;
}) {
  const borderColor = highlight
    ? "border-trav-gold"
    : gender === "stallion"
    ? "border-blue-500/40"
    : gender === "mare"
    ? "border-pink-500/40"
    : "border-trav-border";

  const bgColor = highlight ? "bg-trav-gold/10" : "bg-trav-bg";

  return (
    <div
      className={`${bgColor} border ${borderColor} rounded px-3 py-2 ${
        small ? "min-w-[120px]" : "min-w-[140px]"
      }`}
    >
      <div className={`font-semibold ${highlight ? "text-trav-gold" : "text-gray-200"} ${small ? "text-[10px]" : "text-xs"}`}>
        {name}
      </div>
      {origin && <div className="text-[10px] text-gray-500">{origin}</div>}
    </div>
  );
}

const TRAIT_LABELS: Record<string, string> = {
  sprint_king: "Spurtkung",
  rain_lover: "Regnälskare",
  iron_hooves: "Järnhovar",
  early_bloomer: "Tidig mognad",
  late_bloomer: "Sen mognad",
  nervous_starter: "Nervös startare",
  gallop_prone: "Galoppbenägen",
  cold_hater: "Köldkänslig",
  crowd_shy: "Publikrädd",
  temperamental: "Temperamentsfull",
  glass_legs: "Glasben",
  heavy_sweater: "Svettare",
};
