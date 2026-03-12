"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatOre } from "@/lib/utils";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

type Tab = "stables" | "horses";

export default function LeaderboardPage() {
  const [tab, setTab] = useState<Tab>("stables");

  const { data: stableData, isLoading: stablesLoading } = useQuery({
    queryKey: ["leaderboard-stables"],
    queryFn: api.getStableLeaderboard,
  });

  const { data: horseData, isLoading: horsesLoading } = useQuery({
    queryKey: ["leaderboard-horses"],
    queryFn: api.getHorseLeaderboard,
    enabled: tab === "horses",
  });

  const stables = stableData?.stables || [];
  const horses = horseData?.horses || [];

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-200">Topplista</h2>

      <div className="flex gap-2">
        <Button
          variant={tab === "stables" ? "primary" : "secondary"}
          size="sm"
          onClick={() => setTab("stables")}
        >
          Stall
        </Button>
        <Button
          variant={tab === "horses" ? "primary" : "secondary"}
          size="sm"
          onClick={() => setTab("horses")}
        >
          Hästar
        </Button>
      </div>

      {tab === "stables" && (
        <Card>
          {stablesLoading ? (
            <div className="text-gray-500 text-sm">Laddar...</div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-500 text-xs border-b border-trav-border">
                  <th className="text-left py-2 w-12">#</th>
                  <th className="text-left py-2">Stall</th>
                  <th className="text-center py-2">Hästar</th>
                  <th className="text-center py-2">Rykte</th>
                  <th className="text-center py-2">Fans</th>
                  <th className="text-right py-2">Intjänat</th>
                </tr>
              </thead>
              <tbody>
                {stables.map((s: any) => (
                  <tr
                    key={s.rank}
                    className={`border-b border-trav-border/50 ${
                      !s.is_npc ? "bg-trav-gold/5" : ""
                    }`}
                  >
                    <td className="py-2.5 font-bold text-gray-400">{s.rank}</td>
                    <td className="py-2.5">
                      <span className={`font-medium ${!s.is_npc ? "text-trav-gold" : "text-gray-200"}`}>
                        {s.name}
                      </span>
                      {!s.is_npc && <Badge color="#D4A853" className="ml-2">Du</Badge>}
                    </td>
                    <td className="py-2.5 text-center text-gray-400">{s.horse_count}</td>
                    <td className="py-2.5 text-center text-gray-400">{s.reputation}</td>
                    <td className="py-2.5 text-center text-gray-400">{s.fan_count}</td>
                    <td className="py-2.5 text-right text-trav-gold font-semibold">
                      {formatOre(s.total_earnings)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      )}

      {tab === "horses" && (
        <Card>
          {horsesLoading ? (
            <div className="text-gray-500 text-sm">Laddar...</div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-500 text-xs border-b border-trav-border">
                  <th className="text-left py-2 w-12">#</th>
                  <th className="text-left py-2">Häst</th>
                  <th className="text-left py-2">Stall</th>
                  <th className="text-center py-2">Starter</th>
                  <th className="text-center py-2">1-2-3</th>
                  <th className="text-right py-2">Bästa tid</th>
                  <th className="text-right py-2">Intjänat</th>
                </tr>
              </thead>
              <tbody>
                {horses.map((h: any) => (
                  <tr
                    key={h.rank}
                    className={`border-b border-trav-border/50 ${
                      !h.is_npc ? "bg-trav-gold/5" : ""
                    }`}
                  >
                    <td className="py-2.5 font-bold text-gray-400">{h.rank}</td>
                    <td className="py-2.5">
                      <span className={`font-medium ${!h.is_npc ? "text-trav-gold" : "text-gray-200"}`}>
                        {h.name}
                      </span>
                      {!h.is_npc && <Badge color="#D4A853" className="ml-2">Din</Badge>}
                      <span className="text-xs text-gray-500 ml-2">
                        {h.gender === "stallion" ? "H" : h.gender === "mare" ? "S" : "V"} {h.age_years}år
                      </span>
                    </td>
                    <td className="py-2.5 text-gray-400 text-xs">{h.stable_name}</td>
                    <td className="py-2.5 text-center text-gray-300">{h.total_starts}</td>
                    <td className="py-2.5 text-center">
                      <span className="text-trav-gold">{h.total_wins}</span>
                      <span className="text-gray-500">-</span>
                      <span className="text-gray-300">{h.total_seconds}</span>
                      <span className="text-gray-500">-</span>
                      <span className="text-gray-300">{h.total_thirds}</span>
                    </td>
                    <td className="py-2.5 text-right text-gray-300 tabular-nums">
                      {h.best_km_time || "-"}
                    </td>
                    <td className="py-2.5 text-right text-trav-gold font-semibold">
                      {formatOre(h.total_earnings)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      )}
    </div>
  );
}
