"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { formatOre, statColor } from "@/lib/utils";
import { Card } from "@/components/ui/Card";
import { StatBar } from "@/components/ui/StatBar";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

const PERSONALITY_LABELS: Record<string, string> = {
  calm: "Lugn", nervous: "Nervös", aggressive: "Aggressiv",
  lazy: "Lat", energetic: "Energisk", stubborn: "Envis",
  training_eager: "Träningsvillig", winner: "Vinnare",
  strong_willed: "Stark vilja", moody: "Humörsam",
  food_lover: "Matglad",
};

const TRAIT_LABELS: Record<string, string> = {
  sprint_king: "Spurtkung", rain_lover: "Regnälskare",
  iron_hooves: "Järnhovar", early_bloomer: "Tidig mognad",
  late_bloomer: "Sen mognad", nervous_starter: "Nervös startare",
  gallop_prone: "Galoppbenägen", cold_hater: "Köldkänslig",
  crowd_shy: "Publikrädd", temperamental: "Temperamentsfull",
  glass_legs: "Glasben", heavy_sweater: "Svettare",
};

const TRAIT_POSITIVE = new Set(["sprint_king", "rain_lover", "iron_hooves", "early_bloomer"]);

function CompatibilitySection({ horseId, drivers }: { horseId: string; drivers: any[] }) {
  const queryClient = useQueryClient();
  const [checking, setChecking] = useState<string | null>(null);

  const checkMutation = useMutation({
    mutationFn: (driverId: string) => api.checkCompatibility(driverId, horseId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["horse", horseId] });
      setChecking(null);
    },
    onError: () => setChecking(null),
  });

  return (
    <Card>
      <h3 className="text-sm font-semibold text-gray-300 mb-3">Kuskkompatibilitet</h3>
      {drivers.map((c: any) => (
        <div key={c.driver_id} className="flex justify-between items-center py-1.5">
          <span className="text-gray-300 text-sm">{c.driver_name}</span>
          {c.is_checked ? (
            <span className={`text-sm font-semibold ${c.score >= 70 ? "text-green-400" : c.score >= 50 ? "text-yellow-400" : "text-red-400"}`}>
              {c.score} - {c.label}
            </span>
          ) : (
            <Button
              size="sm"
              variant="secondary"
              onClick={() => { setChecking(c.driver_id); checkMutation.mutate(c.driver_id); }}
              disabled={checking === c.driver_id}
            >
              {checking === c.driver_id ? "Kollar..." : `Kolla (${formatOre(c.check_cost || 50000)})`}
            </Button>
          )}
        </div>
      ))}
    </Card>
  );
}

const SHOES: Record<string, string> = {
  barefoot: "Barfota", light_aluminum: "Lättsko", normal_steel: "Normalsko",
  heavy_steel: "Tung stål", studs: "Broddar", grip: "Grepp", balance: "Balans",
};

const SHOE_EFFECTS: Record<string, { speed: string; gallop: string; gripNormal: string; gripWet: string; gripWinter: string; weight: string }> = {
  barefoot:       { speed: "+2%",  gallop: "+15% risk", gripNormal: "Dåligt",  gripWet: "Uselt",   gripWinter: "Uselt",  weight: "0g" },
  light_aluminum: { speed: "+1%",  gallop: "+5% risk",  gripNormal: "Bra",     gripWet: "Sämre",   gripWinter: "Sämre",  weight: "120g" },
  normal_steel:   { speed: "0%",   gallop: "Normal",    gripNormal: "Normal",  gripWet: "Bra",     gripWinter: "OK",     weight: "350g" },
  heavy_steel:    { speed: "-2%",  gallop: "-10% risk", gripNormal: "Mycket bra", gripWet: "Normal", gripWinter: "Bra",  weight: "500g" },
  studs:          { speed: "-1%",  gallop: "-5% risk",  gripNormal: "Normal",  gripWet: "Bra",     gripWinter: "Utmärkt", weight: "400g" },
  grip:           { speed: "-1%",  gallop: "-8% risk",  gripNormal: "Normal",  gripWet: "Utmärkt", gripWinter: "Normal", weight: "380g" },
  balance:        { speed: "0%",   gallop: "-12% risk", gripNormal: "Bra",     gripWet: "OK",      gripWinter: "OK",     weight: "250g" },
};

const PROGRAMS: Record<string, string> = {
  rest: "Vila", interval: "Intervall", long_distance: "Långdistans",
  start_training: "Startträning", sprint_training: "Spurtträning",
  mental_training: "Mentalträning", strength_training: "Styrketräning",
  balance_training: "Balansträning", swim_training: "Simträning", track_training: "Banträning",
};

