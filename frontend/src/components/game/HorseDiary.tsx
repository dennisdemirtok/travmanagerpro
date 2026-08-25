"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

const TYPE_COLORS: Record<string, string> = {
  speed_test: "#7B8CDE",
  equipment_positive: "#4ADE80",
  equipment_negative: "#FB923C",
  condition_positive: "#4ADE80",
  condition_negative: "#FB923C",
  mental_positive: "#4ADE80",
  mental_negative: "#FB923C",
};

const TYPE_LABELS: Record<string, string> = {
  speed_test: "Snabbjobb",
  equipment_positive: "Utrustning",
  equipment_negative: "Utrustning",
  condition_positive: "Förhållanden",
  condition_negative: "Förhållanden",
  mental_positive: "Mentalt",
  mental_negative: "Mentalt",
};

export function HorseDiary({ horseId }: { horseId: string }) {
  const qc = useQueryClient();
  const [noteText, setNoteText] = useState("");
  const [customTag, setCustomTag] = useState("");

  const { data } = useQuery({
    queryKey: ["diary", horseId],
    queryFn: () => api.getHorseDiary(horseId),
  });

  const refresh = () => qc.invalidateQueries({ queryKey: ["diary", horseId] });

  const addNote = useMutation({
    mutationFn: (text: string) => api.addDiaryNote(horseId, text),
    onSuccess: () => { setNoteText(""); refresh(); },
  });
  const delNote = useMutation({
    mutationFn: (id: string) => api.deleteDiaryNote(id),
    onSuccess: refresh,
  });
  const addTag = useMutation({
    mutationFn: (tag: string) => api.addHorseTag(horseId, tag),
    onSuccess: () => { setCustomTag(""); refresh(); },
  });
  const delTag = useMutation({
    mutationFn: (id: string) => api.deleteHorseTag(id),
    onSuccess: refresh,
  });

  if (!data) return <Card><p className="text-xs text-gray-500">Laddar dagbok…</p></Card>;

  const activeTags: string[] = (data.tags || []).map((t: any) => t.tag);
  const suggestions: string[] = (data.suggested_tags || []).filter(
    (t: string) => !activeTags.includes(t)
  );

  return (
    <Card>
      <div className="flex items-baseline justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-200">Hästdagbok</h3>
        <span className="text-[11px] text-gray-500 tabular-nums">
          Självförtroende {data.confidence} · {data.races_last_30_days} starter/30 d ·
          {" "}{data.days_since_last_race} dagar sedan start
        </span>
      </div>

      {/* Taggar */}
      <div className="mb-4">
        <div className="section-label mb-1.5">Dina taggar</div>
        <div className="flex flex-wrap gap-1.5 mb-2">
          {(data.tags || []).map((t: any) => (
            <button
              key={t.id}
              onClick={() => delTag.mutate(t.id)}
              title="Klicka för att ta bort"
              className="px-2 py-0.5 rounded-md text-[11px] font-medium bg-trav-gold/12 border border-trav-gold/30 text-trav-gold hover:bg-red-500/15 hover:border-red-500/40 hover:text-red-300 transition-colors"
            >
              {t.tag} ×
            </button>
          ))}
          {activeTags.length === 0 && (
            <span className="text-[11px] text-gray-600">Inga taggar än</span>
          )}
        </div>
        <div className="flex flex-wrap gap-1.5">
          {suggestions.slice(0, 8).map((t) => (
            <button
              key={t}
              onClick={() => addTag.mutate(t)}
              className="px-2 py-0.5 rounded-md text-[11px] bg-trav-active border border-trav-border text-gray-400 hover:text-gray-200 hover:border-trav-border-light transition-colors"
            >
              + {t}
            </button>
          ))}
        </div>
        <div className="flex gap-2 mt-2">
          <input
            value={customTag}
            onChange={(e) => setCustomTag(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && customTag.trim() && addTag.mutate(customTag)}
            placeholder="Egen tagg…"
            maxLength={40}
            className="flex-1 bg-trav-bg border border-trav-border rounded-md px-2 py-1 text-xs text-gray-200 placeholder:text-gray-600 focus:border-trav-gold/50"
          />
          <Button size="sm" variant="secondary" onClick={() => customTag.trim() && addTag.mutate(customTag)}>
            Lägg till
          </Button>
        </div>
      </div>

      {/* Observationer */}
      <div className="mb-4">
        <div className="section-label mb-1.5">
          Observationer ({data.observations?.length || 0})
        </div>
        {(data.observations || []).length === 0 ? (
          <p className="text-[11px] text-gray-600">
            Inga observationer än. Kör snabbjobb eller starta i lopp så börjar
            hästens egenskaper avslöja sig.
          </p>
        ) : (
          <div className="space-y-1">
            {data.observations.map((o: any) => (
              <div key={o.id} className="flex gap-2 py-1 border-b border-trav-border/40 last:border-0">
                <span
                  className="text-[10px] font-semibold shrink-0 w-20 pt-0.5"
                  style={{ color: TYPE_COLORS[o.type] || "#9AA0AE" }}
                >
                  {TYPE_LABELS[o.type] || "Notering"}
                </span>
                <span className="text-xs text-gray-300 flex-1">{o.text}</span>
                <span className="text-[10px] text-gray-600 shrink-0 tabular-nums">V{o.game_week}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Egna anteckningar */}
      <div>
        <div className="section-label mb-1.5">Egna anteckningar</div>
        <div className="flex gap-2 mb-2">
          <textarea
            value={noteText}
            onChange={(e) => setNoteText(e.target.value)}
            placeholder="Vad lade du märke till?"
            rows={2}
            className="flex-1 bg-trav-bg border border-trav-border rounded-md px-2 py-1.5 text-xs text-gray-200 placeholder:text-gray-600 focus:border-trav-gold/50 resize-none"
          />
          <Button
            size="sm"
            onClick={() => noteText.trim() && addNote.mutate(noteText)}
            disabled={addNote.isPending || !noteText.trim()}
          >
            Spara
          </Button>
        </div>
        <div className="space-y-1">
          {(data.notes || []).map((n: any) => (
            <div key={n.id} className="flex gap-2 py-1 border-b border-trav-border/40 last:border-0 group">
              <span className="text-[10px] text-gray-600 shrink-0 w-10 pt-0.5 tabular-nums">V{n.game_week}</span>
              <span className="text-xs text-gray-300 flex-1 whitespace-pre-wrap">{n.text}</span>
              <button
                onClick={() => delNote.mutate(n.id)}
                className="text-[10px] text-gray-700 hover:text-red-400 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
              >
                ta bort
              </button>
            </div>
          ))}
          {(data.notes || []).length === 0 && (
            <p className="text-[11px] text-gray-600">Inga anteckningar än.</p>
          )}
        </div>
      </div>
    </Card>
  );
}
