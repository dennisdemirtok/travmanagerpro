"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatOre } from "@/lib/utils";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

const CATEGORY_LABELS: Record<string, string> = {
  prize_money: "Prispeng",
  race_prize: "Prispeng",
  start_fee: "Startpeng",
  breeder_premium: "Uppfödarpremie",
  sponsor_income: "Sponsorintäkt",
  sponsor_bonus: "Sponsorbonus",
  weekly_costs: "Veckokostnader",
  stable_costs: "Stallkostnad",
  driver_salary: "Kusklön",
  driver_commission: "Kuskprovision",
  freelance_driver: "Frilanskusk",
  commission: "Kuskprovision",
  travel: "Resekostnad",
  shoeing: "Skoning",
  training: "Träning",
  breeding: "Avel",
  market_purchase: "Hästköp",
  horse_purchase: "Hästköp",
  market_sale: "Hästförsäljning",
  horse_sale: "Hästförsäljning",
  market_fee: "Försäljningsavgift",
  entry_fee: "Anmälningsavgift",
  entry_fee_refund: "Återbetalning",
  signing_fee: "Signeringsavgift",
  loan: "Lån",
  loan_repayment: "Amortering",
  loan_interest: "Låneränta",
  debt_interest: "Övertrasseringsränta",
  forced_sale: "Tvångsförsäljning",
  bankruptcy_protection: "Konkursskydd",
  restart: "Nystart",
};

const DEBT_STYLES: Record<string, { color: string; bg: string; icon: string }> = {
  ok: { color: "#4ADE80", bg: "bg-green-500/5 border-green-500/20", icon: "✓" },
  loan: { color: "#D4A853", bg: "bg-trav-gold/5 border-trav-gold/20", icon: "◆" },
  warning: { color: "#FB923C", bg: "bg-orange-500/5 border-orange-500/25", icon: "!" },
  severe: { color: "#F87171", bg: "bg-red-500/8 border-red-500/30", icon: "!!" },
  critical: { color: "#F87171", bg: "bg-red-500/12 border-red-500/40", icon: "✕" },
};

function kr(ore: number) {
  return formatOre(ore);
}

