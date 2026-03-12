"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatOre } from "@/lib/utils";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

export default function SponsorsPage() {
  const queryClient = useQueryClient();
  const [collectResult, setCollectResult] = useState<any>(null);
  const { data, isLoading } = useQuery({
    queryKey: ["sponsors"],
    queryFn: api.getSponsors,
  });
  const { data: contractsData } = useQuery({
    queryKey: ["sponsor-contracts"],
    queryFn: api.getSponsorContracts,
  });
  const { data: stable } = useQuery({
    queryKey: ["stable"],
    queryFn: api.getStable,
  });
  const { data: gameState } = useQuery({
    queryKey: ["gameState"],
    queryFn: api.getGameState,
  });

  const signMutation = useMutation({
    mutationFn: (sponsorId: string) => api.signSponsor(sponsorId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sponsors"] });
      queryClient.invalidateQueries({ queryKey: ["sponsor-contracts"] });
      queryClient.invalidateQueries({ queryKey: ["stable"] });
    },
  });

  const terminateMutation = useMutation({
    mutationFn: (contractId: string) => api.terminateSponsorContract(contractId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sponsors"] });
      queryClient.invalidateQueries({ queryKey: ["sponsor-contracts"] });
    },
  });

  const collectMutation = useMutation({
    mutationFn: () => api.collectSponsorIncome(),
    onSuccess: (data) => {
      setCollectResult(data);
      queryClient.invalidateQueries({ queryKey: ["stable"] });
      queryClient.invalidateQueries({ queryKey: ["sponsor-contracts"] });
    },
  });

  const sponsors = data?.sponsors || [];
  const contracts = contractsData?.contracts || [];
  const reputation = stable?.reputation || 0;
  const isSaturday = gameState?.current_game_day === 6;
  const currentWeek = gameState?.current_game_week || 0;
  const alreadyCollected = (stable?.last_sponsor_collection_week || 0) >= currentWeek;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-200">Sponsorer</h2>
        <p className="text-sm text-gray-500">
          Teckna sponsoravtal för veckovis inkomst. Ditt rykte: <span className="text-trav-gold font-semibold">{reputation}</span>
        </p>
      </div>

      {/* Collect sponsor income — Saturday only */}
      {contracts.length > 0 && (
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-gray-300">💰 Hämta sponsorpengar</h3>
              <p className="text-xs text-gray-500 mt-1">
                {isSaturday
                  ? alreadyCollected
                    ? "Du har redan hämtat sponsorpengar denna vecka"
                    : `${formatOre(contracts.reduce((sum: number, c: any) => sum + c.weekly_payment, 0))} att hämta`
                  : "Sponsorpengar kan bara hämtas på lördagar"}
              </p>
            </div>
            <Button
              onClick={() => collectMutation.mutate()}
              disabled={!isSaturday || alreadyCollected || collectMutation.isPending}
            >
              {collectMutation.isPending ? "Hämtar..." : alreadyCollected ? "✅ Hämtat" : "Hämta pengar"}
            </Button>
          </div>
          {collectResult && (
            <div className="mt-3 pt-3 border-t border-trav-border">
              <div className="text-sm text-green-400">
                ✅ Sponsorpengar hämtade: {formatOre(collectResult.total_income)} från {collectResult.contracts_paid} avtal
              </div>
            </div>
          )}
          {collectMutation.isError && (
            <div className="mt-3 pt-3 border-t border-trav-border">
              <div className="text-sm text-red-400">
                ❌ {(collectMutation.error as Error)?.message || "Kunde inte hämta sponsorpengar"}
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Active contracts */}
      {contracts.length > 0 && (
        <Card>
          <h3 className="text-sm font-semibold text-gray-300 mb-3">Aktiva sponsoravtal ({contracts.length}/3)</h3>
          <div className="space-y-3">
            {contracts.map((c: any) => (
              <div key={c.id} className="flex items-center justify-between py-2 border-b border-trav-border last:border-0">
                <div>
                  <span className="text-gray-200 font-medium">{c.sponsor_name}</span>
                  <div className="text-xs text-gray-500">
                    {formatOre(c.weekly_payment)}/vecka | Vinstbonus: {formatOre(c.win_bonus)} | {c.weeks_remaining}v kvar
                  </div>
                </div>
                <Button
                  size="sm"
                  variant="danger"
                  onClick={() => terminateMutation.mutate(c.id)}
                  disabled={terminateMutation.isPending}
                >
                  Avsluta
                </Button>
              </div>
            ))}
          </div>
          <div className="mt-3 pt-3 border-t border-trav-border">
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Total veckovis inkomst</span>
              <span className="text-trav-gold font-bold">
                {formatOre(contracts.reduce((sum: number, c: any) => sum + c.weekly_payment, 0))}/vecka
              </span>
            </div>
          </div>
        </Card>
      )}

      {/* Available sponsors */}
      <Card>
        <h3 className="text-sm font-semibold text-gray-300 mb-3">Tillgängliga sponsorer</h3>
        {isLoading ? (
          <div className="text-gray-500 text-sm">Laddar...</div>
        ) : (
          <div className="space-y-2">
            {sponsors.map((s: any) => (
              <div
                key={s.id}
                className={`flex items-center justify-between py-3 px-3 rounded-lg border ${
                  s.eligible && !s.has_contract
                    ? "border-trav-border hover:border-trav-gold/30"
                    : "border-trav-border/30 opacity-60"
                } transition-colors`}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-gray-200 font-medium">{s.name}</span>
                    {s.has_contract && <Badge color="#22c55e">Aktivt</Badge>}
                    {!s.eligible && <Badge color="#ef4444">Kräver {s.min_reputation} rykte</Badge>}
                  </div>
                  <div className="text-xs text-gray-500 mt-0.5">
                    {formatOre(s.weekly_payment)}/vecka | Vinstbonus: {formatOre(s.win_bonus)} | Min rykte: {s.min_reputation}
                  </div>
                </div>
                {s.eligible && !s.has_contract && contracts.length < 3 && (
                  <Button
                    size="sm"
                    onClick={() => signMutation.mutate(s.id)}
                    disabled={signMutation.isPending}
                  >
                    Teckna
                  </Button>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Info */}
      <Card>
        <h3 className="text-sm font-semibold text-gray-300 mb-2">Hur sponsorer fungerar</h3>
        <ul className="text-xs text-gray-500 space-y-1 list-disc list-inside">
          <li>Max 3 aktiva sponsoravtal samtidigt</li>
          <li>Sponsorpengar hämtas manuellt varje lördag</li>
          <li>Högre rykte ger tillgång till bättre sponsorer</li>
          <li>Avtal varar i 8 veckor och kan avslutas i förtid</li>
          <li>Vinstbonus betalas ut när dina hästar vinner lopp</li>
        </ul>
      </Card>
    </div>
  );
}
