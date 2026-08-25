"use client";

import { useState, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/lib/auth";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { formatOre } from "@/lib/utils";

const DAY_NAMES = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag", "Lördag", "Söndag"];

export function TopBar() {
  const { username, logout } = useAuthStore();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [clock, setClock] = useState("");

  const { data: gameState } = useQuery({
    queryKey: ["gameState"],
    queryFn: api.getGameState,
    refetchInterval: 60000,
  });

  const { data: timeMode } = useQuery({
    queryKey: ["timeMode"],
    queryFn: api.getTimeMode,
    staleTime: 5 * 60 * 1000,
  });

  const nextDayMutation = useMutation({
    mutationFn: api.nextDay,
    onSuccess: () => queryClient.invalidateQueries(),
  });

  const { data: finances } = useQuery({
    queryKey: ["finances"],
    queryFn: api.getFinancialOverview,
    refetchInterval: 60000,
  });

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setClock(now.toLocaleTimeString("sv-SE", { hour: "2-digit", minute: "2-digit" }));
    };
    update();
    const interval = setInterval(update, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const gameWeek = gameState?.current_game_week || 1;
  const gameDay = gameState?.current_game_day || 1;
  const dayName = DAY_NAMES[(gameDay - 1) % 7];

  return (
    <header className="h-14 bg-trav-card/80 backdrop-blur-sm border-b border-trav-border flex items-center justify-between px-6 sticky top-0 z-10">
      <div className="flex items-center gap-3">
        {/* Week badge */}
        <div className="flex items-center gap-1.5 bg-trav-gold/10 border border-trav-gold/20 rounded-md px-2.5 py-1">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-trav-gold">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
            <line x1="16" y1="2" x2="16" y2="6" />
            <line x1="8" y1="2" x2="8" y2="6" />
            <line x1="3" y1="10" x2="21" y2="10" />
          </svg>
          <span className="text-xs font-semibold text-trav-gold tabular-nums">V{gameWeek}</span>
        </div>

        <div className="w-px h-4 bg-trav-border" />

        <span className="text-sm font-medium text-gray-300">{dayName}</span>

        <div className="w-px h-4 bg-trav-border" />

        <div className="flex items-center gap-1.5">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-sm text-gray-400 tabular-nums font-medium">{clock}</span>
        </div>

        {timeMode?.manual && (
          <>
            <div className="w-px h-4 bg-trav-border" />
            <button
              onClick={() => nextDayMutation.mutate()}
              disabled={nextDayMutation.isPending}
              title="Stega fram en speldag"
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-trav-gold/10 border border-trav-gold/25 text-trav-gold text-xs font-semibold hover:bg-trav-gold/20 transition-colors disabled:opacity-50"
            >
              {nextDayMutation.isPending ? "Går vidare…" : "Nästa dag →"}
            </button>
          </>
        )}
      </div>

      <div className="flex items-center gap-3">
        {/* Saldo — alltid synligt, färgat efter läge */}
        {finances && (
          <div
            className="flex flex-col items-end leading-tight px-3 py-1 rounded-lg border"
            style={{
              borderColor: balanceTone(finances).border,
              backgroundColor: balanceTone(finances).bg,
            }}
            title={finances.debt?.label || "Saldo"}
          >
            <span
              className="text-sm font-bold tabular-nums"
              style={{ color: balanceTone(finances).text }}
            >
              {formatOre(finances.balance)}
            </span>
            <span className="text-[10px] text-gray-500 tabular-nums">
              −{formatOre(finances.weekly_costs?.total || 0)}/v
            </span>
          </div>
        )}

        <div className="flex items-center gap-2 bg-trav-hover/50 rounded-lg px-3 py-1.5">
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-trav-gold/30 to-trav-gold-dim/30 flex items-center justify-center">
            <span className="text-[10px] font-bold text-trav-gold">{(username || "?")[0].toUpperCase()}</span>
          </div>
          <span className="text-sm font-medium text-gray-300">{username}</span>
        </div>
        <button
          onClick={handleLogout}
          className="text-xs text-gray-500 hover:text-gray-300 transition-colors px-2 py-1.5 rounded-md hover:bg-trav-hover"
        >
          Logga ut
        </button>
      </div>
    </header>
  );
}

function balanceTone(finances: any) {
  const level = finances?.debt?.level || (finances?.balance < 0 ? "warning" : "ok");
  if (level === "critical" || level === "severe")
    return { text: "#F87171", border: "rgba(248,113,113,0.35)", bg: "rgba(248,113,113,0.08)" };
  if (level === "warning")
    return { text: "#FB923C", border: "rgba(251,146,60,0.3)", bg: "rgba(251,146,60,0.07)" };
  if (level === "loan")
    return { text: "#D4A853", border: "rgba(212,168,83,0.28)", bg: "rgba(212,168,83,0.07)" };
  return { text: "#D4A853", border: "rgba(37,42,58,1)", bg: "rgba(26,30,42,0.5)" };
}
