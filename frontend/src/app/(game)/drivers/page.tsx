"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatOre } from "@/lib/utils";
import { Card } from "@/components/ui/Card";
import { StatBar } from "@/components/ui/StatBar";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

export default function DriversPage() {
  const queryClient = useQueryClient();
  const { data: drivers, isLoading } = useQuery({ queryKey: ["drivers"], queryFn: api.getDrivers });
  const [tab, setTab] = useState<"contracted" | "market">("contracted");
  const [contractModal, setContractModal] = useState<any>(null);
  const [contractType, setContractType] = useState("permanent");
  const [contractWeeks, setContractWeeks] = useState(16);

  const terminateMutation = useMutation({
    mutationFn: (driverId: string) => api.terminateContract(driverId),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["drivers"] }); },
  });

  const hireMutation = useMutation({
    mutationFn: (data: { driverId: string; contract_type: string; weeks: number }) =>
      api.renewContract(data.driverId, data.contract_type, data.weeks),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["drivers"] });
      setContractModal(null);
    },
  });

  if (isLoading) return <div className="text-gray-500">Laddar...</div>;

  const driverList = Array.isArray(drivers) ? drivers : drivers?.contracted || [];
  const marketList = drivers?.market || [];

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-200">Kuskar</h2>

      {/* Tabs */}
      <div className="flex gap-2">
        <Button
          variant={tab === "contracted" ? "primary" : "secondary"}
          size="sm"
          onClick={() => setTab("contracted")}
        >
          Kontrakterade ({driverList.length})
        </Button>
        <Button
          variant={tab === "market" ? "primary" : "secondary"}
          size="sm"
          onClick={() => setTab("market")}
        >
          Kuskmarknad ({marketList.length})
        </Button>
      </div>

      {/* Contracted Drivers */}
      {tab === "contracted" && (
        <div className="space-y-3">
          {driverList.length === 0 && <div className="text-gray-500">Inga kontrakterade kuskar</div>}
          {driverList.map((d: any) => (
            <Card key={d.id}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-semibold text-gray-200">{d.name}</div>
                  <div className="text-xs text-gray-500">{d.driving_style} | {d.contract_type}</div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <div className="text-sm text-trav-gold">{formatOre(d.salary_per_week || 0)}/vecka</div>
                    <div className="text-xs text-orange-400">Provision: {d.commission_rate ? Math.round(d.commission_rate * 100) : 10}%</div>
                  </div>
                  <Button variant="danger" size="sm" onClick={() => { if (confirm("Säga upp kontrakt?")) terminateMutation.mutate(d.id); }}>
                    Säga upp
                  </Button>
                </div>
              </div>
              <div className="grid grid-cols-4 gap-3 mt-3">
                <StatBar value={d.skill} label="Skicklighet" />
                <StatBar value={d.tactical_ability} label="Taktik" />
                <StatBar value={d.sprint_timing} label="Spurt-timing" />
                <StatBar value={d.gallop_handling} label="Galopphantering" />
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Driver Market */}
      {tab === "market" && (
        <div className="space-y-3">
          {marketList.length === 0 && <div className="text-gray-500">Inga kuskar tillgängliga</div>}
          {marketList.map((d: any) => (
            <Card key={d.id}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-semibold text-gray-200">
                    {d.name}
                    {d.is_real_driver && <Badge color="#D4A853" className="ml-2">Proffskusk</Badge>}
                  </div>
                  <div className="text-xs text-gray-500">{d.driving_style} | Popularitet: {d.popularity}</div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right text-xs text-gray-400">
                    <div>{formatOre(d.base_salary)}/vecka</div>
                    <div className="text-gray-600">Gästkörning: {formatOre(d.guest_fee)}/lopp</div>
                    <div className="text-orange-400">Provision: {d.commission_rate ? Math.round(d.commission_rate * 100) : 10}%</div>
                  </div>
                  <Button size="sm" onClick={() => setContractModal(d)}>
                    Teckna kontrakt
                  </Button>
                </div>
              </div>
              <div className="grid grid-cols-4 gap-3 mt-3">
                <StatBar value={d.skill} label="Skicklighet" />
                <StatBar value={d.tactical_ability} label="Taktik" />
                <StatBar value={d.sprint_timing} label="Spurt-timing" />
                <StatBar value={d.gallop_handling} label="Galopphantering" />
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Contract Modal */}
      {contractModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setContractModal(null)}>
          <div className="bg-trav-card border border-trav-border rounded-xl p-6 w-full max-w-sm" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-gray-200 mb-4">Teckna kontrakt</h3>
            <div className="text-sm text-gray-400 mb-4">{contractModal.name}</div>

            <div className="space-y-3">
              <div>
                <label className="text-xs text-gray-500 block mb-1">Kontraktstyp</label>
                <select
                  value={contractType}
                  onChange={(e) => setContractType(e.target.value)}
                  className="w-full px-3 py-2 bg-trav-bg border border-trav-border rounded-lg text-gray-200"
                >
                  <option value="permanent">Permanent</option>
                  <option value="guest">Gäst</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">Längd (veckor)</label>
                <select
                  value={contractWeeks}
                  onChange={(e) => setContractWeeks(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-trav-bg border border-trav-border rounded-lg text-gray-200"
                >
                  <option value={8}>8 veckor</option>
                  <option value={16}>16 veckor</option>
                  <option value={32}>32 veckor (hel säsong)</option>
                </select>
              </div>
              <div className="text-sm text-gray-400 mt-2">
                <div>Lön: {formatOre(contractType === "guest" ? contractModal.guest_fee : contractModal.base_salary)}/{contractType === "guest" ? "lopp" : "vecka"}</div>
                <div>Signeringsavgift: {formatOre((contractType === "guest" ? contractModal.guest_fee : contractModal.base_salary) * 2)}</div>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-5">
              <Button variant="secondary" onClick={() => setContractModal(null)}>Avbryt</Button>
              <Button
                onClick={() => hireMutation.mutate({ driverId: contractModal.id, contract_type: contractType, weeks: contractWeeks })}
                disabled={hireMutation.isPending}
              >
                {hireMutation.isPending ? "Signerar..." : "Signera"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
