"use client";

import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "@/lib/auth";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";

const DAY_NAMES = ["Mandag", "Tisdag", "Onsdag", "Torsdag", "Fredag", "Lordag", "Sondag"];

export function TopBar() {
  const { username, logout } = useAuthStore();
  const router = useRouter();
  const [clock, setClock] = useState("");

  const { data: gameState } = useQuery({
    queryKey: ["gameState"],
    queryFn: api.getGameState,
    refetchInterval: 60000, // Refresh every minute
  });

  // Real-time clock
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
    <header className="h-14 bg-trav-card border-b border-trav-border flex items-center justify-between px-6">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-sm">
          <span className="text-trav-gold font-semibold">Vecka {gameWeek}</span>
          <span className="text-gray-600">|</span>
          <span className="text-gray-300">{dayName}</span>
          <span className="text-gray-600">|</span>
          <span className="text-gray-400 tabular-nums">{clock}</span>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <span className="text-sm text-gray-400">{username}</span>
        <Button variant="ghost" size="sm" onClick={handleLogout}>
          Logga ut
        </Button>
      </div>
    </header>
  );
}
