"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatOre, statColor } from "@/lib/utils";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

type SortKey = "earnings" | "name" | "age" | "speed" | "starts";

const SORT_OPTIONS: { key: SortKey; label: string }[] = [
  { key: "earnings", label: "Intjaning" },
  { key: "name", label: "Namn" },
  { key: "speed", label: "Fart" },
  { key: "starts", label: "Starter" },
  { key: "age", label: "Alder" },
];

const GENDER_SHORT: Record<string, string> = {
  stallion: "H",
  mare: "S",
  gelding: "V",
};

const GENDER_LABEL: Record<string, string> = {
  stallion: "Hingst",
  mare: "Sto",
  gelding: "Valack",
};

export default function HorseDatabasePage() {
  const [sort, setSort] = useState<SortKey>("earnings");
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["horse-database", sort, search],
    queryFn: () => api.getHorseDatabase(sort, search),
  });

  const horses = data?.horses || [];

  const handleSearch = () => {
    setSearch(searchInput);
  };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-200">Hastdatabas</h2>

      {/* Search + Sort */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex gap-2 flex-1">
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder="Sok hastnamn..."
            className="flex-1 px-3 py-2 bg-trav-bg border border-trav-border rounded-lg text-gray-200 text-sm placeholder:text-gray-600"
          />
          <Button size="sm" onClick={handleSearch}>
            Sok
          </Button>
          {search && (
            <Button
              size="sm"
              variant="secondary"
              onClick={() => {
                setSearch("");
                setSearchInput("");
              }}
            >
              Rensa
            </Button>
          )}
        </div>
        <div className="flex gap-1">
          {SORT_OPTIONS.map((opt) => (
            <Button
              key={opt.key}
              size="sm"
              variant={sort === opt.key ? "primary" : "secondary"}
              onClick={() => setSort(opt.key)}
            >
              {opt.label}
            </Button>
          ))}
        </div>
      </div>

      {/* Results count */}
      <div className="text-xs text-gray-500">
        {isLoading ? "Laddar..." : `${horses.length} hastar`}
        {search && ` (sok: "${search}")`}
      </div>

      {/* Horse table */}
      <Card>
        {isLoading ? (
          <div className="text-gray-500 text-sm py-4">Laddar hastdatabas...</div>
        ) : horses.length === 0 ? (
          <div className="text-gray-500 text-sm py-4">Inga hastar hittades.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-500 text-xs border-b border-trav-border">
                  <th className="text-left py-2 w-10">#</th>
                  <th className="text-left py-2">Hast</th>
                  <th className="text-left py-2">Stall</th>
                  <th className="text-center py-2">Fart</th>
                  <th className="text-center py-2">Uth.</th>
                  <th className="text-center py-2">Spurt</th>
                  <th className="text-center py-2">Starter</th>
                  <th className="text-center py-2">1-2-3</th>
                  <th className="text-right py-2">Basta tid</th>
                  <th className="text-right py-2">Intjanat</th>
                </tr>
              </thead>
              <tbody>
                {horses.map((h: any, i: number) => (
                  <tr
                    key={h.id}
                    className={`border-b border-trav-border/50 hover:bg-white/5 transition-colors ${
                      !h.is_npc ? "bg-trav-gold/5" : ""
                    }`}
                  >
                    <td className="py-2.5 font-bold text-gray-500">{i + 1}</td>
                    <td className="py-2.5">
                      <div className="flex items-center gap-2">
                        <span
                          className={`font-medium ${
                            !h.is_npc ? "text-trav-gold" : "text-gray-200"
                          }`}
                        >
                          {h.name}
                        </span>
                        {!h.is_npc && (
                          <Badge color="#D4A853">Spelare</Badge>
                        )}
                      </div>
                      <div className="text-[10px] text-gray-500 mt-0.5">
                        {GENDER_LABEL[h.gender] || h.gender} | {h.age_years} ar | {h.distance_optimum}m
                      </div>
                    </td>
                    <td className="py-2.5 text-gray-400 text-xs">{h.stable_name}</td>
                    <td className="py-2.5 text-center">
                      <span className={statColor(h.speed)}>{h.speed}</span>
                    </td>
                    <td className="py-2.5 text-center">
                      <span className={statColor(h.endurance)}>{h.endurance}</span>
                    </td>
                    <td className="py-2.5 text-center">
                      <span className={statColor(h.sprint_strength)}>{h.sprint_strength}</span>
                    </td>
                    <td className="py-2.5 text-center text-gray-300">
                      {h.total_starts}
                    </td>
                    <td className="py-2.5 text-center">
                      <span className="text-trav-gold">{h.total_wins}</span>
                      <span className="text-gray-500">-</span>
                      <span className="text-gray-300">{h.total_seconds}</span>
                      <span className="text-gray-500">-</span>
                      <span className="text-gray-300">{h.total_thirds}</span>
                    </td>
                    <td className="py-2.5 text-right text-gray-300 tabular-nums">
                      {h.best_km_time_display || "-"}
                    </td>
                    <td className="py-2.5 text-right text-trav-gold font-semibold">
                      {formatOre(h.total_earnings)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
