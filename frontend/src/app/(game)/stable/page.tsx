"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { formatOre, statColor } from "@/lib/utils";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { StatBar } from "@/components/ui/StatBar";
import { MiniChart } from "@/components/ui/MiniChart";
import { useState } from "react";
import { Button } from "@/components/ui/Button";

const STATUS_COLORS: Record<string, string> = {
  ready: "#4ADE80",
  injured: "#F87171",
  resting: "#60A5FA",
  sick: "#FB923C",
  training: "#A855F7",
};

const STATUS_LABELS: Record<string, string> = {
  ready: "Redo",
  injured: "Skadad",
  resting: "Vila",
  sick: "Sjuk",
  training: "Träning",
};

export default function StablePage() {
  const queryClient = useQueryClient();
  const { data: horses, isLoading } = useQuery({ queryKey: ["horses"], queryFn: api.getHorses });
  const { data: stableData } = useQuery({ queryKey: ["stable"], queryFn: api.getStable });
  const { data: gameState } = useQuery({ queryKey: ["gameState"], queryFn: api.getGameState });
  const { data: weeklyCosts } = useQuery({ queryKey: ["weekly-costs"], queryFn: api.getWeeklyCosts });
  const { data: allTracks } = useQuery({ queryKey: ["tracks"], queryFn: api.getTracks });
  const { data: boxInfo } = useQuery({ queryKey: ["box-info"], queryFn: api.getBoxInfo });
  const router = useRouter();
  const [selectedTrack, setSelectedTrack] = useState("");

  const homeTrackMutation = useMutation({
    mutationFn: (trackId: string) => api.setHomeTrack(trackId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["gameState"] });
      queryClient.invalidateQueries({ queryKey: ["stable"] });
    },
  });

  const upgradeMutation = useMutation({
    mutationFn: () => api.upgradeBoxes(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["box-info"] });
      queryClient.invalidateQueries({ queryKey: ["stable"] });
      queryClient.invalidateQueries({ queryKey: ["weekly-costs"] });
    },
  });

  if (isLoading) return <div className="text-gray-500">Laddar...</div>;

  const horseList = Array.isArray(horses) ? horses : horses?.horses || [];

  const tracks = (allTracks || []).map((t: any) => ({
    id: t.id,
    name: `${t.name} (${t.region || t.city})`,
    prestige: t.prestige,
  }));

  const homeTrackName = stableData?.home_track_name || "Inte vald";
  const hasHomeTrack = !!stableData?.home_track_name;
  const costs = weeklyCosts || null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-200">Stall</h2>
        {boxInfo && (
          <div className="flex items-center gap-3">
            <div className="text-sm text-gray-400">
              Boxar: <span className="text-trav-gold font-bold">{boxInfo.current_horses}/{boxInfo.max_horses}</span>
            </div>
            {boxInfo.can_upgrade && (
              <Button
                size="sm"
                variant="secondary"
                onClick={() => { if (confirm(`Uppgradera till ${boxInfo.max_horses + 1} boxar för ${formatOre(boxInfo.next_upgrade_cost)}?`)) upgradeMutation.mutate(); }}
                disabled={upgradeMutation.isPending}
              >
                {upgradeMutation.isPending ? "Uppgraderar..." : `+1 Box (${formatOre(boxInfo.next_upgrade_cost)})`}
              </Button>
            )}
            {!boxInfo.can_upgrade && (
              <Badge color="#22c55e">Max kapacitet</Badge>
            )}
          </div>
        )}
      </div>
      {upgradeMutation.isError && (
        <p className="text-xs text-red-400">{(upgradeMutation.error as Error).message}</p>
      )}

      {/* Home track + Weekly costs row */}
      <div className="grid grid-cols-2 gap-6">
        <Card>
          <h3 className="text-sm font-semibold text-gray-300 mb-2">Hemmabana</h3>
          <p className="text-xs text-gray-500 mb-2">
            Nuvarande: <span className="text-trav-gold">{homeTrackName}</span>
          </p>
          <div className="flex gap-2 items-end">
            <select
              value={selectedTrack}
              onChange={(e) => setSelectedTrack(e.target.value)}
              className="flex-1 px-3 py-2 bg-trav-bg border border-trav-border rounded-lg text-gray-200 text-sm"
            >
              <option value="">Välj hemmabana...</option>
              {tracks.map((t) => (
                <option key={t.id} value={t.id}>{t.name}</option>
              ))}
            </select>
            <Button
              onClick={() => { if (selectedTrack) homeTrackMutation.mutate(selectedTrack); }}
              disabled={!selectedTrack || homeTrackMutation.isPending}
            >
              {homeTrackMutation.isPending ? "Sparar..." : hasHomeTrack ? "Byt" : "Välj"}
            </Button>
          </div>
          {homeTrackMutation.isError && (
            <p className="text-xs text-red-400 mt-2">{(homeTrackMutation.error as Error).message}</p>
          )}
        </Card>

        <Card>
          <h3 className="text-sm font-semibold text-gray-300 mb-2">Veckokostnader (uppskattning)</h3>
          {costs ? (
            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-500">Stallhyra ({costs.horse_count || horseList.length} hästar)</span>
                <span className="text-red-400">{formatOre(costs.stall_rent || 0)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Foder</span>
                <span className="text-red-400">{formatOre(costs.feed_cost || 0)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Personal</span>
                <span className="text-red-400">{formatOre(costs.staff_cost || 0)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Kusklöner</span>
                <span className="text-red-400">{formatOre(costs.driver_salaries || 0)}</span>
              </div>
              <div className="flex justify-between border-t border-trav-border pt-1.5 mt-1.5">
                <span className="text-gray-300 font-semibold">Totalt / vecka</span>
                <span className="text-red-400 font-bold">{formatOre(costs.total || 0)}</span>
              </div>
            </div>
          ) : (
            <p className="text-xs text-gray-500">Laddar...</p>
          )}
        </Card>
      </div>

      {/* Horse list */}
      <div className="space-y-3">
        {horseList.map((h: any) => (
          <Card key={h.id} hoverable onClick={() => router.push(`/stable/${h.id}`)}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div>
                  <div className="font-semibold text-gray-200 flex items-center gap-2">
                    {h.name}
                    {h.trend === "up" && <span className="text-green-400 text-[10px] font-bold px-1 py-0.5 rounded bg-green-900/30 border border-green-700/30">↑</span>}
                    {h.trend === "down" && <span className="text-red-400 text-[10px] font-bold px-1 py-0.5 rounded bg-red-900/30 border border-red-700/30">↓</span>}
                    {h.trend === "stable" && <span className="text-gray-500 text-[10px] font-bold px-1 py-0.5 rounded bg-gray-800/50 border border-gray-700/30">→</span>}
                  </div>
                  <div className="text-xs text-gray-500">
                    {h.age_years} år | {h.gender === "mare" ? "Sto" : h.gender === "stallion" ? "Hingst" : "Valack"}
                    {h.total_starts > 0 && <span className="ml-1">| {h.total_starts} starter ({h.total_wins}–{(h.total_starts - h.total_wins)})</span>}
                  </div>
                </div>
                <Badge color={STATUS_COLORS[h.status] || "#D4A853"}>{STATUS_LABELS[h.status] || h.status}</Badge>
              </div>
              <div className="flex items-center gap-5">
                <div className="w-20"><StatBar value={h.speed} label="Fart" color={statColor(h.speed)} small /></div>
                <div className="w-20"><StatBar value={h.endurance} label="Uthållig." color={statColor(h.endurance)} small /></div>
                <div className="w-20"><StatBar value={h.sprint_strength} label="Spurt" color={statColor(h.sprint_strength)} small /></div>
                <div className="flex items-center gap-2">
                  {h.form_history?.length > 1 && (
                    <MiniChart
                      data={h.form_history}
                      color={h.form >= 60 ? "#4ADE80" : h.form < 40 ? "#F87171" : "#FBBF24"}
                      width={60}
                      height={24}
                    />
                  )}
                  <div className="text-right min-w-[36px]">
                    <div className="text-[10px] text-gray-500">Form</div>
                    <div className={`text-sm font-bold ${h.form >= 60 ? "text-green-400" : h.form < 40 ? "text-red-400" : "text-yellow-400"}`}>{h.form}</div>
                  </div>
                </div>
                <div className="text-right min-w-[60px]">
                  <div className="text-[10px] text-gray-500">Intjäning</div>
                  <div className="text-sm text-trav-gold">{formatOre(h.total_earnings || 0)}</div>
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
