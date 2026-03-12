"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatOre } from "@/lib/utils";
import { Card } from "@/components/ui/Card";

const CATEGORY_LABELS: Record<string, string> = {
  race_prize: "Prispeng",
  sponsor_income: "Sponsorintakt",
  sponsor_bonus: "Sponsorbonus",
  stable_costs: "Stallkostnad",
  driver_salary: "Kusklöner",
  commission: "Kuskprovision",
  travel: "Resekostnad",
  shoeing: "Skoning",
  training: "Träning",
  breeding: "Avel",
  market_purchase: "Hästköp",
  market_sale: "Hästförsäljning",
  market_fee: "Försäljningsavgift",
  entry_fee: "Anmälningsavgift",
  signing_fee: "Signeringsavgift",
};

export default function FinancesPage() {
  const { data: overview } = useQuery({ queryKey: ["finances"], queryFn: api.getFinancialOverview });
  const { data: txnData } = useQuery({ queryKey: ["transactions"], queryFn: () => api.getTransactions({ limit: 50 }) });
  const { data: weeklyCosts } = useQuery({ queryKey: ["weekly-costs"], queryFn: api.getWeeklyCosts });

  const txns = txnData?.transactions || [];
  const costs = weeklyCosts || null;

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-200">Ekonomi</h2>

      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <div className="text-xs text-gray-500 mb-1">Saldo</div>
          <div className="text-xl font-bold text-trav-gold">{overview ? formatOre(overview.balance) : "..."}</div>
        </Card>
        <Card>
          <div className="text-xs text-gray-500 mb-1">Intäkter (vecka)</div>
          <div className="text-xl font-bold text-green-400">{overview ? formatOre(overview.weekly_summary?.income?.total || 0) : "..."}</div>
        </Card>
        <Card>
          <div className="text-xs text-gray-500 mb-1">Utgifter (vecka)</div>
          <div className="text-xl font-bold text-red-400">{overview ? formatOre(overview.weekly_summary?.expenses?.total || 0) : "..."}</div>
        </Card>
      </div>

      {/* Weekly cost breakdown */}
      <Card>
        <h3 className="text-sm font-semibold text-gray-300 mb-3">Fasta kostnader per vecka</h3>
        {costs ? (
          <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Stallhyra</span>
              <span className="text-red-400">{formatOre(costs.stall_rent || 0)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Foder</span>
              <span className="text-red-400">{formatOre(costs.feed_cost || 0)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Personal</span>
              <span className="text-red-400">{formatOre(costs.staff_cost || 0)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Kusklöner</span>
              <span className="text-red-400">{formatOre(costs.driver_salaries || 0)}</span>
            </div>
            <div className="flex justify-between col-span-2 border-t border-trav-border pt-2 mt-1">
              <span className="text-gray-300 font-semibold">Totalt per vecka</span>
              <span className="text-red-400 font-bold">{formatOre(costs.total || 0)}</span>
            </div>
            <div className="col-span-2 text-xs text-gray-600">
              {costs.horse_count || 0} hästar i stallet
            </div>
          </div>
        ) : (
          <p className="text-xs text-gray-500">Laddar...</p>
        )}
      </Card>

      {/* Transaction list */}
      <Card>
        <h3 className="text-sm font-semibold text-gray-300 mb-3">Transaktioner</h3>
        <div className="space-y-1">
          {txns.map((t: any) => (
            <div key={t.id} className="flex items-center justify-between py-2 border-b border-trav-border/50 last:border-0">
              <div>
                <div className="text-sm text-gray-300">{t.description}</div>
                <div className="text-xs text-gray-500">
                  <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] mr-1 ${
                    t.amount >= 0 ? "bg-green-900/20 text-green-400" : "bg-red-900/20 text-red-400"
                  }`}>
                    {CATEGORY_LABELS[t.category] || t.category}
                  </span>
                  Vecka {t.game_week}
                </div>
              </div>
              <div className={`text-sm font-semibold tabular-nums ${t.amount >= 0 ? "text-green-400" : "text-red-400"}`}>
                {t.amount >= 0 ? "+" : ""}{formatOre(t.amount)}
              </div>
            </div>
          ))}
          {txns.length === 0 && <p className="text-gray-600 text-sm">Inga transaktioner än</p>}
        </div>
      </Card>
    </div>
  );
}
