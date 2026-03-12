"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { formatOre } from "@/lib/utils";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { StatBar } from "@/components/ui/StatBar";

export default function MarketPage() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const { data, isLoading } = useQuery({
    queryKey: ["market-listings"],
    queryFn: api.getMarketListings,
  });
  const { data: horsesData } = useQuery({
    queryKey: ["horses"],
    queryFn: api.getHorses,
  });

  const [showSellModal, setShowSellModal] = useState(false);
  const [sellHorseId, setSellHorseId] = useState("");
  const [sellStartPrice, setSellStartPrice] = useState(1000000);
  const [sellBuyoutPrice, setSellBuyoutPrice] = useState(2000000);
  const [bidListingId, setBidListingId] = useState<string | null>(null);
  const [bidAmount, setBidAmount] = useState(0);

  const listMutation = useMutation({
    mutationFn: () => api.listHorseForSale(sellHorseId, sellStartPrice, sellBuyoutPrice),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["market-listings"] });
      setShowSellModal(false);
    },
  });

  const bidMutation = useMutation({
    mutationFn: () => api.placeBid(bidListingId!, bidAmount),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["market-listings"] });
      setBidListingId(null);
    },
  });

  const buyoutMutation = useMutation({
    mutationFn: (listingId: string) => api.buyoutHorse(listingId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["market-listings"] });
      queryClient.invalidateQueries({ queryKey: ["horses"] });
      queryClient.invalidateQueries({ queryKey: ["stable"] });
    },
  });

  const cancelMutation = useMutation({
    mutationFn: (listingId: string) => api.cancelListing(listingId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["market-listings"] });
    },
  });

  const acceptBidMutation = useMutation({
    mutationFn: (listingId: string) => api.acceptBid(listingId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["market-listings"] });
      queryClient.invalidateQueries({ queryKey: ["horses"] });
      queryClient.invalidateQueries({ queryKey: ["stable"] });
    },
  });

  const giveAwayMutation = useMutation({
    mutationFn: (horseId: string) => api.giveAwayHorse(horseId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["horses"] });
      queryClient.invalidateQueries({ queryKey: ["stable"] });
    },
  });

  const listings = data?.listings || [];
  const myHorses = horsesData?.horses || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-200">Hästmarknad</h2>
          <p className="text-sm text-gray-500">Köp och sälj hästar. 10% avgift vid försäljning.</p>
        </div>
        <Button onClick={() => setShowSellModal(true)}>Sälj en häst</Button>
      </div>

      {/* Sell modal */}
      {showSellModal && (
        <Card>
          <h3 className="text-sm font-semibold text-gray-300 mb-3">Lägg ut häst till försäljning</h3>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="text-xs text-gray-500 block mb-1">Välj häst</label>
              <select
                value={sellHorseId}
                onChange={(e) => setSellHorseId(e.target.value)}
                className="w-full px-3 py-2 bg-trav-bg border border-trav-border rounded-lg text-gray-200 text-sm"
              >
                <option value="">Välj...</option>
                {myHorses.map((h: any) => (
                  <option key={h.id} value={h.id}>
                    {h.name} (Spd {h.speed}, End {h.endurance})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">Utropspris (öre)</label>
              <input
                type="number"
                value={sellStartPrice}
                onChange={(e) => setSellStartPrice(Number(e.target.value))}
                min={100000}
                step={100000}
                className="w-full px-3 py-2 bg-trav-bg border border-trav-border rounded-lg text-gray-200 text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">Köp direkt-pris (öre)</label>
              <input
                type="number"
                value={sellBuyoutPrice}
                onChange={(e) => setSellBuyoutPrice(Number(e.target.value))}
                min={sellStartPrice}
                step={100000}
                className="w-full px-3 py-2 bg-trav-bg border border-trav-border rounded-lg text-gray-200 text-sm"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => listMutation.mutate()} disabled={!sellHorseId || listMutation.isPending}>
              {listMutation.isPending ? "Lägger ut..." : "Lägg ut"}
            </Button>
            <Button variant="ghost" onClick={() => setShowSellModal(false)}>Avbryt</Button>
          </div>
          {listMutation.isError && (
            <p className="text-xs text-red-400 mt-2">{(listMutation.error as Error).message}</p>
          )}

          {/* Give away option */}
          <div className="mt-4 pt-4 border-t border-trav-border">
            <p className="text-xs text-gray-500 mb-2">Eller ge bort hästen gratis för att frigöra en box:</p>
            <Button
              variant="danger"
              size="sm"
              onClick={() => {
                if (sellHorseId && confirm("Är du säker? Hästen försvinner permanent från ditt stall."))
                  giveAwayMutation.mutate(sellHorseId);
              }}
              disabled={!sellHorseId || giveAwayMutation.isPending}
            >
              {giveAwayMutation.isPending ? "Ger bort..." : "Ge bort häst"}
            </Button>
            {giveAwayMutation.isSuccess && (
              <p className="text-xs text-green-400 mt-2">Hästen har getts bort!</p>
            )}
            {giveAwayMutation.isError && (
              <p className="text-xs text-red-400 mt-2">{(giveAwayMutation.error as Error).message}</p>
            )}
          </div>
        </Card>
      )}

      {/* Bid modal */}
      {bidListingId && (
        <Card>
          <h3 className="text-sm font-semibold text-gray-300 mb-3">Lägg bud</h3>
          <div className="mb-3">
            <label className="text-xs text-gray-500 block mb-1">Ditt bud (öre)</label>
            <input
              type="number"
              value={bidAmount}
              onChange={(e) => setBidAmount(Number(e.target.value))}
              min={100000}
              step={50000}
              className="w-full px-3 py-2 bg-trav-bg border border-trav-border rounded-lg text-gray-200 text-sm"
            />
          </div>
          <div className="flex gap-2">
            <Button onClick={() => bidMutation.mutate()} disabled={bidMutation.isPending}>
              {bidMutation.isPending ? "Budar..." : "Lägg bud"}
            </Button>
            <Button variant="ghost" onClick={() => setBidListingId(null)}>Avbryt</Button>
          </div>
          {bidMutation.isError && (
            <p className="text-xs text-red-400 mt-2">{(bidMutation.error as Error).message}</p>
          )}
        </Card>
      )}

      {/* Listings */}
      {isLoading ? (
        <div className="text-gray-500">Laddar marknad...</div>
      ) : listings.length === 0 ? (
        <Card>
          <p className="text-gray-500 text-sm text-center py-8">
            Inga hästar till salu just nu. Kom tillbaka senare!
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {listings.map((l: any) => {
            const h = l.horse;
            const avgStat = Math.round(
              (h.speed + h.endurance + h.mentality + h.start_ability + h.sprint_strength + h.balance + h.strength) / 7
            );
            return (
              <Card key={l.id} className="hover:border-trav-gold/30 transition-colors">
                <div className="flex gap-6">
                  {/* Horse info */}
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h3
                        className="text-base font-bold text-trav-gold cursor-pointer hover:underline"
                        onClick={() => router.push(`/horse/${h.id}`)}
                      >
                        {h.name}
                      </h3>
                      <Badge color="#6B7280">{h.gender === "stallion" ? "Hingst" : h.gender === "mare" ? "Sto" : "Valack"}</Badge>
                      {h.total_wins > 0 && <Badge color="#22c55e">{h.total_wins} segrar</Badge>}
                    </div>
                    <p className="text-xs text-gray-500 mb-3">
                      Stall: {l.seller_name} | {h.total_starts} starter | Bästa km-tid: {h.best_km_time || "-"}
                    </p>

                    {/* Stats mini grid */}
                    <div className="grid grid-cols-4 gap-x-4 gap-y-1 text-xs">
                      <div className="flex justify-between"><span className="text-gray-500">Spd</span><span className="text-gray-300">{h.speed}</span></div>
                      <div className="flex justify-between"><span className="text-gray-500">Uth</span><span className="text-gray-300">{h.endurance}</span></div>
                      <div className="flex justify-between"><span className="text-gray-500">Men</span><span className="text-gray-300">{h.mentality}</span></div>
                      <div className="flex justify-between"><span className="text-gray-500">Sta</span><span className="text-gray-300">{h.start_ability}</span></div>
                      <div className="flex justify-between"><span className="text-gray-500">Spr</span><span className="text-gray-300">{h.sprint_strength}</span></div>
                      <div className="flex justify-between"><span className="text-gray-500">Bal</span><span className="text-gray-300">{h.balance}</span></div>
                      <div className="flex justify-between"><span className="text-gray-500">Stk</span><span className="text-gray-300">{h.strength}</span></div>
                      <div className="flex justify-between"><span className="text-gray-500">Snitt</span><span className="text-trav-gold font-semibold">{avgStat}</span></div>
                    </div>

                    <div className="mt-2 text-xs text-gray-500">
                      Form: {h.form} | Distans: {h.distance_optimum}m | Intjänat: {formatOre(h.total_earnings)}
                    </div>

                    {/* Traits (if inspected) */}
                    {h.traits_revealed && h.special_traits?.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {h.special_traits.map((t: string) => (
                          <span key={t} className="text-[10px] px-1.5 py-0.5 rounded bg-purple-900/30 text-purple-300 border border-purple-700/30">
                            {t}
                          </span>
                        ))}
                      </div>
                    )}
                    {h.traits_revealed && h.personality_primary && (
                      <div className="mt-1 text-[10px] text-gray-500">
                        Personlighet: {h.personality_primary}{h.personality_secondary ? ` / ${h.personality_secondary}` : ""}
                      </div>
                    )}
                  </div>

                  {/* Pricing + actions */}
                  <div className="w-48 flex flex-col justify-between text-right">
                    <div>
                      {/* Countdown badge */}
                      <div className="mb-2">
                        <span className={`text-[10px] px-2 py-0.5 rounded font-medium ${
                          l.days_remaining <= 2
                            ? "bg-red-900/30 text-red-300 border border-red-700/30"
                            : l.days_remaining <= 4
                            ? "bg-yellow-900/30 text-yellow-300 border border-yellow-700/30"
                            : "bg-blue-900/30 text-blue-300 border border-blue-700/30"
                        }`}>
                          {l.days_remaining === 1 ? "Sista dagen" : `${l.days_remaining} dagar kvar`}
                        </span>
                      </div>
                      <div className="text-xs text-gray-500">Utropspris</div>
                      <div className="text-sm text-gray-300">{formatOre(l.starting_price)}</div>
                      {l.buyout_price && (
                        <>
                          <div className="text-xs text-gray-500 mt-1">Köp direkt</div>
                          <div className="text-sm font-bold text-trav-gold">{formatOre(l.buyout_price)}</div>
                        </>
                      )}
                      {l.current_bid > 0 && (
                        <>
                          <div className="text-xs text-gray-500 mt-1">Högsta bud</div>
                          <div className="text-sm text-green-400">{formatOre(l.current_bid)}</div>
                        </>
                      )}
                      <div className="text-xs text-gray-600 mt-1">{l.total_bids} bud</div>
                    </div>

                    <div className="flex flex-col gap-1 mt-3">
                      {l.is_own ? (
                        <>
                          {l.current_bid > 0 && (
                            <Button
                              size="sm"
                              onClick={() => {
                                if (confirm(`Acceptera bud på ${formatOre(l.current_bid)}?`))
                                  acceptBidMutation.mutate(l.id);
                              }}
                              disabled={acceptBidMutation.isPending}
                            >
                              {acceptBidMutation.isPending ? "Accepterar..." : `Acceptera bud (${formatOre(l.current_bid)})`}
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="danger"
                            onClick={() => cancelMutation.mutate(l.id)}
                            disabled={l.current_bid > 0 || cancelMutation.isPending}
                          >
                            Avbryt
                          </Button>
                        </>
                      ) : (
                        <>
                          <Button
                            size="sm"
                            onClick={() => {
                              setBidListingId(l.id);
                              setBidAmount(Math.max(l.starting_price, l.current_bid + 50000));
                            }}
                          >
                            Bjud
                          </Button>
                          {l.buyout_price && (
                            <Button
                              size="sm"
                              variant="secondary"
                              onClick={() => buyoutMutation.mutate(l.id)}
                              disabled={buyoutMutation.isPending}
                            >
                              Köp direkt
                            </Button>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
