"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

export default function BalancePage() {
  const [runs, setRuns] = useState(100);
  const [stretch, setStretch] = useState("medium");
  const [seed, setSeed] = useState(20260101);
  const [run, setRun] = useState(0);

  const { data, isFetching, error } = useQuery({
    queryKey: ["balance", run],
    queryFn: () => api.runBalanceTest({ runs, stretch_class: stretch, seed }),
    enabled: run > 0,
  });

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-xl font-bold text-gray-200 tracking-tight">Balansverktyg</h2>
        <p className="text-xs text-gray-500 mt-1">
          Kör N lopp med ett medvetet jämnt fält och mät hur taktikvalen presterar.
          Målet: ingen position/tempo-kombination ska vinna över 30 %.
        </p>
      </div>

      <Card>
        <div className="flex flex-wrap items-end gap-3">
          <label className="text-xs">
            <span className="block text-gray-500 mb-1">Antal lopp</span>
            <input
              type="number" min={10} max={500} step={10}
              value={runs} onChange={(e) => setRuns(Number(e.target.value))}
              className="w-24 bg-trav-bg border border-trav-border rounded-md px-2 py-1 text-gray-200"
            />
          </label>
          <label className="text-xs">
            <span className="block text-gray-500 mb-1">Upplopp</span>
            <select
              value={stretch} onChange={(e) => setStretch(e.target.value)}
              className="bg-trav-bg border border-trav-border rounded-md px-2 py-1 text-gray-200"
            >
              <option value="short">Kort (140 m)</option>
              <option value="medium">Normalt (200 m)</option>
              <option value="long">Långt (320 m)</option>
            </select>
          </label>
          <label className="text-xs">
            <span className="block text-gray-500 mb-1">Seed</span>
            <input
              type="number" value={seed} onChange={(e) => setSeed(Number(e.target.value))}
              className="w-32 bg-trav-bg border border-trav-border rounded-md px-2 py-1 text-gray-200"
            />
          </label>
          <Button onClick={() => setRun((r) => r + 1)} disabled={isFetching}>
            {isFetching ? "Simulerar…" : "Kör test"}
          </Button>
        </div>
        {error && <p className="text-xs text-red-400 mt-2">{(error as Error).message}</p>}
      </Card>

      {data && (
        <>
          <div
            className="rounded-xl border px-4 py-3"
            style={{
              borderColor: data.passes ? "#4ADE8044" : "#EF444455",
              backgroundColor: data.passes ? "#4ADE800D" : "#EF444412",
            }}
          >
            <div
              className="text-sm font-semibold"
              style={{ color: data.passes ? "#4ADE80" : "#EF4444" }}
            >
              {data.verdict}
            </div>
            <div className="text-[11px] text-gray-500 mt-1 tabular-nums">
              {data.runs} lopp · {data.field_size} hästar · {data.distance} m ·
              {" "}spridning {data.spread} procentenheter ·
              {" "}förväntat {data.expected_win_pct} % per häst ·
              {" "}galopp {data.gallop_rate} % · disk {data.dq_rate} % ·
              {" "}snittvinnartid {data.avg_winning_km_time} s/km
            </div>
          </div>

          <Card>
            <div className="section-label mb-3">Vinstprocent per taktikkombination</div>
            <div className="space-y-1.5">
              {data.combos.map((c: any) => (
                <div key={c.label} className="flex items-center gap-3 text-xs">
                  <span className="w-52 shrink-0 text-gray-300">{c.label}</span>
                  <div className="flex-1 h-4 bg-trav-border/50 rounded overflow-hidden relative">
                    <div
                      className="h-full rounded"
                      style={{
                        width: `${Math.min(100, c.win_pct * 2.5)}%`,
                        backgroundColor: c.win_pct > 30 ? "#EF4444"
                          : c.win_pct === 0 ? "#4B5563" : "#D4A853",
                      }}
                    />
                    <span
                      className="absolute inset-y-0 left-1.5 flex items-center text-[10px] font-bold tabular-nums"
                      style={{ color: c.win_pct > 12 ? "#0B0E14" : "#9AA0AE" }}
                    >
                      {c.win_pct} %
                    </span>
                  </div>
                  <span className="w-28 shrink-0 text-right text-gray-600 tabular-nums">
                    {c.wins}/{c.starts} · pall {c.podium_pct} %
                  </span>
                </div>
              ))}
            </div>
            <p className="text-[10px] text-gray-600 mt-3">
              Röd stapel = över 30 %-gränsen. Grå = kombinationen vann aldrig.
            </p>
          </Card>
        </>
      )}
    </div>
  );
}
