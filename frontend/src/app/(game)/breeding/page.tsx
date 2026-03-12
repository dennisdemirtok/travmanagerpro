"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatOre } from "@/lib/utils";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

export default function BreedingPage() {
  const queryClient = useQueryClient();
  const [selectedStallion, setSelectedStallion] = useState<string | null>(null);
  const [selectedMare, setSelectedMare] = useState<string | null>(null);

  const { data: stallions, isLoading: stallionsLoading } = useQuery({
    queryKey: ["stallions"],
    queryFn: api.getStallions,
  });

  const { data: breedingStatus } = useQuery({
    queryKey: ["breeding-status"],
    queryFn: api.getBreedingStatus,
  });

  const { data: horses } = useQuery({
    queryKey: ["horses"],
    queryFn: api.getHorses,
  });

  const breedMutation = useMutation({
    mutationFn: () => api.breed(selectedMare!, selectedStallion!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["breeding-status"] });
      queryClient.invalidateQueries({ queryKey: ["horses"] });
      queryClient.invalidateQueries({ queryKey: ["stable"] });
      setSelectedMare(null);
      setSelectedStallion(null);
    },
  });

  const mares = (breedingStatus || []).filter((m: any) => !m.is_pregnant);
  const pregnantMares = (breedingStatus || []).filter((m: any) => m.is_pregnant);
  const stallionList = stallions || [];

  const selectedStallionData = stallionList.find((s: any) => s.id === selectedStallion);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-200">Avel</h2>
        <p className="text-sm text-gray-500">
          Avla dina ston med framgångsrika hingstar för att producera nya talanger.
        </p>
      </div>

      {/* Pregnant mares */}
      {pregnantMares.length > 0 && (
        <Card>
          <h3 className="text-sm font-semibold text-gray-300 mb-3">Dräktiga ston</h3>
          <div className="space-y-2">
            {pregnantMares.map((m: any) => (
              <div key={m.id} className="flex items-center justify-between py-2 border-b border-trav-border last:border-0">
                <div>
                  <span className="text-gray-200 font-medium">{m.name}</span>
                  <div className="text-xs text-gray-500">
                    Dräktig sedan vecka {m.pregnancy_week} | Föl väntas vecka {m.expected_foal_week}
                  </div>
                </div>
                <Badge color="#a855f7">Dräktig</Badge>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Breeding form */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Mare selection */}
        <Card>
          <h3 className="text-sm font-semibold text-gray-300 mb-3">Välj sto</h3>
          {mares.length === 0 ? (
            <p className="text-sm text-gray-500">Inga tillgängliga ston (du behöver ett sto som inte är dräktigt eller i träning)</p>
          ) : (
            <div className="space-y-2">
              {mares.map((m: any) => (
                <button
                  key={m.id}
                  onClick={() => setSelectedMare(m.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg border transition-colors ${
                    selectedMare === m.id
                      ? "border-trav-gold bg-trav-active"
                      : "border-trav-border hover:border-trav-gold/30"
                  }`}
                >
                  <span className="text-gray-200 font-medium">{m.name}</span>
                  <span className="text-xs text-gray-500 ml-2">{m.age_years} år</span>
                </button>
              ))}
            </div>
          )}
        </Card>

        {/* Stallion selection */}
        <Card>
          <h3 className="text-sm font-semibold text-gray-300 mb-3">Välj hingst</h3>
          {stallionsLoading ? (
            <div className="text-gray-500 text-sm">Laddar hingstar...</div>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {stallionList.map((s: any) => (
                <button
                  key={s.id}
                  onClick={() => setSelectedStallion(s.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg border transition-colors ${
                    selectedStallion === s.id
                      ? "border-trav-gold bg-trav-active"
                      : "border-trav-border hover:border-trav-gold/30"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-gray-200 font-medium">{s.name}</span>
                    <span className="text-trav-gold text-sm">{formatOre(s.stud_fee)}</span>
                  </div>
                  <div className="text-xs text-gray-500 mt-0.5">
                    {s.origin_country} | Prestige: {s.prestige}
                  </div>
                  <div className="flex gap-2 mt-1 flex-wrap">
                    {Object.entries(s.bonuses || {}).map(([stat, val]: [string, any]) =>
                      val > 0 ? (
                        <span key={stat} className="text-[10px] text-green-400/70 bg-green-900/20 px-1.5 py-0.5 rounded">
                          {stat}: +{val}
                        </span>
                      ) : null
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* Breed button */}
      {selectedMare && selectedStallion && (
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-gray-300">Bekräfta avel</h3>
              <p className="text-xs text-gray-500 mt-1">
                Betäckningsavgift: <span className="text-trav-gold">{formatOre(selectedStallionData?.stud_fee || 0)}</span>
                {" "}| Föl väntas om 4 spelveckor
              </p>
            </div>
            <Button
              onClick={() => breedMutation.mutate()}
              disabled={breedMutation.isPending}
            >
              {breedMutation.isPending ? "Avlar..." : "Starta avel"}
            </Button>
          </div>
          {breedMutation.isError && (
            <p className="text-xs text-red-400 mt-2">{(breedMutation.error as Error).message}</p>
          )}
        </Card>
      )}

      {/* Info */}
      <Card>
        <h3 className="text-sm font-semibold text-gray-300 mb-2">Hur avel fungerar</h3>
        <ul className="text-xs text-gray-500 space-y-1 list-disc list-inside">
          <li>Endast ston kan avlas</li>
          <li>Välj en hingst från katalogen — dyrare hingstar ger bättre chanser</li>
          <li>Dräktigheten varar 4 spelveckor</li>
          <li>Fölet kan inte tävla förrän det är 2 år gammalt</li>
          <li>Fölets stats baseras på både sto och hingst, plus slump</li>
          <li>30% chans att fölet får en speciell egenskap (20% positiv, 80% negativ)</li>
        </ul>
      </Card>
    </div>
  );
}
