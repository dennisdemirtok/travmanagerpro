"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatOre } from "@/lib/utils";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

const TONES: Record<string, string> = {
  humble: "Ödmjuk", confident: "Självsäker", provocative: "Provokativ",
};

const EVENT_ICONS: Record<string, string> = {
  training_complete: "🏋️",
  injury: "🩹",
  fatigue: "😴",
  recovered: "✅",
  mood_high: "😊",
  mood_low: "😔",
  energy_warning: "⚠️",
};

const STAT_LABELS: Record<string, string> = {
  speed: "Fart", endurance: "Uthållighet", mentality: "Mentalitet",
  start_ability: "Startförmåga", sprint_strength: "Spurt",
  balance: "Balans", strength: "Styrka",
};

const EVENT_COLORS: Record<string, string> = {
  training_complete: "text-green-400",
  injury: "text-red-400",
  fatigue: "text-orange-400",
  recovered: "text-green-400",
  mood_high: "text-blue-400",
  mood_low: "text-amber-400",
  energy_warning: "text-yellow-400",
};

export default function DashboardPage() {
  const queryClient = useQueryClient();
  const { data: stable } = useQuery({ queryKey: ["stable"], queryFn: api.getStable });
  const { data: gameState } = useQuery({ queryKey: ["gameState"], queryFn: api.getGameState });
  const { data: schedule } = useQuery({ queryKey: ["schedule"], queryFn: api.getRaceSchedule });
  const { data: events } = useQuery({ queryKey: ["events"], queryFn: () => api.getEvents() });
  const { data: transactions } = useQuery({ queryKey: ["transactions"], queryFn: () => api.getTransactions({ limit: 5 }) });
  const { data: horses } = useQuery({ queryKey: ["horses"], queryFn: api.getHorses });

  const [prTone, setPrTone] = useState("confident");
  const [prContent, setPrContent] = useState("");
  const [prResult, setPrResult] = useState<any>(null);
  const [showCheckupModal, setShowCheckupModal] = useState(false);
  const [devMsg, setDevMsg] = useState("");

  const checkupMutation = useMutation({
    mutationFn: api.dailyCheckup,
    onSuccess: (data) => {
      setShowCheckupModal(true);
      queryClient.invalidateQueries();
    },
  });

  const prMutation = useMutation({
    mutationFn: () => api.createPressRelease(prTone, prContent),
    onSuccess: (data) => {
      setPrResult(data);
      setPrContent("");
      queryClient.invalidateQueries({ queryKey: ["stable"] });
    },
  });

  const advanceMutation = useMutation({
    mutationFn: () => api.advanceTime(12),
    onSuccess: (data) => {
      setDevMsg(`Spolat 12h → V${data.new_game_week} D${data.new_game_day}`);
      queryClient.invalidateQueries();
    },
    onError: (e: Error) => setDevMsg(`Fel: ${e.message}`),
  });

  const simulateMutation = useMutation({
    mutationFn: () => api.simulateNext(),
    onSuccess: (data) => {
      setDevMsg(`Simulerade ${data.track} V${data.game_week} (${data.races_count} lopp)`);
      queryClient.invalidateQueries();
    },
    onError: (e: Error) => setDevMsg(`Fel: ${e.message}`),
  });

  const tickMutation = useMutation({
    mutationFn: () => api.devTick(),
    onSuccess: () => {
      setDevMsg("Tick klar — kontrollera logg");
      queryClient.invalidateQueries();
    },
    onError: (e: Error) => setDevMsg(`Fel: ${e.message}`),
  });

  const sessions = schedule?.sessions?.filter((s: any) => !s.is_simulated)?.slice(0, 3) || [];
  const txnList = transactions?.transactions || [];
  const eventList = events?.events || [];

  // Stable strength calculations
  const horseList = Array.isArray(horses) ? horses : horses?.horses || [];
  const readyHorses = horseList.filter((h: any) => h.status === "ready");
  const avgForm = horseList.length > 0 ? Math.round(horseList.reduce((s: number, h: any) => s + (h.form || 0), 0) / horseList.length) : 0;
  const avgSpeed = horseList.length > 0 ? Math.round(horseList.reduce((s: number, h: any) => s + (h.speed || 0), 0) / horseList.length) : 0;
  const totalEarnings = horseList.reduce((s: number, h: any) => s + (h.total_earnings || 0), 0);
  const formTrendUp = horseList.filter((h: any) => h.trend === "up").length;
  const formTrendDown = horseList.filter((h: any) => h.trend === "down").length;

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-200">Dashboard</h2>

      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4">
        <Card><div className="text-xs text-gray-500">Saldo</div><div className="text-xl font-bold text-trav-gold">{formatOre(stable?.balance || 0)}</div></Card>
        <Card><div className="text-xs text-gray-500">Hästar</div><div className="text-xl font-bold text-gray-200">{stable?.horse_count || 0}</div></Card>
        <Card><div className="text-xs text-gray-500">Rykte</div><div className="text-xl font-bold text-gray-200">{stable?.reputation || 0}</div></Card>
        <Card><div className="text-xs text-gray-500">Fans</div><div className="text-xl font-bold text-gray-200">{stable?.fan_count || 0}</div></Card>
      </div>

      {/* Stable Strength */}
      {horseList.length > 0 && (
        <Card>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-300">📊 Stallstyrka</h3>
            <span className="text-xs text-gray-500">{readyHorses.length}/{horseList.length} redo</span>
          </div>
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center">
              <div className={`text-lg font-bold ${avgForm >= 60 ? "text-green-400" : avgForm < 40 ? "text-red-400" : "text-yellow-400"}`}>{avgForm}</div>
              <div className="text-[10px] text-gray-500">Snitt Form</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-blue-400">{avgSpeed}</div>
              <div className="text-[10px] text-gray-500">Snitt Fart</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-trav-gold">{formatOre(totalEarnings)}</div>
              <div className="text-[10px] text-gray-500">Total intjäning</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-gray-200 flex items-center justify-center gap-1">
                {formTrendUp > 0 && <span className="text-green-400 text-sm">↑{formTrendUp}</span>}
                {formTrendDown > 0 && <span className="text-red-400 text-sm">↓{formTrendDown}</span>}
                {formTrendUp === 0 && formTrendDown === 0 && <span className="text-gray-500 text-sm">→</span>}
              </div>
              <div className="text-[10px] text-gray-500">Formtrend</div>
            </div>
          </div>
        </Card>
      )}

      {/* Daily checkup */}
      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-gray-300">🐴 Daglig tillsyn</h3>
            <p className="text-xs text-gray-500">Kör stallrunda — kontrollera hästar, träningsresultat och händelser</p>
          </div>
          <Button onClick={() => checkupMutation.mutate()} disabled={checkupMutation.isPending}>
            {checkupMutation.isPending ? "Kör runda..." : "Kör stallrunda"}
          </Button>
        </div>
        {checkupMutation.data && !showCheckupModal && (
          <div className="mt-3 text-xs text-gray-400 flex items-center gap-2">
            <span>{checkupMutation.data.processed} hästar kontrollerade.</span>
            {(checkupMutation.data.events?.length || 0) > 0 && (
              <button onClick={() => setShowCheckupModal(true)} className="text-trav-gold hover:underline">Visa rapport →</button>
            )}
          </div>
        )}
      </Card>

      {/* Stallrunda result modal */}
      {showCheckupModal && checkupMutation.data && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setShowCheckupModal(false)}>
          <div className="bg-trav-card border border-trav-border rounded-xl p-6 w-full max-w-lg max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-200">🐴 Stallrunderapport</h3>
              <span className="text-xs text-gray-500">{checkupMutation.data.processed} hästar kontrollerade</span>
            </div>

            {(checkupMutation.data.events?.length || 0) === 0 ? (
              <div className="text-center py-6">
                <div className="text-3xl mb-2">✅</div>
                <p className="text-gray-400">Allt lugnt i stallet. Inga särskilda händelser idag.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {checkupMutation.data.events.map((e: any, i: number) => (
                  <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-trav-bg border border-trav-border/50">
                    <span className="text-xl">{EVENT_ICONS[e.type] || "📋"}</span>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-gray-200 text-sm">{e.horse}</span>
                        <span className={`text-xs font-medium ${EVENT_COLORS[e.type] || "text-gray-400"}`}>
                          {e.type === "training_complete" && "Träning klar"}
                          {e.type === "injury" && "Skadad"}
                          {e.type === "fatigue" && "Uttröttad"}
                          {e.type === "recovered" && "Återhämtad"}
                        </span>
                      </div>
                      <p className="text-xs text-gray-400 mt-0.5">{e.detail}</p>
                      {e.stat_changes && Object.values(e.stat_changes).some((v: any) => v > 0) && (
                        <div className="flex flex-wrap gap-1.5 mt-1.5">
                          {Object.entries(e.stat_changes as Record<string, number>)
                            .filter(([, v]) => v > 0)
                            .map(([stat, val]) => (
                              <span key={stat} className="text-[10px] px-1.5 py-0.5 rounded bg-green-900/30 text-green-400 border border-green-700/30">
                                {STAT_LABELS[stat] || stat} +{val}
                              </span>
                            ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="mt-5 flex justify-end">
              <Button onClick={() => setShowCheckupModal(false)}>Stäng</Button>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-6">
        {/* Events + Transactions */}
        <Card>
          <h3 className="text-sm font-semibold text-gray-300 mb-3">Senaste händelser</h3>
          {txnList.length === 0 && eventList.length === 0 && <p className="text-xs text-gray-500">Inga händelser än</p>}
          {eventList.slice(0, 3).map((e: any) => (
            <div key={e.id} className="text-xs py-1 border-b border-trav-border last:border-0">
              <span className="text-trav-gold">[{e.event_type}]</span> <span className="text-gray-300">{e.title}</span>
            </div>
          ))}
          {txnList.map((t: any) => (
            <div key={t.id} className="flex justify-between text-xs py-1 border-b border-trav-border last:border-0">
              <span className="text-gray-400">{t.description}</span>
              <span className={t.amount >= 0 ? "text-green-400" : "text-red-400"}>{formatOre(t.amount)}</span>
            </div>
          ))}
        </Card>

        {/* Upcoming races */}
        <Card>
          <h3 className="text-sm font-semibold text-gray-300 mb-3">🏇 Kommande lopp</h3>
          {sessions.length === 0 && <p className="text-xs text-gray-500">Inga kommande lopp</p>}
          {sessions.map((s: any) => {
            const currentTotal = ((gameState?.current_game_week || 1) - 1) * 7 + (gameState?.current_game_day || 1);
            const sessionTotal = ((s.game_week || 1) - 1) * 7 + (s.game_day || 1);
            const daysUntil = sessionTotal - currentTotal;
            const yourEntries = s.races?.reduce((sum: number, r: any) => sum + (r.your_entries?.length || 0), 0) || 0;
            const totalRaces = s.races?.length || 0;
            const startTime = s.start_time || (s.game_day === 6 ? "19:20" : "12:00");

            return (
              <div key={s.id} className="py-2.5 border-b border-trav-border last:border-0">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-gray-300 text-sm flex items-center gap-2">
                      {s.track_name}
                      {(s.is_v75 || (s.start_time === "19:20" && s.game_day === 6)) && (
                        <Badge color="#D4A853">V75</Badge>
                      )}
                    </div>
                    <div className="text-xs text-gray-500">
                      {s.day_name || ""} V{s.game_week} | {s.weather} | Kl {startTime} | {totalRaces} lopp
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={`text-[11px] font-medium px-2 py-0.5 rounded ${
                      daysUntil <= 0 ? "bg-green-900/30 text-green-300 border border-green-700/30" :
                      daysUntil === 1 ? "bg-red-900/30 text-red-300 border border-red-700/30" :
                      daysUntil <= 3 ? "bg-yellow-900/30 text-yellow-300 border border-yellow-700/30" :
                      "bg-blue-900/30 text-blue-300 border border-blue-700/30"
                    }`}>
                      {daysUntil <= 0 ? "Idag" : daysUntil === 1 ? "Imorgon" : `Om ${daysUntil} dagar`}
                    </span>
                    {yourEntries > 0 && (
                      <div className="text-[10px] text-green-400 mt-0.5">{yourEntries} anmäld(a)</div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </Card>
      </div>

      {/* Press release */}
      <Card>
        <h3 className="text-sm font-semibold text-gray-300 mb-3">Pressmeddelande</h3>
        <p className="text-xs text-gray-500 mb-3">Skriv ett pressmeddelande för att öka ditt rykte och locka fans.</p>
        <div className="flex gap-2 mb-2">
          {Object.entries(TONES).map(([k, v]) => (
            <button key={k} onClick={() => setPrTone(k)}
              className={`px-3 py-1 text-xs rounded-full border ${prTone === k ? "border-trav-gold text-trav-gold" : "border-trav-border text-gray-500"}`}>
              {v}
            </button>
          ))}
        </div>
        <textarea value={prContent} onChange={(e) => setPrContent(e.target.value)}
          placeholder="Skriv ditt meddelande här (minst 10 tecken)..."
          className="w-full px-3 py-2 bg-trav-bg border border-trav-border rounded-lg text-gray-200 text-sm h-20 resize-none mb-2" />
        <div className="flex items-center gap-3">
          <Button onClick={() => prMutation.mutate()} disabled={prContent.length < 10 || prMutation.isPending}>
            {prMutation.isPending ? "Publicerar..." : "Publicera"}
          </Button>
          {prResult && (
            <span className={`text-xs ${prResult.backfired ? "text-red-400" : "text-green-400"}`}>
              {prResult.backfired ? "Bakslag!" : "Publicerat!"} Rykte: {prResult.new_reputation} ({prResult.reputation_change >= 0 ? "+" : ""}{prResult.reputation_change})
              {prResult.income > 0 && ` | +${formatOre(prResult.income)}`}
            </span>
          )}
        </div>
      </Card>

      {/* Dev Tools */}
      <Card>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-orange-400">🛠️ Dev-verktyg</h3>
          <span className="text-xs text-gray-500 tabular-nums">
            Speltid: V{gameState?.current_game_week || "?"} D{gameState?.current_game_day || "?"} ({gameState?.total_game_days || 0} dagar)
          </span>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            onClick={() => advanceMutation.mutate()}
            disabled={advanceMutation.isPending}
          >
            {advanceMutation.isPending ? "..." : "⏩ +1 dag (12h)"}
          </Button>
          <Button
            size="sm"
            onClick={() => simulateMutation.mutate()}
            disabled={simulateMutation.isPending}
          >
            {simulateMutation.isPending ? "..." : "🏇 Simulera nästa session"}
          </Button>
          <Button
            size="sm"
            onClick={() => tickMutation.mutate()}
            disabled={tickMutation.isPending}
          >
            {tickMutation.isPending ? "..." : "⚙️ Kör tick"}
          </Button>
        </div>
        {devMsg && (
          <p className="text-xs text-orange-300 mt-2">{devMsg}</p>
        )}
      </Card>
    </div>
  );
}
