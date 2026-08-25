"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatOre } from "@/lib/utils";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

const TYPE_LABELS: Record<string, string> = {
  color: "Stallfärg",
  sulky: "Sulky",
  banner: "Banderoll",
};

export default function PremiumPage() {
  const qc = useQueryClient();
  const { data: status } = useQuery({ queryKey: ["premium"], queryFn: api.getPremiumStatus });
  const { data: pass } = useQuery({ queryKey: ["season-pass"], queryFn: api.getSeasonPass });

  const refresh = () => {
    qc.invalidateQueries({ queryKey: ["premium"] });
    qc.invalidateQueries({ queryKey: ["season-pass"] });
    qc.invalidateQueries({ queryKey: ["box-info"] });
  };

  const equip = useMutation({ mutationFn: (k: string) => api.equipCosmetic(k), onSuccess: refresh });
  const grantPremium = useMutation({ mutationFn: api.devGrantPremium, onSuccess: refresh });
  const grantCosmetic = useMutation({ mutationFn: (k: string) => api.devGrantCosmetic(k), onSuccess: refresh });
  const grantPass = useMutation({ mutationFn: api.devGrantSeasonPass, onSuccess: refresh });

  if (!status) return <p className="text-gray-500 text-sm">Laddar…</p>;

  const byType = (t: string) => (status.cosmetics || []).filter((c: any) => c.type === t);

  return (
    <div className="space-y-5">
      <div className="flex items-baseline justify-between">
        <h2 className="text-xl font-bold text-gray-200 tracking-tight">Premium & kosmetik</h2>
        {status.is_premium && <Badge color="#D4A853">Premium aktivt</Badge>}
      </div>

      <div className="rounded-xl border border-orange-500/25 bg-orange-500/5 px-4 py-3">
        <p className="text-xs text-orange-300">
          Ingen betaltjänst är inkopplad ännu. Knapparna nedan aktiverar rättigheterna
          direkt för test — köpflödet måste kopplas till en riktig betalleverantör
          innan lansering.
        </p>
      </div>

      {/* Premium */}
      <Card>
        <div className="flex items-start justify-between gap-4 mb-3">
          <div>
            <h3 className="text-sm font-semibold text-gray-200">
              TravManager Premium — {status.price_sek} kr/mån
            </h3>
            <p className="text-[11px] text-gray-500 mt-0.5">
              Aldrig fart eller stats för pengar. Bara utrymme, historik och analys.
            </p>
          </div>
          <div className="text-right shrink-0">
            <div className="text-lg font-bold text-trav-gold tabular-nums">
              {status.boxes.effective} boxar
            </div>
            {status.boxes.premium_bonus > 0 && (
              <div className="text-[10px] text-green-400">
                +{status.boxes.premium_bonus} från premium
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-1.5 mb-4">
          {status.features.map((f: any) => (
            <div key={f.key} className="flex items-baseline gap-2 text-xs">
              <span className="text-trav-gold">✓</span>
              <span className="text-gray-200">{f.title}</span>
              <span className="text-gray-600">{f.detail}</span>
            </div>
          ))}
        </div>

        {status.is_premium ? (
          <p className="text-[11px] text-gray-500">
            Aktivt i {status.weeks_remaining} veckor till (t.o.m. vecka {status.premium_until_week}).
          </p>
        ) : (
          <Button onClick={() => grantPremium.mutate()} disabled={grantPremium.isPending}>
            Aktivera premium (test)
          </Button>
        )}
      </Card>

      {/* Kosmetik */}
      {["color", "sulky", "banner"].map((type) => (
        <Card key={type}>
          <div className="section-label mb-3">{TYPE_LABELS[type]}</div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {byType(type).map((c: any) => {
              const equipped =
                (type === "color" && status.equipped.color === c.value) ||
                (type === "sulky" && status.equipped.sulky === c.value) ||
                (type === "banner" && status.equipped.banner === c.value);
              return (
                <div
                  key={c.key}
                  className={`rounded-lg border p-2.5 ${
                    equipped
                      ? "border-trav-gold/50 bg-trav-gold/8"
                      : "border-trav-border bg-trav-hover/30"
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    {type === "color" && (
                      <span
                        className="w-4 h-4 rounded border border-black/40 shrink-0"
                        style={{ backgroundColor: c.value }}
                      />
                    )}
                    <span className="text-xs font-semibold text-gray-200 truncate">{c.name}</span>
                  </div>
                  <p className="text-[10px] text-gray-500 mb-2">{c.detail}</p>
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[10px] text-gray-500">
                      {c.price_sek ? `${c.price_sek} kr` : "Ingår"}
                    </span>
                    {equipped ? (
                      <span className="text-[10px] font-semibold text-trav-gold">Vald</span>
                    ) : c.unlocked ? (
                      <button
                        onClick={() => equip.mutate(c.key)}
                        className="text-[10px] font-semibold text-gray-300 hover:text-trav-gold"
                      >
                        Använd
                      </button>
                    ) : (
                      <button
                        onClick={() => grantCosmetic.mutate(c.key)}
                        className="text-[10px] font-semibold text-gray-500 hover:text-gray-200"
                      >
                        Lås upp (test)
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
          {type === "color" && (
            <p className="text-[10px] text-gray-600 mt-2">
              Stallfärgen syns på dina hästar i loppuppspelningen.
            </p>
          )}
        </Card>
      ))}

      {/* Säsongspass */}
      {pass && (
        <Card>
          <div className="flex items-start justify-between gap-4 mb-3">
            <div>
              <h3 className="text-sm font-semibold text-gray-200">
                Säsongspass {pass.season_number} — {pass.price_sek} kr
              </h3>
              <p className="text-[11px] text-gray-500 mt-0.5">{pass.how_to_earn}</p>
            </div>
            <div className="text-right shrink-0">
              <div className="text-lg font-bold text-trav-gold tabular-nums">
                {pass.points}
              </div>
              <div className="text-[10px] text-gray-500">av {pass.max_points} p</div>
            </div>
          </div>

          <div className="h-1.5 bg-trav-border rounded-full mb-4 overflow-hidden">
            <div
              className="h-full bg-trav-gold/70 rounded-full"
              style={{ width: `${Math.min(100, (pass.points / pass.max_points) * 100)}%` }}
            />
          </div>

          <div className="space-y-1.5">
            {pass.tiers.map((t: any) => (
              <div
                key={t.points}
                className={`grid grid-cols-[52px_1fr_1fr] gap-2 items-center text-[11px] py-1.5 border-b border-trav-border/40 last:border-0 ${
                  t.reached ? "" : "opacity-55"
                }`}
              >
                <span className="tabular-nums text-gray-500">
                  {t.reached ? "✓ " : ""}{t.points} p
                </span>
                <span className="text-gray-300">
                  {t.free ? t.free.label : <span className="text-gray-700">—</span>}
                </span>
                <span className={t.premium_locked ? "text-gray-600" : "text-trav-gold"}>
                  {t.premium ? t.premium.label : <span className="text-gray-700">—</span>}
                  {t.premium && t.premium_locked && " (låst)"}
                </span>
              </div>
            ))}
          </div>
          <div className="grid grid-cols-[52px_1fr_1fr] gap-2 text-[10px] text-gray-600 mt-2">
            <span />
            <span>Gratisspår</span>
            <span>Passpår</span>
          </div>

          {!pass.has_pass && (
            <Button
              size="sm"
              className="mt-3"
              onClick={() => grantPass.mutate()}
              disabled={grantPass.isPending}
            >
              Aktivera säsongspass (test)
            </Button>
          )}
        </Card>
      )}
    </div>
  );
}
