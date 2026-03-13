const API_BASE = "/api/v1";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (res.status === 401) {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `API error ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Auth
  register: (data: { username: string; email: string; password: string; stable_name: string }) =>
    apiFetch<{ access_token: string; refresh_token: string; token_type: string }>("/auth/register", { method: "POST", body: JSON.stringify(data) }),
  login: (username: string, password: string) =>
    apiFetch<{ access_token: string; refresh_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),

  // Game
  initGame: () => apiFetch<{ status: string; game_week: number }>("/game/init", { method: "POST" }),
  getGameState: () => apiFetch<any>("/game/state"),

  // Stable
  getStable: () => apiFetch<any>("/stable"),
  getTracks: () => apiFetch<any>("/stable/tracks"),
  getMorningReport: () => apiFetch<any>("/stable/morning-report"),

  // Horses
  getHorses: () => apiFetch<any>("/horses"),
  getHorse: (id: string) => apiFetch<any>(`/horses/${id}`),

  // Drivers
  getDrivers: () => apiFetch<any>("/drivers"),
  getCompatibility: (driverId: string, horseId: string) => apiFetch<any>(`/drivers/${driverId}/compatibility/${horseId}`),
  checkCompatibility: (driverId: string, horseId: string) =>
    apiFetch<any>(`/drivers/${driverId}/compatibility/${horseId}/check`, { method: "POST" }),

  // Races
  getRaceSchedule: () => apiFetch<any>("/races/schedule"),
  enterRace: (raceId: string, data: any) => apiFetch<any>(`/races/${raceId}/enter`, { method: "POST", body: JSON.stringify(data) }),
  getRaceResult: (raceId: string) => apiFetch<any>(`/races/${raceId}/result`),

  // Horse start points
  getHorseStartPoints: (horseId: string) => apiFetch<any>(`/horses/${horseId}/start-points`),

  // Finances
  getFinancialOverview: () => apiFetch<any>("/finances/overview"),
  getTransactions: (params?: { category?: string; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.category) qs.set("category", params.category);
    if (params?.limit) qs.set("limit", String(params.limit));
    const q = qs.toString();
    return apiFetch<any>(`/finances/transactions${q ? `?${q}` : ""}`);
  },

  // Events
  getEvents: (unread?: boolean) => apiFetch<any>(`/events${unread ? "?unread=true" : ""}`),

  // Horse management
  changeShoe: (horseId: string, shoe_type: string) =>
    apiFetch<any>(`/horses/${horseId}/shoe`, { method: "PUT", body: JSON.stringify({ shoe_type }) }),
  changeTraining: (horseId: string, program: string, intensity: string = "normal") =>
    apiFetch<any>(`/horses/${horseId}/training`, { method: "PUT", body: JSON.stringify({ program, intensity }) }),
  updateFeed: (horseId: string, feeds: { feed_type: string; percentage: number }[]) =>
    apiFetch<any>(`/horses/${horseId}/feed`, { method: "PUT", body: JSON.stringify({ feeds }) }),

  // Race management
  updateTactics: (entryId: string, tactics: Record<string, string>) =>
    apiFetch<any>(`/races/entries/${entryId}/tactics`, { method: "PUT", body: JSON.stringify(tactics) }),
  withdrawEntry: (entryId: string) =>
    apiFetch<any>(`/races/entries/${entryId}`, { method: "DELETE" }),

  // Stable management
  dailyCheckup: () => apiFetch<any>("/stable/daily-checkup", { method: "POST" }),
  createPressRelease: (tone: string, content: string) =>
    apiFetch<any>("/stable/press-release", { method: "POST", body: JSON.stringify({ tone, content }) }),

  // Driver contracts
  renewContract: (driverId: string, contract_type: string, weeks: number = 16) =>
    apiFetch<any>(`/drivers/${driverId}/contract`, { method: "POST", body: JSON.stringify({ contract_type, weeks }) }),
  terminateContract: (driverId: string) =>
    apiFetch<any>(`/drivers/${driverId}/contract`, { method: "DELETE" }),

  // Event actions
  handleEventAction: (eventId: string) =>
    apiFetch<any>(`/events/${eventId}/action`, { method: "POST" }),

  // Sponsors
  getSponsors: () => apiFetch<any>("/sponsors"),
  getSponsorContracts: () => apiFetch<any>("/sponsors/contracts"),
  signSponsor: (sponsorId: string) =>
    apiFetch<any>("/sponsors/sign", { method: "POST", body: JSON.stringify({ sponsor_id: sponsorId }) }),
  terminateSponsorContract: (contractId: string) =>
    apiFetch<any>(`/sponsors/contracts/${contractId}`, { method: "DELETE" }),
  collectSponsorIncome: () =>
    apiFetch<any>("/sponsors/collect", { method: "POST" }),

  // Horse Market
  getMarketListings: () => apiFetch<any>("/market/listings"),
  listHorseForSale: (horseId: string, startingPrice: number, buyoutPrice?: number) =>
    apiFetch<any>("/market/list", {
      method: "POST",
      body: JSON.stringify({ horse_id: horseId, starting_price: startingPrice, buyout_price: buyoutPrice }),
    }),
  placeBid: (listingId: string, amount: number) =>
    apiFetch<any>(`/market/listings/${listingId}/bid`, {
      method: "POST",
      body: JSON.stringify({ amount }),
    }),
  buyoutHorse: (listingId: string) =>
    apiFetch<any>(`/market/listings/${listingId}/buyout`, { method: "POST" }),
  acceptBid: (listingId: string) =>
    apiFetch<any>(`/market/listings/${listingId}/accept`, { method: "POST" }),
  giveAwayHorse: (horseId: string) =>
    apiFetch<any>(`/market/give-away/${horseId}`, { method: "POST" }),
  cancelListing: (listingId: string) =>
    apiFetch<any>(`/market/listings/${listingId}`, { method: "DELETE" }),
  getHorseProfile: (horseId: string) => apiFetch<any>(`/market/horse/${horseId}`),

  // Breeding
  getStallions: () => apiFetch<any>("/breeding/stallions"),
  breed: (mareId: string, stallionId: string) =>
    apiFetch<any>("/breeding/breed", {
      method: "POST",
      body: JSON.stringify({ mare_id: mareId, stallion_id: stallionId }),
    }),
  getBreedingStatus: () => apiFetch<any>("/breeding/status"),
  getPedigree: (horseId: string) => apiFetch<any>(`/breeding/pedigree/${horseId}`),

  // Training
  quickTrain: (horseId: string) =>
    apiFetch<any>("/training/quick-train", {
      method: "POST",
      body: JSON.stringify({ horse_id: horseId }),
    }),
  sendToProfessional: (horseId: string, targetStat: string, trainerLevel: string = "standard") =>
    apiFetch<any>("/training/professional", {
      method: "POST",
      body: JSON.stringify({ horse_id: horseId, target_stat: targetStat, trainer_level: trainerLevel }),
    }),
  getTrainingStatus: () => apiFetch<any>("/training/professional/status"),

  // Stable — home track & costs
  setHomeTrack: (trackId: string) =>
    apiFetch<any>("/stable/home-track", {
      method: "PUT",
      body: JSON.stringify({ track_id: trackId }),
    }),
  getWeeklyCosts: () => apiFetch<any>("/stable/weekly-costs"),
  getBoxInfo: () => apiFetch<any>("/stable/box-info"),
  upgradeBoxes: () => apiFetch<any>("/stable/upgrade-boxes", { method: "POST" }),

  // Horse database
  getHorseDatabase: (sort: string = "earnings", search: string = "") =>
    apiFetch<any>(`/horses/database?sort=${sort}&search=${encodeURIComponent(search)}`),

  // Leaderboard
  getStableLeaderboard: () => apiFetch<any>("/leaderboard/stables"),
  getHorseLeaderboard: () => apiFetch<any>("/leaderboard/horses"),

  // Dev
  advanceTime: (hours: number = 24) =>
    apiFetch<any>(`/game/dev/advance?hours=${hours}`, { method: "POST" }),
  simulateNext: () =>
    apiFetch<any>("/game/dev/simulate-next", { method: "POST" }),
  devTick: () =>
    apiFetch<any>("/game/dev/tick", { method: "POST" }),
};
