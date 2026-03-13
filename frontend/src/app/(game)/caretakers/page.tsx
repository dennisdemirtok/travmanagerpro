"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatOre } from "@/lib/utils";
import { Card } from "@/components/ui/Card";
import { StatBar } from "@/components/ui/StatBar";
import { SkillBars } from "@/components/ui/SkillBars";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

const SPECIALTY_LABELS: Record<string, string> = {
  speed: "Fart",
  endurance: "Uthållighet",
  mentality: "Mentalitet",
  start_ability: "Startsnabbhet",
  sprint_strength: "Spurtstyrka",
  balance: "Balans",
  strength: "Styrka",
};

const PERSONALITY_LABELS: Record<string, string> = {
  meticulous: "Noggrann",
  calm: "Lugn",
  energetic: "Energisk",
  experienced: "Erfaren",
  strict: "Sträng",
  gentle: "Mjuk",
};

const COMPAT_COLORS: Record<string, string> = {
  "Utmärkt": "#4ADE80",
  "Bra": "#D4A853",
  "OK": "#FB923C",
  "Dålig": "#F87171",
  "Mycket dålig": "#EF4444",
};

export default function CaretakersPage() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["caretakers"], queryFn: api.getCaretakers });
  const { data: horses } = useQuery({ queryKey: ["horses"], queryFn: api.getHorses });
  const [tab, setTab] = useState<"assignments" | "market">("market");
  const [scoutModal, setScoutModal] = useState<any>(null);
  const [selectedScoutHorse, setSelectedScoutHorse] = useState("");
  const [hireModal, setHireModal] = useState<any>(null);
  const [selectedHireHorse, setSelectedHireHorse] = useState("");
  const [offeredSalary, setOfferedSalary] = useState(0);
  const [hireResult, setHireResult] = useState<any>(null);
  const [scoutResult, setScoutResult] = useState<any>(null);

  const scoutMutation = useMutation({
    mutationFn: (data: { caretakerId: string; horseId: string }) =>
      api.scoutCaretaker(data.caretakerId, data.horseId),
    onSuccess: (result) => {
      setScoutResult(result);
      queryClient.invalidateQueries({ queryKey: ["caretakers"] });
    },
  });

  const hireMutation = useMutation({
    mutationFn: (data: { caretakerId: string; horseId: string; salary: number }) =>
      api.hireCaretaker(data.caretakerId, data.horseId, data.salary),
    onSuccess: (result) => {
      setHireResult(result);
      if (result.accepted) {
        queryClient.invalidateQueries({ queryKey: ["caretakers"] });
        queryClient.invalidateQueries({ queryKey: ["horses"] });
      }
    },
  });

  const fireMutation = useMutation({
    mutationFn: (assignmentId: string) => api.fireCaretaker(assignmentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["caretakers"] });
      queryClient.invalidateQueries({ queryKey: ["horses"] });
    },
  });

  if (isLoading) return <div className="text-gray-500">Laddar...</div>;

  const available = data?.available || [];
  const assignments = data?.assignments || [];
  const scoutReports = data?.scout_reports || [];
  const horseList = Array.isArray(horses) ? horses : horses?.horses || [];

  // Get scout report for a specific caretaker-horse pair
  const getReport = (caretakerId: string, horseId: string) =>
    scoutReports.find((r: any) => r.caretaker_id === caretakerId && r.horse_id === horseId);

  // Check if horse already has a caretaker
  const horseHasCaretaker = (horseId: string) =>
    assignments.some((a: any) => a.horse_id === horseId);

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-200">Skötare</h2>

      {/* Tabs */}
      <div className="flex gap-1 bg-trav-dark-2 rounded-lg p-0.5 w-fit">
        <button
          onClick={() => setTab("market")}
          className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${
            tab === "market" ? "bg-trav-gold text-black" : "text-gray-400 hover:text-white"
          }`}
        >
          Skötarmarknad ({available.length})
        </button>
        <button
          onClick={() => setTab("assignments")}
          className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${
            tab === "assignments" ? "bg-trav-gold text-black" : "text-gray-400 hover:text-white"
          }`}
        >
          Mina skötare ({assignments.length})
        </button>
      </div>

      {/* Info box */}
      {tab === "market" && (
        <Card>
          <div className="text-xs text-gray-500">
            <span className="text-trav-gold font-medium">Tips:</span> Granska en skötare för att se kompatibilitet med din häst (750 kr).
            Bra kompatibilitet ger bonus på hästens egenskaper (+1 till +3 bars). Olika skötare specialiserar sig på olika egenskaper.
          </div>
        </Card>
      )}

      {/* ======= MARKET TAB ======= */}
      {tab === "market" && (
        <div className="space-y-3">
          {available.length === 0 && (
            <Card>
              <p className="text-sm text-gray-500 text-center py-4">Inga skötare tillgängliga just nu</p>
            </Card>
          )}
          {available.map((c: any) => (
            <Card key={c.id}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-gray-200">{c.name}</span>
                    <Badge color={COMPAT_COLORS["OK"] || "#888"}>
                      {PERSONALITY_LABELS[c.personality] || c.personality}
                    </Badge>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    Specialitet: <span className="text-trav-gold">{SPECIALTY_LABELS[c.primary_specialty] || c.primary_specialty}</span>
                    {c.secondary_specialty && (
                      <span> + <span className="text-gray-300">{SPECIALTY_LABELS[c.secondary_specialty]}</span></span>
                    )}
                  </div>
                  <div className="mt-2 w-48">
                    <StatBar value={c.skill} label="Skicklighet" />
                  </div>
                </div>
                <div className="text-right flex flex-col items-end gap-2">
                  <div>
                    <div className="text-sm text-trav-gold">{formatOre(c.salary_demand)}/vecka</div>
                    <div className="text-[10px] text-gray-500">Rekommenderad lön</div>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="secondary" onClick={() => {
                      setScoutModal(c);
                      setSelectedScoutHorse("");
                      setScoutResult(null);
                    }}>
                      Granska
                    </Button>
                    <Button size="sm" onClick={() => {
                      setHireModal(c);
                      setSelectedHireHorse("");
                      setOfferedSalary(c.salary_demand);
                      setHireResult(null);
                    }}>
                      Anställ
                    </Button>
                  </div>
                </div>
              </div>

              {/* Show any existing scout reports for this caretaker */}
              {scoutReports.filter((r: any) => r.caretaker_id === c.id).length > 0 && (
                <div className="mt-3 pt-3 border-t border-trav-border/50">
                  <div className="text-[10px] text-gray-600 mb-1.5">Granskningar:</div>
                  <div className="flex flex-wrap gap-2">
                    {scoutReports
                      .filter((r: any) => r.caretaker_id === c.id)
                      .map((r: any) => {
                        const horse = horseList.find((h: any) => h.id === r.horse_id);
                        return (
                          <div key={r.horse_id} className="flex items-center gap-1.5 text-xs bg-trav-bg rounded px-2 py-1">
                            <span className="text-gray-400">{horse?.name || "Häst"}</span>
                            <span
                              className="font-bold"
                              style={{ color: COMPAT_COLORS[r.compatibility_label] || "#888" }}
                            >
                              {r.compatibility_label} ({r.compatibility_score})
                            </span>
                            {r.primary_boost > 0 && (
                              <span className="text-green-400">+{r.primary_boost}</span>
                            )}
                          </div>
                        );
                      })}
                  </div>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}

      {/* ======= ASSIGNMENTS TAB ======= */}
      {tab === "assignments" && (
        <div className="space-y-3">
          {assignments.length === 0 && (
            <Card>
              <p className="text-sm text-gray-500 text-center py-4">
                Inga skötare anställda. Gå till Skötarmarknaden för att hitta en.
              </p>
            </Card>
          )}
          {assignments.map((a: any) => (
            <Card key={a.assignment_id}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-gray-200">{a.caretaker?.name}</span>
                    <span className="text-xs text-gray-500">→</span>
                    <span className="text-sm text-trav-gold">{a.horse_name}</span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {PERSONALITY_LABELS[a.caretaker?.personality] || ""} |
                    Specialitet: {SPECIALTY_LABELS[a.caretaker?.primary_specialty] || ""}
                    {a.caretaker?.secondary_specialty && ` + ${SPECIALTY_LABELS[a.caretaker.secondary_specialty]}`}
                  </div>

                  {/* Compatibility */}
                  {a.compatibility_score != null && (
                    <div className="flex items-center gap-3 mt-2">
                      <div className="flex items-center gap-1.5">
                        <span className="text-[10px] text-gray-500">Kompatibilitet:</span>
                        <SkillBars rating={Math.round(a.compatibility_score / 5)} compact />
                        <span
                          className="text-xs font-bold"
                          style={{ color: COMPAT_COLORS[a.compatibility_label] || "#888" }}
                        >
                          {a.compatibility_label}
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Stat boosts */}
                  {a.stat_boosts && Object.keys(a.stat_boosts).length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-2">
                      {Object.entries(a.stat_boosts).map(([stat, boost]: [string, any]) => (
                        <div key={stat} className="flex items-center gap-1 text-xs bg-green-900/20 border border-green-700/30 rounded px-2 py-0.5">
                          <span className="text-gray-400">{SPECIALTY_LABELS[stat] || stat}</span>
                          <span className="text-green-400 font-bold">+{boost}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <div className="text-right flex flex-col items-end gap-2">
                  <div className="text-sm text-trav-gold">{formatOre(a.salary_per_week)}/vecka</div>
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => {
                      if (confirm("Avskeda denna skötare?")) fireMutation.mutate(a.assignment_id);
                    }}
                  >
                    Avskeda
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* ======= SCOUT MODAL ======= */}
      {scoutModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setScoutModal(null)}>
          <div className="bg-trav-card border border-trav-border rounded-xl p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-gray-200 mb-1">Granska skötare</h3>
            <div className="text-sm text-gray-400 mb-4">{scoutModal.name} — {PERSONALITY_LABELS[scoutModal.personality]}</div>

            <div className="space-y-3">
              <div>
                <label className="text-xs text-gray-500 block mb-1">Välj häst att granska för</label>
                <select
                  value={selectedScoutHorse}
                  onChange={(e) => { setSelectedScoutHorse(e.target.value); setScoutResult(null); }}
                  className="w-full px-3 py-2 bg-trav-bg border border-trav-border rounded-lg text-gray-200"
                >
                  <option value="">Välj häst...</option>
                  {horseList.map((h: any) => {
                    const report = getReport(scoutModal.id, h.id);
                    const hasCaretaker = horseHasCaretaker(h.id);
                    return (
                      <option key={h.id} value={h.id} disabled={hasCaretaker}>
                        {h.name}{report ? ` (redan granskad: ${report.compatibility_label})` : ""}{hasCaretaker ? " (har skötare)" : ""}
                      </option>
                    );
                  })}
                </select>
              </div>

              {/* Already-scouted info */}
              {selectedScoutHorse && getReport(scoutModal.id, selectedScoutHorse) && !scoutResult && (
                <div className="bg-trav-bg rounded-lg p-3 border border-trav-border/50">
                  <div className="text-xs text-gray-500 mb-1">Redan granskad:</div>
                  {(() => {
                    const r = getReport(scoutModal.id, selectedScoutHorse);
                    return (
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold" style={{ color: COMPAT_COLORS[r.compatibility_label] || "#888" }}>
                          {r.compatibility_label} ({r.compatibility_score}/100)
                        </span>
                        {r.primary_boost > 0 && (
                          <span className="text-xs text-green-400">
                            +{r.primary_boost} {SPECIALTY_LABELS[scoutModal.primary_specialty]}
                          </span>
                        )}
                      </div>
                    );
                  })()}
                </div>
              )}

              {/* Scout result */}
              {scoutResult && !scoutResult.error && (
                <div className="bg-trav-bg rounded-lg p-4 border border-trav-border/50 space-y-2">
                  <div className="text-xs font-semibold text-gray-400">Granskning:</div>
                  <div className="flex items-center gap-3">
                    <SkillBars rating={Math.round(scoutResult.compatibility_score / 5)} label="Kompatibilitet" />
                    <span className="text-sm font-bold" style={{ color: COMPAT_COLORS[scoutResult.compatibility_label] || "#888" }}>
                      {scoutResult.compatibility_label}
                    </span>
                  </div>

                  {scoutResult.stat_boosts && Object.keys(scoutResult.stat_boosts).length > 0 && (
                    <div className="pt-2 border-t border-trav-border/30">
                      <div className="text-[10px] text-gray-500 mb-1">Statbonusar vid anställning:</div>
                      {Object.entries(scoutResult.stat_boosts).map(([stat, boost]: [string, any]) => (
                        <div key={stat} className="flex items-center gap-2 text-sm">
                          <span className="text-gray-400">{SPECIALTY_LABELS[stat]}</span>
                          <span className="text-green-400 font-bold">+{boost}</span>
                          <span className="text-[10px] text-gray-600">(~{Math.round(boost / 5)} bars)</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {scoutResult.stat_boosts && Object.keys(scoutResult.stat_boosts).length === 0 && (
                    <div className="text-xs text-red-400">Kompatibiliteten är för låg för att ge bonusar.</div>
                  )}

                  {!scoutResult.already_scouted && (
                    <div className="text-[10px] text-gray-600 pt-1">Kostnad: {formatOre(scoutResult.cost || 75000)}</div>
                  )}
                </div>
              )}

              <div className="text-xs text-gray-500">Granskning kostar 750 kr per häst.</div>
            </div>

            <div className="flex justify-end gap-3 mt-5">
              <Button variant="secondary" onClick={() => setScoutModal(null)}>Stäng</Button>
              <Button
                onClick={() => scoutMutation.mutate({ caretakerId: scoutModal.id, horseId: selectedScoutHorse })}
                disabled={!selectedScoutHorse || scoutMutation.isPending}
              >
                {scoutMutation.isPending ? "Granskar..." : "Granska (750 kr)"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* ======= HIRE MODAL ======= */}
      {hireModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setHireModal(null)}>
          <div className="bg-trav-card border border-trav-border rounded-xl p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-gray-200 mb-1">Anställ skötare</h3>
            <div className="text-sm text-gray-400 mb-4">
              {hireModal.name} — {SPECIALTY_LABELS[hireModal.primary_specialty]}
              {hireModal.secondary_specialty && ` + ${SPECIALTY_LABELS[hireModal.secondary_specialty]}`}
            </div>

            {hireResult ? (
              <div className="space-y-3">
                {hireResult.accepted ? (
                  <div className="bg-green-900/20 border border-green-700/30 rounded-lg p-4">
                    <div className="text-green-400 font-bold mb-1">Accepterat!</div>
                    <div className="text-sm text-gray-300">{hireResult.message}</div>
                    <div className="text-xs text-gray-500 mt-2">
                      Lön: {formatOre(hireResult.salary_per_week)}/vecka | Signeringsavgift: {formatOre(hireResult.signing_fee)}
                    </div>
                  </div>
                ) : (
                  <div className="bg-red-900/20 border border-red-700/30 rounded-lg p-4">
                    <div className="text-red-400 font-bold mb-1">Avvisat</div>
                    <div className="text-sm text-gray-300">{hireResult.message}</div>
                  </div>
                )}
                <div className="flex justify-end">
                  <Button variant="secondary" onClick={() => { setHireModal(null); setHireResult(null); }}>Stäng</Button>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Välj häst</label>
                  <select
                    value={selectedHireHorse}
                    onChange={(e) => setSelectedHireHorse(e.target.value)}
                    className="w-full px-3 py-2 bg-trav-bg border border-trav-border rounded-lg text-gray-200"
                  >
                    <option value="">Välj häst...</option>
                    {horseList.map((h: any) => {
                      const hasCaretaker = horseHasCaretaker(h.id);
                      const report = getReport(hireModal.id, h.id);
                      return (
                        <option key={h.id} value={h.id} disabled={hasCaretaker}>
                          {h.name}
                          {report ? ` (${report.compatibility_label})` : " (ej granskad)"}
                          {hasCaretaker ? " (har skötare)" : ""}
                        </option>
                      );
                    })}
                  </select>
                </div>

                {/* Show scout report if available */}
                {selectedHireHorse && getReport(hireModal.id, selectedHireHorse) && (
                  <div className="bg-trav-bg rounded-lg p-3 border border-trav-border/50">
                    {(() => {
                      const r = getReport(hireModal.id, selectedHireHorse);
                      return (
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-gray-500">Kompatibilitet:</span>
                          <span className="text-sm font-bold" style={{ color: COMPAT_COLORS[r.compatibility_label] || "#888" }}>
                            {r.compatibility_label} ({r.compatibility_score}/100)
                          </span>
                          {r.primary_boost > 0 && (
                            <span className="text-xs text-green-400">+{r.primary_boost} {SPECIALTY_LABELS[hireModal.primary_specialty]}</span>
                          )}
                        </div>
                      );
                    })()}
                  </div>
                )}

                {selectedHireHorse && !getReport(hireModal.id, selectedHireHorse) && (
                  <div className="text-xs text-orange-400 flex items-center gap-1">
                    ⚠️ Hästen är inte granskad. Granska först för att se kompatibilitet.
                  </div>
                )}

                <div>
                  <label className="text-xs text-gray-500 block mb-1">Erbjuden lön (öre/vecka)</label>
                  <input
                    type="number"
                    value={offeredSalary}
                    onChange={(e) => setOfferedSalary(Number(e.target.value))}
                    className="w-full px-3 py-2 bg-trav-bg border border-trav-border rounded-lg text-gray-200"
                    step={10000}
                  />
                  <div className="text-[10px] text-gray-500 mt-1">
                    Rekommenderad: {formatOre(hireModal.salary_demand)}/vecka |
                    Signeringsavgift: {formatOre(offeredSalary * 2)}
                  </div>
                </div>

                <div className="flex justify-end gap-3 mt-5">
                  <Button variant="secondary" onClick={() => setHireModal(null)}>Avbryt</Button>
                  <Button
                    onClick={() =>
                      hireMutation.mutate({
                        caretakerId: hireModal.id,
                        horseId: selectedHireHorse,
                        salary: offeredSalary,
                      })
                    }
                    disabled={!selectedHireHorse || hireMutation.isPending}
                  >
                    {hireMutation.isPending ? "Erbjuder..." : "Erbjud lön"}
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
