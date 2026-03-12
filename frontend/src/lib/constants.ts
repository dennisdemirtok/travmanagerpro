export const COLORS = {
  bg: "#0C0E13",
  bgCard: "#141720",
  bgHover: "#1A1E2A",
  bgActive: "#1E2333",
  border: "#252A3A",
  borderLight: "#2E3448",
  gold: "#D4A853",
  goldDim: "#B8923D",
  goldBright: "#F0C864",
  green: "#4ADE80",
  greenDim: "#22C55E",
  red: "#F87171",
  redDim: "#EF4444",
  blue: "#60A5FA",
  purple: "#A78BFA",
  orange: "#FB923C",
  text: "#E8E6E1",
  textDim: "#9CA3AF",
  textMuted: "#6B7280",
};

export const STATUS_LABELS: Record<string, string> = {
  ready: "Redo",
  injured: "Skadad",
  resting: "Vila",
  sick: "Sjuk",
  retired: "Pensionerad",
};

export const STATUS_COLORS: Record<string, string> = {
  ready: COLORS.green,
  injured: COLORS.red,
  resting: COLORS.blue,
  sick: COLORS.orange,
  retired: COLORS.textMuted,
};

export const SHOE_LABELS: Record<string, string> = {
  normal: "Normalsko",
  light_aluminum: "Lättsko",
  barefoot: "Barfota",
  studs: "Broddar",
  half_studs: "Halvbroddar",
};

export const POSITIONING_OPTIONS = [
  { value: "lead", label: "Ledning" },
  { value: "second", label: "Andra par" },
  { value: "third", label: "Tredje par" },
  { value: "trailing", label: "Sista" },
  { value: "free", label: "Fri" },
];

export const TEMPO_OPTIONS = [
  { value: "fast", label: "Snabbt" },
  { value: "balanced", label: "Balanserat" },
  { value: "conservative", label: "Konservativt" },
  { value: "adaptive", label: "Adaptivt" },
];

export const SPRINT_OPTIONS = [
  { value: "early_600m", label: "Tidigt (600m)" },
  { value: "normal_400m", label: "Normalt (400m)" },
  { value: "late_200m", label: "Sent (200m)" },
  { value: "all_out_sprint", label: "Allt ut" },
];

export const GALLOP_SAFETY_OPTIONS = [
  { value: "cautious", label: "Försiktig" },
  { value: "normal", label: "Normal" },
  { value: "aggressive", label: "Aggressiv" },
];