const INTENSITIES: Record<string, string> = {
  light: "Lätt", normal: "Normal", hard: "Hård", maximum: "Maximal",
};

const PRO_STATS = [
  { value: "speed", label: "Fart" },
  { value: "endurance", label: "Uthållighet" },
  { value: "mentality", label: "Mentalitet" },
  { value: "start_ability", label: "Startförmåga" },
  { value: "sprint_strength", label: "Spurtstyrka" },
  { value: "balance", label: "Balans" },
  { value: "strength", label: "Styrka" },
];

const STAT_LABELS: Record<string, string> = {
  speed: "Fart", endurance: "Uthållighet", mentality: "Mentalitet",
  start_ability: "Startförmåga", sprint_strength: "Spurt",
  balance: "Balans", strength: "Styrka",
};

const PRO_LEVELS = [
  { value: "standard", label: "Standard (3 000 kr/v)", cost: 300000 },
  { value: "advanced", label: "Avancerad (6 000 kr/v)", cost: 600000 },
  { value: "elite", label: "Elite (10 000 kr/v)", cost: 1000000 },
];

export default function HorseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const { data: horse, isLoading } = useQuery({ queryKey: ["horse", id], queryFn: () => api.getHorse(id) });
  const { data: startPoints } = useQuery({ queryKey: ["start-points", id], queryFn: () => api.getHorseStartPoints(id) });
  const { data: trainingStatus } = useQuery({ queryKey: ["training-status"], queryFn: api.getTrainingStatus });
  const { data: gameState } = useQuery({ queryKey: ["gameState"], queryFn: api.getGameState });

  const [selectedShoe, setSelectedShoe] = useState("");
  const [selectedProgram, setSelectedProgram] = useState("");
  const [selectedIntensity, setSelectedIntensity] = useState("normal");
  const [showProModal, setShowProModal] = useState(false);
  const [proStat, setProStat] = useState("speed");
  const [proLevel, setProLevel] = useState("standard");

  const invalidateHorse = () => {
    queryClient.invalidateQueries({ queryKey: ["horse", id] });
    queryClient.invalidateQueries({ queryKey: ["horses"] });
    queryClient.invalidateQueries({ queryKey: ["stable"] });
  };

  const shoeMutation = useMutation({
    mutationFn: () => api.changeShoe(id, selectedShoe),
    onSuccess: invalidateHorse,
  });

  const trainingMutation = useMutation({
    mutationFn: () => api.changeTraining(id, selectedProgram, selectedIntensity),
    onSuccess: invalidateHorse,
  });

  const quickTrainMutation = useMutation({
    mutationFn: () => api.quickTrain(id),
    onSuccess: invalidateHorse,
  });

  const proTrainMutation = useMutation({
    mutationFn: () => api.sendToProfessional(id, proStat, proLevel),
    onSuccess: () => {
      invalidateHorse();
      queryClient.invalidateQueries({ queryKey: ["training-status"] });
      setShowProModal(false);
    },
  });

  if (isLoading) return <div className="text-gray-500">Laddar...</div>;
  if (!horse) return <div className="text-gray-500">Hästen hittades inte</div>;

  const stats = [
    { label: "Fart", value: horse.speed },
    { label: "Uthållighet", value: horse.endurance },
    { label: "Mentalitet", value: horse.mentality },
    { label: "Startförmåga", value: horse.start_ability },
    { label: "Spurtstyrka", value: horse.sprint_strength },
    { label: "Balans", value: horse.balance },
    { label: "Styrka", value: horse.strength },
  ];

  const activeTraining = (trainingStatus || []).find((t: any) => t.horse_id === id && !t.completed);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <h2 className="text-xl font-bold text-gray-200">{horse.name}</h2>
        <Badge>{horse.status}</Badge>
        <span className="text-sm text-gray-500">{horse.age_years} år | {horse.gender === "mare" ? "Sto" : horse.gender === "stallion" ? "Hingst" : "Valack"}</span>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <Card className="col-span-2">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">Egenskaper</h3>
          <div className="grid grid-cols-2 gap-3">
            {stats.map((s) => (
              <StatBar key={s.label} value={s.value} label={s.label} color={statColor(s.value)} />
            ))}
          </div>

          {/* Personality */}
          {(horse.personality_primary || horse.personality_secondary) && (
            <div className="mt-4 pt-3 border-t border-trav-border">
              <div className="text-xs text-gray-500 mb-1.5">Personlighet</div>
              <div className="flex gap-2">
                {horse.personality_primary && (
                  <span className="text-xs px-2 py-1 rounded bg-blue-900/30 text-blue-300 border border-blue-700/30">
                    {PERSONALITY_LABELS[horse.personality_primary] || horse.personality_primary}
                  </span>
                )}
                {horse.personality_secondary && (
                  <span className="text-xs px-2 py-1 rounded bg-indigo-900/30 text-indigo-300 border border-indigo-700/30">
                    {PERSONALITY_LABELS[horse.personality_secondary] || horse.personality_secondary}
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Special traits */}
          {horse.special_traits && horse.special_traits.length > 0 && (
            <div className="mt-3 pt-3 border-t border-trav-border">
              <div className="text-xs text-gray-500 mb-1.5">Speciella egenskaper</div>
              <div className="flex flex-wrap gap-1.5">
                {horse.special_traits.map((t: string) => {
                  const isPositive = TRAIT_POSITIVE.has(t);
                  return (
                    <span
                      key={t}
                      className={`text-[10px] px-2 py-0.5 rounded border ${
                        isPositive
                          ? "bg-green-900/20 text-green-300 border-green-700/30"
                          : "bg-red-900/20 text-red-300 border-red-700/30"
                      }`}
                    >
                      {TRAIT_LABELS[t] || t}
                    </span>
                  );
                })}
              </div>
            </div>
          )}
        </Card>

        <Card>
          <h3 className="text-sm font-semibold text-gray-300 mb-4">Information</h3>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between"><span className="text-gray-500">Ålder</span><span className="text-gray-300">{horse.age_years} år</span></div>
            <div className="flex justify-between"><span className="text-gray-500">Kön</span><span className="text-gray-300">{horse.gender === "mare" ? "Sto" : horse.gender === "stallion" ? "Hingst" : "Valack"}</span></div>
            <div className="flex justify-between"><span className="text-gray-500">Vikt</span><span className="text-gray-300">{horse.current_weight} kg</span></div>
            <div className="flex justify-between"><span className="text-gray-500">Kondition</span><span className="text-gray-300">{horse.condition}</span></div>
            <div className="flex justify-between"><span className="text-gray-500">Form</span><span className={`font-semibold ${horse.form >= 60 ? "text-green-400" : horse.form < 40 ? "text-red-400" : "text-yellow-400"}`}>{horse.form}</span></div>
            <div className="flex justify-between"><span className="text-gray-500">Energi</span><span className="text-gray-300">{horse.energy}</span></div>
            <div className="flex justify-between"><span className="text-gray-500">Humör</span><span className="text-gray-300">{horse.mood}</span></div>
            <div className="flex justify-between"><span className="text-gray-500">Trötthet</span><span className="text-gray-300">{horse.fatigue}</span></div>
            {horse.distance_optimum && (
              <div className="flex justify-between"><span className="text-gray-500">Optimaldistans</span><span className="text-gray-300">{horse.distance_optimum}m</span></div>
            )}
            {horse.surface_preference && (
              <div className="flex justify-between"><span className="text-gray-500">Underlag</span><span className="text-gray-300">{horse.surface_preference}</span></div>
            )}
          </div>
        </Card>
      </div>

      {/* Quick Train + Professional */}
      <div className="grid grid-cols-2 gap-6">
        <Card>
          <h3 className="text-sm font-semibold text-gray-300 mb-2">Formträning</h3>
          <p className="text-xs text-gray-500 mb-3">Snabb formträning som direkt ökar hästens form. Kostar 5 000 kr.</p>
          <Button
            onClick={() => quickTrainMutation.mutate()}
            disabled={quickTrainMutation.isPending || horse.status !== "ready"}
          >
            {quickTrainMutation.isPending ? "Tränar..." : "Formträning (5 000 kr)"}
          </Button>
          {quickTrainMutation.isError && (
            <p className="text-xs text-red-400 mt-2">{(quickTrainMutation.error as Error).message}</p>
          )}
          {quickTrainMutation.isSuccess && (
            <p className="text-xs text-green-400 mt-2">Formträning genomförd!</p>
          )}
        </Card>

        <Card>
          <h3 className="text-sm font-semibold text-gray-300 mb-2">Professionell träning</h3>
          <p className="text-xs text-gray-500 mb-3">Skicka hästen till en professionell tränare i 1-2 veckor för att förbättra en specifik stat.</p>
          {activeTraining ? (
            <div className="text-xs">
              <Badge color="#a855f7">Hos profstränare</Badge>
              <p className="text-gray-400 mt-1">Tränar: {activeTraining.target_stat} | Återgår vecka {activeTraining.end_week}</p>
            </div>
          ) : (
            <Button
              variant="secondary"
              onClick={() => setShowProModal(true)}
              disabled={horse.status !== "ready"}
            >
              Skicka till profstränare
            </Button>
          )}
        </Card>
      </div>

      {/* Professional Training Modal */}
      {showProModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setShowProModal(false)}>
          <div className="bg-trav-card border border-trav-border rounded-xl p-6 w-full max-w-sm" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-gray-200 mb-4">Professionell tränare</h3>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-gray-500 block mb-1">Stat att träna</label>
                <select value={proStat} onChange={(e) => setProStat(e.target.value)}
                  className="w-full px-3 py-2 bg-trav-bg border border-trav-border rounded-lg text-gray-200 text-sm">
                  {PRO_STATS.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">Träningsnivå</label>
                <select value={proLevel} onChange={(e) => setProLevel(e.target.value)}
                  className="w-full px-3 py-2 bg-trav-bg border border-trav-border rounded-lg text-gray-200 text-sm">
                  {PRO_LEVELS.map((l) => <option key={l.value} value={l.value}>{l.label}</option>)}
                </select>
              </div>
              <p className="text-xs text-gray-500">
                Hästen kommer vara borta i 1-2 veckor. Högre nivå = bättre resultat men dyrare.
              </p>
            </div>
            {proTrainMutation.isError && (
              <p className="text-xs text-red-400 mt-2">{(proTrainMutation.error as Error).message}</p>
            )}
            <div className="flex justify-end gap-3 mt-5">
              <Button variant="secondary" onClick={() => setShowProModal(false)}>Avbryt</Button>
              <Button onClick={() => proTrainMutation.mutate()} disabled={proTrainMutation.isPending}>
                {proTrainMutation.isPending ? "Skickar..." : "Skicka"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Shoe management */}
      <Card>
        <h3 className="text-sm font-semibold text-gray-300 mb-3">Skoning</h3>
        <p className="text-xs text-gray-500 mb-2">Nuvarande: <span className="text-trav-gold">{SHOES[horse.current_shoe] || horse.current_shoe}</span></p>
        <div className="flex gap-2 items-end">
          <select value={selectedShoe} onChange={(e) => setSelectedShoe(e.target.value)}
            className="flex-1 px-3 py-2 bg-trav-bg border border-trav-border rounded-lg text-gray-200 text-sm">
            <option value="">Välj sko...</option>
            {Object.entries(SHOES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          <Button onClick={() => shoeMutation.mutate()} disabled={!selectedShoe || shoeMutation.isPending}>
            {shoeMutation.isPending ? "Byter..." : "Byt sko"}
          </Button>
        </div>
        {/* Shoe effects table */}
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-[11px]">
            <thead>
              <tr className="text-gray-500 border-b border-trav-border">
                <th className="text-left py-1.5 pr-2">Sko</th>
                <th className="text-center py-1.5 px-1">Fart</th>
                <th className="text-center py-1.5 px-1">Galopprisk</th>
                <th className="text-center py-1.5 px-1">Grepp</th>
                <th className="text-center py-1.5 px-1">Vått</th>
                <th className="text-center py-1.5 px-1">Vinter</th>
                <th className="text-center py-1.5 px-1">Vikt</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(SHOE_EFFECTS).map(([key, fx]) => (
                <tr key={key} className={`border-b border-trav-border/30 ${horse.current_shoe === key ? "bg-trav-gold/10" : ""}`}>
                  <td className={`py-1.5 pr-2 font-medium ${horse.current_shoe === key ? "text-trav-gold" : "text-gray-300"}`}>{SHOES[key]}</td>
                  <td className={`py-1.5 px-1 text-center ${fx.speed.startsWith("+") ? "text-green-400" : fx.speed.startsWith("-") ? "text-red-400" : "text-gray-400"}`}>{fx.speed}</td>
                  <td className={`py-1.5 px-1 text-center ${fx.gallop.includes("+") ? "text-red-400" : fx.gallop.includes("-") ? "text-green-400" : "text-gray-400"}`}>{fx.gallop}</td>
                  <td className="py-1.5 px-1 text-center text-gray-400">{fx.gripNormal}</td>
                  <td className="py-1.5 px-1 text-center text-gray-400">{fx.gripWet}</td>
                  <td className="py-1.5 px-1 text-center text-gray-400">{fx.gripWinter}</td>
                  <td className="py-1.5 px-1 text-center text-gray-500">{fx.weight}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Training management */}
      <Card>
        <h3 className="text-sm font-semibold text-gray-300 mb-3">Träning</h3>
        <p className="text-xs text-gray-500 mb-2">Nuvarande: <span className="text-trav-gold">{PROGRAMS[horse.current_training] || horse.current_training || "Vila"}</span></p>

        {/* Training lock status */}
        {horse.training_locked_until && gameState?.total_game_days && horse.training_locked_until > gameState.total_game_days && (
          <div className="mb-3 p-3 rounded-lg bg-amber-900/20 border border-amber-700/30">
            <div className="flex items-center gap-2 text-amber-300 text-sm font-medium">
              <span>⏳</span>
              <span>Hästen tränar — {horse.training_locked_until - gameState.total_game_days} dag(ar) kvar</span>
            </div>
            <p className="text-xs text-amber-400/70 mt-1">Byt av träningsprogram kan göras efter att nuvarande pass är klart.</p>
          </div>
        )}

        {/* Training result from last session */}
        {horse.training_last_result && Object.keys(horse.training_last_result).length > 0 && (
          <div className="mb-3 p-3 rounded-lg bg-green-900/20 border border-green-700/30">
            <div className="text-green-300 text-sm font-medium mb-1">📊 Senaste träningsresultat</div>
            <div className="flex flex-wrap gap-2">
              {Object.entries(horse.training_last_result as Record<string, number>)
                .filter(([, v]) => v > 0)
                .map(([stat, val]) => (
                  <span key={stat} className="text-xs px-2 py-0.5 rounded bg-green-900/30 text-green-400 border border-green-700/30">
                    {STAT_LABELS[stat] || stat} +{val}
                  </span>
                ))}
              {Object.values(horse.training_last_result as Record<string, number>).every((v) => v === 0) && (
                <span className="text-xs text-gray-500">Ingen förbättring denna gång</span>
              )}
            </div>
          </div>
        )}

        <div className="flex gap-2 items-end">
          <select value={selectedProgram} onChange={(e) => setSelectedProgram(e.target.value)}
            className="flex-1 px-3 py-2 bg-trav-bg border border-trav-border rounded-lg text-gray-200 text-sm">
            <option value="">Välj program...</option>
            {Object.entries(PROGRAMS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          <select value={selectedIntensity} onChange={(e) => setSelectedIntensity(e.target.value)}
            className="px-3 py-2 bg-trav-bg border border-trav-border rounded-lg text-gray-200 text-sm">
            {Object.entries(INTENSITIES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          <Button
            onClick={() => trainingMutation.mutate()}
            disabled={
              !selectedProgram ||
              trainingMutation.isPending ||
              (horse.training_locked_until && gameState?.total_game_days && horse.training_locked_until > gameState.total_game_days)
            }
          >
            {trainingMutation.isPending ? "Sparar..." : "Ändra träning"}
          </Button>
        </div>
        {trainingMutation.isError && (
          <p className="text-xs text-red-400 mt-2">{(trainingMutation.error as Error).message}</p>
        )}
      </Card>

      {/* Career + Start Points */}
      <Card>
        <h3 className="text-sm font-semibold text-gray-300 mb-3">Karriär</h3>
        <div className="grid grid-cols-4 gap-6 text-center">
          <div>
            <div className="text-2xl font-bold text-gray-200">{horse.total_starts || 0}</div>
            <div className="text-xs text-gray-500">Starter</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-trav-gold">{horse.total_wins || 0}</div>
            <div className="text-xs text-gray-500">Segrar</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-green-400">{formatOre(horse.total_earnings || 0)}</div>
            <div className="text-xs text-gray-500">Intjäning</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-blue-400">{startPoints?.total ?? 0}</div>
            <div className="text-xs text-gray-500">Startpoäng</div>
          </div>
        </div>
        {startPoints && startPoints.total > 0 && (
          <div className="mt-3 text-xs text-gray-500">
            Placeringspoäng: {startPoints.placement_points} | Intjäningspoäng: {startPoints.earnings_points}
          </div>
        )}
      </Card>

      {/* Compatibility */}
      {horse.compatibility_with_drivers?.length > 0 && (
        <CompatibilitySection horseId={id} drivers={horse.compatibility_with_drivers} />
      )}
    </div>
  );
}