export default function FinancesPage() {
  const qc = useQueryClient();
  const [loanAmount, setLoanAmount] = useState(2_500_000); // 25 000 kr
  const [error, setError] = useState<string | null>(null);

  const { data: overview } = useQuery({ queryKey: ["finances"], queryFn: api.getFinancialOverview });
  const { data: txnData } = useQuery({ queryKey: ["transactions"], queryFn: () => api.getTransactions({ limit: 50 }) });
  const { data: weeklyCosts } = useQuery({ queryKey: ["weekly-costs"], queryFn: api.getWeeklyCosts });

  const debt = overview?.debt;
  const txns = txnData?.transactions || [];
  const costs = weeklyCosts || null;

  const refresh = () => {
    qc.invalidateQueries({ queryKey: ["finances"] });
    qc.invalidateQueries({ queryKey: ["transactions"] });
    qc.invalidateQueries({ queryKey: ["weekly-costs"] });
    qc.invalidateQueries({ queryKey: ["stable"] });
  };

  const loanMut = useMutation({
    mutationFn: (amount: number) => api.takeLoan(amount),
    onSuccess: () => { setError(null); refresh(); },
    onError: (e: any) => setError(e.message),
  });
  const repayMut = useMutation({
    mutationFn: (amount: number) => api.repayLoan(amount),
    onSuccess: () => { setError(null); refresh(); },
    onError: (e: any) => setError(e.message),
  });
  const restartMut = useMutation({
    mutationFn: () => api.restartStable(),
    onSuccess: () => { setError(null); refresh(); },
    onError: (e: any) => setError(e.message),
  });

  const balance = overview?.balance ?? 0;
  const net = overview?.weekly_summary?.net ?? 0;
  const style = DEBT_STYLES[debt?.level || "ok"];

  return (
    <div className="space-y-5">
      <div className="flex items-baseline justify-between">
        <h2 className="text-xl font-bold text-gray-200 tracking-tight">Ekonomi</h2>
        {debt && (
          <Badge color={style.color}>{debt.label}</Badge>
        )}
      </div>

      {/* Skuldbanner */}
      {debt && debt.level !== "ok" && (
        <div className={`rounded-xl border px-4 py-3 ${style.bg}`}>
          <div className="flex items-start gap-3">
            <span className="text-lg leading-none mt-0.5" style={{ color: style.color }}>{style.icon}</span>
            <div className="flex-1 text-sm">
              <div className="font-semibold" style={{ color: style.color }}>{debt.label}</div>
              <div className="text-gray-400 mt-1 space-y-0.5 text-xs">
                {debt.weekly_overdraft_interest > 0 && (
                  <div>Övertrasseringsränta: <span className="text-red-400">{kr(debt.weekly_overdraft_interest)}/vecka</span> (2 %)</div>
                )}
                {debt.loan_principal > 0 && (
                  <div>Lån: {kr(debt.loan_principal)} — ränta <span className="text-red-400">{kr(debt.weekly_loan_interest)}/vecka</span> (3 %)</div>
                )}
                {debt.forced_sale_deadline_week && (
                  <div className="text-orange-300">Sälj en häst före vecka {debt.forced_sale_deadline_week}, annars tvångssäljer banken din sämsta häst för halva värdet.</div>
                )}
                {debt.level === "critical" && (
                  <div className="text-red-300">Saldot kan inte sjunka under {kr(debt.bankruptcy_floor)}. Gör en nystart för att skriva av skulden.</div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Nyckeltal */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Card className="p-3">
          <div className="text-[11px] uppercase tracking-wider text-gray-500 mb-1">Saldo</div>
          <div className={`text-lg font-bold tabular-nums ${balance < 0 ? "text-red-400" : "text-trav-gold"}`}>
            {overview ? kr(balance) : "…"}
          </div>
        </Card>
        <Card className="p-3">
          <div className="text-[11px] uppercase tracking-wider text-gray-500 mb-1">Netto (senaste 100)</div>
          <div className={`text-lg font-bold tabular-nums ${net < 0 ? "text-red-400" : "text-green-400"}`}>
            {overview ? (net >= 0 ? "+" : "") + kr(net) : "…"}
          </div>
        </Card>
        <Card className="p-3">
          <div className="text-[11px] uppercase tracking-wider text-gray-500 mb-1">Intäkter</div>
          <div className="text-lg font-bold text-green-400 tabular-nums">
            {overview ? kr(overview.weekly_summary?.income?.total || 0) : "…"}
          </div>
        </Card>
        <Card className="p-3">
          <div className="text-[11px] uppercase tracking-wider text-gray-500 mb-1">Utgifter</div>
          <div className="text-lg font-bold text-red-400 tabular-nums">
            {overview ? kr(overview.weekly_summary?.expenses?.total || 0) : "…"}
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Veckokostnader */}
        <Card>
          <h3 className="text-sm font-semibold text-gray-300 mb-3">Fasta kostnader per vecka</h3>
          {costs ? (
            <div className="space-y-1.5 text-sm">
              <CostRow label={`Stallhyra (${costs.horse_count || 0} hästar, progressiv)`} value={costs.stall_rent} />
              <CostRow label="Foder" value={costs.feed} />
              <CostRow label="Personal" value={costs.staff} />
              <CostRow label="Kusklöner (kontrakt)" value={costs.driver_salaries} />
              {costs.interest > 0 && <CostRow label="Räntor" value={costs.interest} highlight />}
              <div className="flex justify-between border-t border-trav-border pt-2 mt-2">
                <span className="text-gray-300 font-semibold">Totalt per vecka</span>
                <span className="text-red-400 font-bold tabular-nums">{kr(costs.total || 0)}</span>
              </div>
              <div className="text-[11px] text-gray-600 pt-1">
                Nästa häst kostar <span className="text-gray-400">{kr(costs.next_horse_rent || 0)}</span> extra i hyra.
                Häst 1–3: 1 500 kr · 4–6: 3 000 kr · 7+: 5 000 kr
              </div>
            </div>
          ) : (
            <p className="text-xs text-gray-500">Laddar…</p>
          )}
        </Card>

        {/* Lån */}
        <Card>
          <h3 className="text-sm font-semibold text-gray-300 mb-3">Banken</h3>
          {debt ? (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <div className="text-[11px] text-gray-500">Utestående lån</div>
                  <div className="font-semibold text-gray-200 tabular-nums">{kr(debt.loan_principal)}</div>
                </div>
                <div>
                  <div className="text-[11px] text-gray-500">Låneutrymme kvar</div>
                  <div className="font-semibold text-gray-200 tabular-nums">{kr(debt.loan_headroom)}</div>
                </div>
              </div>

              <div>
                <label className="text-[11px] text-gray-500 block mb-1">
                  Belopp: <span className="text-trav-gold font-semibold tabular-nums">{kr(loanAmount)}</span>
                </label>
                <input
                  type="range"
                  min={500_000}
                  max={Math.max(500_000, debt.max_loan)}
                  step={500_000}
                  value={loanAmount}
                  onChange={(e) => setLoanAmount(Number(e.target.value))}
                  className="w-full accent-trav-gold"
                />
                <div className="flex justify-between text-[10px] text-gray-600">
                  <span>5 000 kr</span>
                  <span>{kr(debt.max_loan)}</span>
                </div>
              </div>

              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={() => loanMut.mutate(loanAmount)}
                  disabled={loanMut.isPending || debt.loan_headroom <= 0}
                >
                  Låna {kr(loanAmount)}
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => repayMut.mutate(Math.min(loanAmount, debt.loan_principal))}
                  disabled={repayMut.isPending || debt.loan_principal <= 0}
                >
                  Amortera
                </Button>
              </div>

              <p className="text-[11px] text-gray-600">
                Ränta 3 % per vecka på utestående lån. Maxlån {kr(debt.max_loan)}.
                Amortering väljer du själv — räntan dras varje vecka.
              </p>

              {debt.can_restart && (
                <div className="border-t border-trav-border pt-3">
                  <p className="text-[11px] text-gray-500 mb-2">
                    Du har nått skuldgolvet. En nystart behåller din bästa häst, skriver av skulden
                    och sänker ryktet med 20.
                  </p>
                  <Button
                    size="sm"
                    variant="danger"
                    onClick={() => restartMut.mutate()}
                    disabled={restartMut.isPending}
                  >
                    Gör nystart
                  </Button>
                </div>
              )}

              {error && <p className="text-xs text-red-400">{error}</p>}
            </div>
          ) : (
            <p className="text-xs text-gray-500">Laddar…</p>
          )}
        </Card>
      </div>

      {/* Transaktioner */}
      <Card>
        <h3 className="text-sm font-semibold text-gray-300 mb-3">Transaktioner</h3>
        <div className="divide-y divide-trav-border/50">
          {txns.map((t: any) => (
            <div key={t.id} className="flex items-center justify-between gap-4 py-2">
              <div className="min-w-0">
                <div className="text-sm text-gray-300 truncate">{t.description}</div>
                <div className="text-[11px] text-gray-500 mt-0.5 flex items-center gap-1.5">
                  <span
                    className={`inline-block px-1.5 py-0.5 rounded text-[10px] ${
                      t.amount >= 0 ? "bg-green-900/20 text-green-400" : "bg-red-900/20 text-red-400"
                    }`}
                  >
                    {CATEGORY_LABELS[t.category] || t.category}
                  </span>
                  <span>V{t.game_week}</span>
                </div>
              </div>
              <div className={`text-sm font-semibold tabular-nums shrink-0 ${t.amount >= 0 ? "text-green-400" : "text-red-400"}`}>
                {t.amount >= 0 ? "+" : ""}{kr(t.amount)}
              </div>
            </div>
          ))}
          {txns.length === 0 && <p className="text-gray-600 text-sm py-2">Inga transaktioner än</p>}
        </div>
      </Card>
    </div>
  );
}

function CostRow({ label, value, highlight }: { label: string; value?: number; highlight?: boolean }) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-500">{label}</span>
      <span className={`tabular-nums ${highlight ? "text-orange-400" : "text-red-400"}`}>
        {formatOre(value || 0)}
      </span>
    </div>
  );
}
