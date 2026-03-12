"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatOre } from "@/lib/utils";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

const POSITIONING = [
  { value: "lead", label: "Ledning" },
  { value: "second", label: "Andra par" },
  { value: "outside", label: "Ytterspar" },
  { value: "trailing", label: "Sista" },
  { value: "back", label: "Bakre" },
];
const TEMPO = [
  { value: "offensive", label: "Offensivt" },
  { value: "balanced", label: "Balanserat" },
  { value: "cautious", label: "Försiktigt" },
];
const SPRINT = [
  { value: "early_600m", label: "Tidigt 600m" },
  { value: "normal_400m", label: "Normalt 400m" },
  { value: "late_250m", label: "Sent 250m" },
];
const SHOES = [
  { value: "normal_steel", label: "Normalsko" },
  { value: "light_aluminum", label: "Lättsko" },
  { value: "barefoot", label: "Barfota" },
];

const DAY_NAMES: Record<number, string> = {
  1: "Mån", 2: "Tis", 3: "Ons", 4: "Tor", 5: "Fre", 6: "Lör", 7: "Sön",
};

export default function RacesPage() {
  const queryClient = useQueryClient();
  const { data: schedule, isLoading } = useQuery({ queryKey: ["schedule"], queryFn: api.getRaceSchedule });
  const { data: horses } = useQuery({ queryKey: ["horses"], queryFn: api.getHorses });
  const { data: drivers } = useQuery({ queryKey: ["drivers"], queryFn: api.getDrivers });
  const { data: gameState } = useQuery({ queryKey: ["gameState"], queryFn: api.getGameState });

  const [tab, setTab] = useState<"anmalan" | "resultat">("anmalan");
  const [filterHorse, setFilterHorse] = useState("");
  const [entryModal, setEntryModal] = useState<any>(null);
  const [selectedHorse, setSelectedHorse] = useState("");
  const [selectedDriver, setSelectedDriver] = useState("");
  const [positioning, setPositioning] = useState("second");
  const [tempo, setTempo] = useState("balanced");
  const [sprint, setSprint] = useState("normal_400m");
  const [shoe, setShoe] = useState("normal_steel");
  const [entryError, setEntryError] = useState("");

  const enterMutation = useMutation({
    mutationFn: (data: { raceId: string; body: any }) => api.enterRace(data.raceId, data.body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["schedule"] });
      setEntryModal(null);
    },
    onError: (err: any) => setEntryError(err.message),
  });

  const handleEnter = () => {
    if (!selectedHorse || !selectedDriver) { setEntryError("Välj häst och kusk"); return; }
    enterMutation.mutate({
      raceId: entryModal.id,
      body: {
        horse_id: selectedHorse,
        driver_id: selectedDriver,
        shoe,
        tactics: { positioning, tempo, sprint_order: sprint, gallop_safety: "normal", curve_strategy: "middle", whip_usage: "normal" },
      },
    });
  };

  if (isLoading) return <div className="text-gray-500">Laddar...</div>;

  const horseList = Array.isArray(horses) ? horses : horses?.horses || [];
  const driverList = Array.isArray(drivers) ? drivers : drivers?.contracted || [];
  const sessions = schedule?.sessions || [];
  const currentWeek = gameState?.current_game_week || 1;
  const currentDay = gameState?.current_game_day || 1;
  const currentTotalDay = gameState?.total_game_days || ((currentWeek - 1) * 7 + currentDay);

  const isDeadlinePassed = (session: any) => {
    const dlWeek = session.entry_deadline_week || session.game_week;
    const dlDay = session.entry_deadline_day || 1;
    const currentTotal = (currentWeek - 1) * 7 + currentDay;
    const deadlineTotal = (dlWeek - 1) * 7 + dlDay;
    return currentTotal >= deadlineTotal;
  };

  const getDaysUntil = (session: any) => {
    const sessionTotalDay = (session.game_week - 1) * 7 + (session.game_day || 1);
    return sessionTotalDay - currentTotalDay;
  };

  const getDaysLabel = (daysUntil: number) => {
    if (daysUntil <= 0) return "Idag";
    if (daysUntil === 1) return "Imorgon";
    return `Om ${daysUntil} dagar`;
  };

  // Split sessions
  const upcomingSessions = sessions.filter((s: any) => !s.is_simulated);
  const finishedSessions = sessions.filter((s: any) => s.is_simulated);
  const displaySessions = tab === "anmalan" ? upcomingSessions : finishedSessions;

  // Horse filter: find races that match selected horse
  const selectedFilterHorse = horseList.find((h: any) => h.id === filterHorse);

  const isRaceEligible = (race: any, session: any) => {
    if (!selectedFilterHorse) return true;
    if (selectedFilterHorse.status !== "ready") return false;
    if (race.your_entries?.length > 0) return false; // already entered
    if (isDeadlinePassed(session)) return false;
    if (race.min_start_points > 0 && (selectedFilterHorse.start_points || 0) < race.min_start_points) return false;
    return true;
  };

  return (
    <div className="space-y-6">
      {/* Header with tabs */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-200">Loppschema</h2>
        <div className="flex gap-1 bg-trav-dark-2 rounded-lg p-0.5">
          <button
            onClick={() => setTab("anmalan")}
            className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${
              tab === "anmalan" ? "bg-trav-gold text-black" : "text-gray-400 hover:text-white"
            }`}
          >
            Anmälan ({upcomingSessions.length})
          </button>
          <button
            onClick={() => setTab("resultat")}
            className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${
              tab === "resultat" ? "bg-trav-gold text-black" : "text-gray-400 hover:text-white"
            }`}
          >
            Resultat ({finishedSessions.length})
          </button>
        </div>
      </div>

      {/* Horse filter (only on anmälan tab) */}
      {tab === "anmalan" && (
        <Card>
          <div className="flex items-center gap-3">
            <label className="text-sm text-gray-400 whitespace-nowrap">Filtrera per häst:</label>
            <select
              value={filterHorse}
              onChange={(e) => setFilterHorse(e.target.value)}
              className="flex-1 px-3 py-2 bg-trav-bg border border-trav-border rounded-lg text-gray-200 text-sm"
            >
              <option value="">Alla lopp</option>
              {horseList
                .filter((h: any) => h.status === "ready")
                .map((h: any) => (
                  <option key={h.id} value={h.id}>
                    {h.name} (Form: {h.form}, SP: {h.start_points || 0})
                  </option>
                ))}
            </select>
            {selectedFilterHorse && (
              <span className="text-xs text-gray-500">
                {selectedFilterHorse.name} — Startpoäng: {selectedFilterHorse.start_points || 0}
              </span>
            )}
          </div>
        </Card>
      )}

      {/* Sessions */}
      {displaySessions.length === 0 && (
        <Card>
          <p className="text-sm text-gray-500 text-center py-4">
            {tab === "anmalan" ? "Inga kommande lopp just nu" : "Inga avslutade lopp att visa"}
          </p>
        </Card>
      )}

      {displaySessions.map((session: any) => {
        const deadlinePassed = isDeadlinePassed(session);
        const isV75 = session.is_v75 || (session.start_time === "19:20" && session.game_day === 6);
        const startTime = session.start_time || (session.game_day === 6 ? "19:20" : "12:00");
        const daysUntil = getDaysUntil(session);

        // Filter races by horse eligibility if a horse is selected
        const visibleRaces = filterHorse
          ? session.races?.filter((r: any) => isRaceEligible(r, session)) || []
          : session.races || [];

        // Don't show session if all races are filtered out
        if (filterHorse && visibleRaces.length === 0) return null;

        return (
          <Card key={session.id}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <div>
                  <div className="font-semibold text-gray-200">{session.track_name}</div>
                  <div className="text-xs text-gray-500">
                    {session.day_name || DAY_NAMES[session.game_day] || "Okänd"} V{session.game_week} | {session.track_city} | {session.weather} | Kl {startTime}
                    {session.track_region && <span className="ml-1 text-gray-600">({session.track_region})</span>}
                  </div>
                </div>
                {isV75 && <Badge color="#D4A853">V75</Badge>}
                {session.travel_distance != null && session.travel_distance > 0 && (
                  <span className="text-[10px] px-2 py-0.5 rounded bg-orange-900/20 text-orange-300 border border-orange-700/30">
                    Resa: {formatOre(session.travel_cost || 0)}
                  </span>
                )}
              </div>
              <div className="text-right flex items-center gap-2">
                {session.is_simulated ? (
                  <Badge color="#4ADE80">Avslutad</Badge>
                ) : deadlinePassed ? (
                  <Badge color="#FBBF24">Väntar på start</Badge>
                ) : (
                  <>
                    <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                      daysUntil <= 1 ? "bg-red-900/30 text-red-300 border border-red-700/30" :
                      daysUntil <= 3 ? "bg-yellow-900/30 text-yellow-300 border border-yellow-700/30" :
                      "bg-blue-900/30 text-blue-300 border border-blue-700/30"
                    }`}>
                      {getDaysLabel(daysUntil)}
                    </span>
                    <div className="text-[10px] text-gray-600">
                      DL: V{session.entry_deadline_week} D{session.entry_deadline_day}
                    </div>
                  </>
                )}
              </div>
            </div>
            <div className="space-y-2">
              {visibleRaces.map((race: any) => (
                <div key={race.id} className="flex items-center justify-between p-3 bg-trav-bg rounded-lg">
                  <div>
                    <div className="text-sm text-gray-300 flex items-center gap-2">
                      {race.race_name} - {race.distance}m ({race.start_method})
                      {race.race_class === "gold" && <Badge color="#D4A853">Guld</Badge>}
                      {race.race_class === "silver" && <Badge color="#C0C0C0">Silver</Badge>}
                      {(race.race_class === "age_2" || race.race_class === "age_3") && (
                        <Badge color="#60A5FA">{race.race_class === "age_2" ? "2-åringar" : "3-åringar"}</Badge>
                      )}
                    </div>
                    <div className="text-xs text-gray-500">
                      {formatOre(race.prize_pool)} | {race.current_entries}/{race.max_entries} anmälda
                      {race.min_start_points > 0 && (
                        <span className="text-yellow-400 ml-2">Min {race.min_start_points} poäng</span>
                      )}
                      {race.entry_fee > 0 && (
                        <span className="text-gray-400 ml-2">Anm.avg: {formatOre(race.entry_fee)}</span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {race.your_entries?.length > 0 && <Badge color="#4ADE80">Anmäld</Badge>}
                    {!session.is_simulated && !deadlinePassed && !race.your_entries?.length && (
                      <Button size="sm" onClick={() => {
                        setEntryModal({ ...race, session });
                        setEntryError("");
                        if (filterHorse) setSelectedHorse(filterHorse);
                      }}>Anmäl</Button>
                    )}
                    {session.is_simulated && (
                      <a href={`/races/${race.id}`} className="text-sm text-trav-gold hover:underline">Resultat</a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        );
      })}

      {/* Entry Modal */}
      {entryModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setEntryModal(null)}>
          <div className="bg-trav-card border border-trav-border rounded-xl p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-gray-200 mb-4">Anmäl till lopp</h3>
            <div className="text-sm text-gray-400 mb-2">{entryModal.race_name} - {entryModal.distance}m | {formatOre(entryModal.prize_pool)}</div>
            {entryModal.min_start_points > 0 && (
              <div className="text-xs text-yellow-400 mb-2">Krav: minst {entryModal.min_start_points} startpoäng</div>
            )}
            {entryModal.session?.travel_cost > 0 && (
              <div className="text-xs text-orange-400 mb-4">
                Resekostnad: {formatOre(entryModal.session.travel_cost)} (avstånd: {entryModal.session.travel_distance} regioner)
              </div>
            )}

            <div className="space-y-3">
              <div>
                <label className="text-xs text-gray-500 block mb-1">Häst</label>
                <select value={selectedHorse} onChange={(e) => setSelectedHorse(e.target.value)} className="w-full px-3 py-2 bg-trav-bg border border-trav-border rounded-lg text-gray-200">
                  <option value="">Välj häst...</option>
                  {horseList.filter((h: any) => h.status === "ready").map((h: any) => <option key={h.id} value={h.id}>{h.name} (Form: {h.form})</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">Kusk</label>
                <select value={selectedDriver} onChange={(e) => setSelectedDriver(e.target.value)} className="w-full px-3 py-2 bg-trav-bg border border-trav-border rounded-lg text-gray-200">
                  <option value="">Välj kusk...</option>
                  {driverList.map((d: any) => {
                    const isBooked = entryModal.session?.booked_driver_ids?.includes(d.id);
                    return (
                      <option key={d.id} value={d.id} disabled={isBooked}>
                        {d.name} ({d.commission_rate ? Math.round(d.commission_rate * 100) : 10}% provision){isBooked ? " (upptagen)" : ""}
                      </option>
                    );
                  })}
                </select>
              </div>
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Position</label>
                  <select value={positioning} onChange={(e) => setPositioning(e.target.value)} className="w-full px-2 py-1.5 bg-trav-bg border border-trav-border rounded text-sm text-gray-200">
                    {POSITIONING.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Tempo</label>
                  <select value={tempo} onChange={(e) => setTempo(e.target.value)} className="w-full px-2 py-1.5 bg-trav-bg border border-trav-border rounded text-sm text-gray-200">
                    {TEMPO.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Spurt</label>
                  <select value={sprint} onChange={(e) => setSprint(e.target.value)} className="w-full px-2 py-1.5 bg-trav-bg border border-trav-border rounded text-sm text-gray-200">
                    {SPRINT.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </div>
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">Skor</label>
                <select value={shoe} onChange={(e) => setShoe(e.target.value)} className="w-full px-3 py-2 bg-trav-bg border border-trav-border rounded-lg text-gray-200">
                  {SHOES.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </div>
            </div>

            {entryError && <p className="text-red-400 text-sm mt-3">{entryError}</p>}

            <div className="flex justify-end gap-3 mt-5">
              <Button variant="secondary" onClick={() => setEntryModal(null)}>Avbryt</Button>
              <Button onClick={handleEnter} disabled={enterMutation.isPending}>
                {enterMutation.isPending ? "Anmäler..." : "Anmäl"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
