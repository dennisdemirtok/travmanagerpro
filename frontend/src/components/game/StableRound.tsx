"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

const STAT_LABELS: Record<string, string> = {
  speed: "Fart", endurance: "Uthållighet", mentality: "Mentalitet",
  start_ability: "Startförmåga", sprint_strength: "Spurt",
  balance: "Balans", strength: "Styrka",
};

const KIND_COLORS: Record<string, string> = {
  health_scare: "#FB923C",
  form_peak: "#4ADE80",
  caretaker_note: "#7B8CDE",
  equipment_wear: "#FB923C",
  purchase_offer: "#D4A853",
  driver_conflict: "#7B8CDE",
  feed_delay: "#FB923C",
  youngster_breakthrough: "#4ADE80",
};

export function StableRound() {
  const qc = useQueryClient();
  const [report, setReport] = useState<any>(null);
  const [outcomes, setOutcomes] = useState<Record<string, string>>({});

  const { data: pending } = useQuery({
    queryKey: ["pending-events"],
    queryFn: api.getPendingEvents,
  });

  const roundMut = useMutation({
    mutationFn: api.runStableRound,
    onSuccess: (data) => {
      setReport(data);
      qc.invalidateQueries({ queryKey: ["pending-events"] });
      qc.invalidateQueries({ queryKey: ["horses"] });
      qc.invalidateQueries({ queryKey: ["finances"] });
    },
  });

  const resolveMut = useMutation({
    mutationFn: ({ id, choice }: { id: string; choice: string }) => api.resolveEvent(id, choice),
    onSuccess: (data, vars) => {
      setOutcomes((o) => ({ ...o, [vars.id]: data.outcome }));
      qc.invalidateQueries({ queryKey: ["pending-events"] });
      qc.invalidateQueries({ queryKey: ["horses"] });
      qc.invalidateQueries({ queryKey: ["finances"] });
      qc.invalidateQueries({ queryKey: ["stable"] });
    },
  });

  const events: any[] = pending?.events || [];
  const training: any[] = report?.training || [];

  return (
    <Card>
      <div className="flex items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-semibold text-gray-200">Daglig tillsyn</h3>
          <p className="text-xs text-gray-500 mt-0.5">
            Kör stallrundan — träningsresultat och dagens händelser
          </p>
        </div>
        <Button onClick={() => roundMut.mutate()} disabled={roundMut.isPending}>
          {roundMut.isPending ? "Kör runda…" : "Kör stallrunda"}
        </Button>
      </div>

      {report?.already_done && (
        <p className="text-[11px] text-gray-500 mt-3">
          Stallrundan är redan körd i dag. Stega fram till nästa dag för nya händelser.
        </p>
      )}

      {training.length > 0 && (
        <div className="mt-4">
          <div className="section-label mb-2">Dagens träning</div>
          <div className="space-y-1">
            {training.map((t) => (
              <div key={t.horse_id} className="text-xs border-b border-trav-border/40 last:border-0 py-1.5">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-gray-200 font-medium">{t.horse_name}</span>
                  <span className="text-gray-500">{t.label}</span>
                  <span className="text-gray-600 tabular-nums">energi {t.energy}</span>
                  <span className="text-gray-600 tabular-nums">form {t.form}</span>
                  {Object.entries(t.stat_changes || {}).map(([k, v]: any) => (
                    <span key={k} className="text-green-400 font-semibold">
                      {STAT_LABELS[k] || k} +{v}
                    </span>
                  ))}
                  {t.overtrained && (
                    <span className="text-orange-400 font-semibold">Överträning</span>
                  )}
                </div>
                {t.notes?.map((n: string, i: number) => (
                  <p key={i} className="text-[11px] text-gray-500 mt-0.5">· {n}</p>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}

      {events.length > 0 && (
        <div className="mt-4">
          <div className="section-label mb-2">Beslut att fatta ({events.length})</div>
          <div className="space-y-2">
            {events.map((e) => (
              <div
                key={e.id}
                className="rounded-lg border p-3"
                style={{
                  borderColor: (KIND_COLORS[e.kind] || "#252A3A") + "44",
                  backgroundColor: (KIND_COLORS[e.kind] || "#252A3A") + "0D",
                }}
              >
                <div className="text-xs font-semibold" style={{ color: KIND_COLORS[e.kind] || "#E8E6E1" }}>
                  {e.title}
                </div>
                <p className="text-xs text-gray-400 mt-1">{e.description}</p>
                <div className="flex flex-wrap gap-2 mt-2.5">
                  {e.choices.map((c: any) => (
                    <button
                      key={c.key}
                      onClick={() => resolveMut.mutate({ id: e.id, choice: c.key })}
                      disabled={resolveMut.isPending}
                      className="text-left px-2.5 py-1.5 rounded-md bg-trav-active border border-trav-border hover:border-trav-border-light hover:bg-trav-hover transition-colors disabled:opacity-50"
                    >
                      <div className="text-[11px] font-semibold text-gray-200">{c.label}</div>
                      <div className="text-[10px] text-gray-500">{c.detail}</div>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {Object.keys(outcomes).length > 0 && (
        <div className="mt-4">
          <div className="section-label mb-2">Utfall</div>
          {Object.entries(outcomes).map(([id, text]) => (
            <p key={id} className="text-xs text-gray-300 py-1 border-b border-trav-border/40 last:border-0">
              {text}
            </p>
          ))}
        </div>
      )}
    </Card>
  );
}
