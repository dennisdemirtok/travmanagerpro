import { useState, useEffect, useRef } from "react";

const COLORS = {
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

// --- Mock Data ---
const HORSES = [
  { id: 1, name: "Bliansen", age: 5, speed: 78, endurance: 82, mentality: 71, start: 85, sprint: 74, condition: 92, health: 88, weight: 485, gallop_risk: 12, wins: 8, races: 24, earnings: 342000, training: "Intervall", shoe: "Lättsko", status: "Redo", trend: "up" },
  { id: 2, name: "Expressen", age: 4, speed: 85, endurance: 68, mentality: 65, start: 72, sprint: 88, condition: 78, health: 95, weight: 472, gallop_risk: 22, wins: 5, races: 16, earnings: 218000, training: "Spurt", shoe: "Normalsko", status: "Redo", trend: "up" },
  { id: 3, name: "Dalero", age: 7, speed: 72, endurance: 90, mentality: 88, start: 68, sprint: 65, condition: 85, health: 62, weight: 498, gallop_risk: 8, wins: 15, races: 52, earnings: 890000, training: "Vila", shoe: "Broddar", status: "Skadad", trend: "down" },
  { id: 4, name: "Nattsvansen", age: 3, speed: 65, endurance: 55, mentality: 58, start: 70, sprint: 62, condition: 88, health: 97, weight: 445, gallop_risk: 28, wins: 1, races: 5, earnings: 45000, training: "Mental", shoe: "Barfota", status: "Redo", trend: "up" },
  { id: 5, name: "Guldpilen", age: 6, speed: 81, endurance: 79, mentality: 75, start: 80, sprint: 77, condition: 70, health: 80, weight: 490, gallop_risk: 15, wins: 11, races: 38, earnings: 567000, training: "Långdistans", shoe: "Normalsko", status: "Redo", trend: "stable" },
];

const DRIVERS = [
  { id: 1, name: "Erik Lindblom", skill: 82, tactical: 78, sprint: 85, gallop: 80, exp: 74, salary: 12000, contract: 12 },
  { id: 2, name: "Anna Svensson", skill: 75, tactical: 88, sprint: 72, gallop: 85, exp: 68, salary: 9500, contract: 8 },
];

const UPCOMING_RACES = [
  { id: 1, name: "V75-1 Silverdivisionen", distance: "2140m", start: "Volt", prize: "150 000 kr", day: "Lördag", time: "15:20", entries: 12, division: "Silver" },
  { id: 2, name: "Ungloppserie Omg 3", distance: "1640m", start: "Auto", prize: "60 000 kr", day: "Onsdag", time: "19:45", entries: 8, division: "Ung" },
  { id: 3, name: "Gulddivisionen Kval", distance: "2640m", start: "Volt", prize: "250 000 kr", day: "Lördag", time: "16:05", entries: 10, division: "Guld" },
];

const NEWS = [
  { type: "injury", text: "Dalero halt efter gårdagens träning — veterinär tillkallad", time: "2 tim sedan" },
  { type: "transfer", text: "Ny hingst 'Stormkungen' ute på auktion — bud från 180 000 kr", time: "4 tim sedan" },
  { type: "race", text: "Expressen anmäld till Ungloppsserie Omg 3 på onsdag", time: "6 tim sedan" },
  { type: "sponsor", text: "Betsafe erbjuder sponsoravtal — 25 000 kr/månad", time: "1 dag sedan" },
  { type: "achievement", text: "Achievement upplåst: 'Femte vinsten'", time: "2 dagar sedan" },
];

const FINANCES = { balance: 487250, income_week: 68000, expense_week: 52000, trend: [420, 435, 448, 460, 455, 472, 487] };

// --- Components ---

function StatBar({ value, max = 100, color = COLORS.gold, label, small = false }) {
  const pct = Math.min((value / max) * 100, 100);
  const h = small ? "4px" : "6px";
  return (
    <div style={{ flex: 1 }}>
      {label && <div style={{ fontSize: 11, color: COLORS.textMuted, marginBottom: 3 }}>{label}</div>}
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <div style={{ flex: 1, height: h, background: COLORS.border, borderRadius: 3, overflow: "hidden" }}>
          <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: 3, transition: "width 0.6s ease" }} />
        </div>
        <span style={{ fontSize: small ? 11 : 12, color: COLORS.textDim, fontVariantNumeric: "tabular-nums", minWidth: 24, textAlign: "right" }}>{value}</span>
      </div>
    </div>
  );
}

function Badge({ children, color = COLORS.gold }) {
  return (
    <span style={{
      display: "inline-block", padding: "2px 8px", borderRadius: 4, fontSize: 11, fontWeight: 600,
      background: color + "18", color, border: `1px solid ${color}33`, letterSpacing: 0.3
    }}>{children}</span>
  );
}

function Card({ children, style, onClick, hover = false }) {
  const [hovered, setHovered] = useState(false);
  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onClick={onClick}
      style={{
        background: hovered && hover ? COLORS.bgHover : COLORS.bgCard,
        border: `1px solid ${hovered && hover ? COLORS.borderLight : COLORS.border}`,
        borderRadius: 10, padding: 18, transition: "all 0.2s ease",
        cursor: onClick ? "pointer" : "default", ...style
      }}
    >{children}</div>
  );
}

function MiniChart({ data, color = COLORS.gold, height = 40, width = 120 }) {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((v - min) / range) * (height - 4) - 2;
    return `${x},${y}`;
  }).join(" ");
  return (
    <svg width={width} height={height} style={{ display: "block" }}>
      <defs>
        <linearGradient id={`grad-${color.replace("#","")}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon
        points={`0,${height} ${points} ${width},${height}`}
        fill={`url(#grad-${color.replace("#","")})`}
      />
      <polyline points={points} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" />
    </svg>
  );
}

function TrendArrow({ trend }) {
  if (trend === "up") return <span style={{ color: COLORS.green, fontSize: 14 }}>▲</span>;
  if (trend === "down") return <span style={{ color: COLORS.red, fontSize: 14 }}>▼</span>;
  return <span style={{ color: COLORS.textMuted, fontSize: 12 }}>●</span>;
}

// --- Screens ---

function DashboardScreen({ onNavigate }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Top summary */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
        {[
          { label: "Saldo", value: `${(FINANCES.balance / 1000).toFixed(0)}k kr`, sub: "+16k denna vecka", color: COLORS.green, icon: "💰" },
          { label: "Hästar", value: HORSES.length, sub: `${HORSES.filter(h => h.status === "Redo").length} redo`, color: COLORS.gold, icon: "🐴" },
          { label: "Nästa lopp", value: "Ons", sub: "19:45 — Unglopp", color: COLORS.blue, icon: "🏁" },
          { label: "Division", value: "Silver", sub: "3:e plats", color: COLORS.purple, icon: "🏆" },
        ].map((item, i) => (
          <Card key={i} style={{ textAlign: "center", padding: 16 }}>
            <div style={{ fontSize: 22, marginBottom: 4 }}>{item.icon}</div>
            <div style={{ fontSize: 11, color: COLORS.textMuted, textTransform: "uppercase", letterSpacing: 1.2, marginBottom: 4 }}>{item.label}</div>
            <div style={{ fontSize: 22, fontWeight: 700, color: item.color, fontFamily: "'DM Serif Display', Georgia, serif" }}>{item.value}</div>
            <div style={{ fontSize: 11, color: COLORS.textDim, marginTop: 2 }}>{item.sub}</div>
          </Card>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        {/* News feed */}
        <Card style={{ padding: 0 }}>
          <div style={{ padding: "14px 18px 10px", borderBottom: `1px solid ${COLORS.border}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.text, letterSpacing: 0.5, textTransform: "uppercase" }}>Stallnyheter</span>
            <span style={{ fontSize: 11, color: COLORS.textMuted }}>Idag</span>
          </div>
          <div style={{ padding: "6px 0" }}>
            {NEWS.map((n, i) => (
              <div key={i} style={{ display: "flex", gap: 10, padding: "10px 18px", borderBottom: i < NEWS.length - 1 ? `1px solid ${COLORS.border}10` : "none", alignItems: "flex-start" }}>
                <span style={{ fontSize: 16, marginTop: 1 }}>
                  {{ injury: "🩺", transfer: "📋", race: "🏇", sponsor: "💼", achievement: "⭐" }[n.type]}
                </span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 12.5, color: COLORS.text, lineHeight: 1.4 }}>{n.text}</div>
                  <div style={{ fontSize: 10.5, color: COLORS.textMuted, marginTop: 3 }}>{n.time}</div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Quick actions + economy */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <Card>
            <div style={{ fontSize: 13, fontWeight: 600, color: COLORS.text, letterSpacing: 0.5, textTransform: "uppercase", marginBottom: 12 }}>Ekonomi</div>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div>
                <div style={{ fontSize: 26, fontWeight: 700, color: COLORS.gold, fontFamily: "'DM Serif Display', Georgia, serif" }}>
                  {FINANCES.balance.toLocaleString("sv-SE")} kr
                </div>
                <div style={{ display: "flex", gap: 16, marginTop: 6 }}>
                  <span style={{ fontSize: 12, color: COLORS.green }}>▲ +{FINANCES.income_week.toLocaleString("sv-SE")} kr/v</span>
                  <span style={{ fontSize: 12, color: COLORS.red }}>▼ −{FINANCES.expense_week.toLocaleString("sv-SE")} kr/v</span>
                </div>
              </div>
              <MiniChart data={FINANCES.trend} color={COLORS.green} width={100} height={44} />
            </div>
          </Card>

          <Card>
            <div style={{ fontSize: 13, fontWeight: 600, color: COLORS.text, letterSpacing: 0.5, textTransform: "uppercase", marginBottom: 12 }}>Snabbåtgärder</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              {[
                { label: "Skriv pressmeddelande", icon: "📰", action: () => {} },
                { label: "Anmäl till lopp", icon: "🏁", action: () => onNavigate("race") },
                { label: "Transfermarknad", icon: "🔄", action: () => onNavigate("transfer") },
                { label: "Stallvisning", icon: "🏠", action: () => {} },
              ].map((a, i) => (
                <div key={i} onClick={a.action} style={{
                  display: "flex", alignItems: "center", gap: 8, padding: "10px 12px", borderRadius: 8,
                  background: COLORS.bgHover, cursor: "pointer", transition: "background 0.15s",
                  border: `1px solid ${COLORS.border}`,
                }}>
                  <span style={{ fontSize: 16 }}>{a.icon}</span>
                  <span style={{ fontSize: 12, color: COLORS.text }}>{a.label}</span>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <div style={{ fontSize: 13, fontWeight: 600, color: COLORS.text, letterSpacing: 0.5, textTransform: "uppercase", marginBottom: 10 }}>Kommande lopp</div>
            {UPCOMING_RACES.slice(0, 2).map((r, i) => (
              <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 0", borderBottom: i === 0 ? `1px solid ${COLORS.border}30` : "none" }}>
                <div>
                  <div style={{ fontSize: 12.5, color: COLORS.text, fontWeight: 500 }}>{r.name}</div>
                  <div style={{ fontSize: 11, color: COLORS.textMuted }}>{r.distance} • {r.start} • {r.entries} hästar</div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: 12, color: COLORS.gold, fontWeight: 600 }}>{r.day} {r.time}</div>
                  <div style={{ fontSize: 11, color: COLORS.textMuted }}>{r.prize}</div>
                </div>
              </div>
            ))}
          </Card>
        </div>
      </div>
    </div>
  );
}

function StableScreen({ onSelectHorse }) {
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div>
          <div style={{ fontSize: 11, color: COLORS.textMuted, textTransform: "uppercase", letterSpacing: 1.2 }}>Ditt stall</div>
          <div style={{ fontSize: 18, fontWeight: 700, color: COLORS.text, fontFamily: "'DM Serif Display', Georgia, serif" }}>{HORSES.length} hästar • 2 kuskar</div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {["Alla", "Redo", "Skadad", "Vila"].map((f, i) => (
            <button key={i} style={{
              padding: "6px 14px", borderRadius: 6, border: `1px solid ${i === 0 ? COLORS.gold : COLORS.border}`,
              background: i === 0 ? COLORS.gold + "15" : "transparent", color: i === 0 ? COLORS.gold : COLORS.textDim,
              fontSize: 12, cursor: "pointer", fontWeight: 500
            }}>{f}</button>
          ))}
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {HORSES.map((h) => (
          <Card key={h.id} hover onClick={() => onSelectHorse(h)} style={{ padding: 14 }}>
            <div style={{ display: "grid", gridTemplateColumns: "200px 1fr 140px 100px", alignItems: "center", gap: 16 }}>
              {/* Name & basics */}
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <div style={{
                  width: 40, height: 40, borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center",
                  background: h.status === "Skadad" ? COLORS.red + "15" : COLORS.gold + "10",
                  border: `1px solid ${h.status === "Skadad" ? COLORS.red + "30" : COLORS.gold + "25"}`,
                  fontSize: 20
                }}>🐴</div>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: COLORS.text, display: "flex", alignItems: "center", gap: 6 }}>
                    {h.name} <TrendArrow trend={h.trend} />
                  </div>
                  <div style={{ fontSize: 11, color: COLORS.textMuted }}>{h.age} år • {h.weight} kg • <Badge color={h.status === "Skadad" ? COLORS.red : COLORS.green}>{h.status}</Badge></div>
                </div>
              </div>

              {/* Stats */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 8 }}>
                <StatBar value={h.speed} label="SNB" color={COLORS.gold} small />
                <StatBar value={h.endurance} label="UTH" color={COLORS.blue} small />
                <StatBar value={h.mentality} label="MEN" color={COLORS.purple} small />
                <StatBar value={h.start} label="STA" color={COLORS.orange} small />
                <StatBar value={h.sprint} label="SPU" color={COLORS.green} small />
              </div>

              {/* Condition */}
              <div>
                <StatBar value={h.condition} label="Kondition" color={COLORS.green} small />
                <div style={{ marginTop: 4 }}>
                  <StatBar value={h.health} label="Hälsa" color={h.health > 75 ? COLORS.green : COLORS.red} small />
                </div>
              </div>

              {/* Record */}
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: COLORS.gold }}>{h.wins}/{h.races}</div>
                <div style={{ fontSize: 11, color: COLORS.textMuted }}>{(h.earnings / 1000).toFixed(0)}k kr</div>
                <div style={{ fontSize: 10, color: COLORS.textMuted, marginTop: 2 }}>{h.training} • {h.shoe}</div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

function HorseDetailScreen({ horse, onBack }) {
  const [tab, setTab] = useState("overview");
  const h = horse;

  const trainingOptions = [
    { name: "Intervall", desc: "Snabbhet + Uthållighet", cost: "4 500 kr/v", load: "Hög", icon: "⚡" },
    { name: "Långdistans", desc: "Uthållighet + Kondition", cost: "3 000 kr/v", load: "Låg", icon: "🛤️" },
    { name: "Startträning", desc: "Startförmåga", cost: "3 500 kr/v", load: "Medel", icon: "🚀" },
    { name: "Spurtträning", desc: "Spurtstyrka", cost: "4 000 kr/v", load: "Medel", icon: "💨" },
    { name: "Mentalträning", desc: "Mentalitet, −galopprisk", cost: "2 500 kr/v", load: "Låg", icon: "🧠" },
    { name: "Vila", desc: "Återhämtning", cost: "500 kr/v", load: "Ingen", icon: "😴" },
  ];

  return (
    <div>
      <div onClick={onBack} style={{ display: "inline-flex", alignItems: "center", gap: 6, cursor: "pointer", fontSize: 12, color: COLORS.textMuted, marginBottom: 16, padding: "4px 0" }}>
        ← Tillbaka till stallet
      </div>

      {/* Header */}
      <Card style={{ marginBottom: 16, display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
          <div style={{
            width: 64, height: 64, borderRadius: 12, display: "flex", alignItems: "center", justifyContent: "center",
            background: `linear-gradient(135deg, ${COLORS.gold}20, ${COLORS.gold}08)`,
            border: `1px solid ${COLORS.gold}30`, fontSize: 32
          }}>🐴</div>
          <div>
            <div style={{ fontSize: 24, fontWeight: 700, color: COLORS.text, fontFamily: "'DM Serif Display', Georgia, serif", display: "flex", alignItems: "center", gap: 10 }}>
              {h.name} <TrendArrow trend={h.trend} /> <Badge color={h.status === "Skadad" ? COLORS.red : COLORS.green}>{h.status}</Badge>
            </div>
            <div style={{ fontSize: 13, color: COLORS.textDim, marginTop: 4 }}>
              {h.age} år • {h.weight} kg • Galopprisk: <span style={{ color: h.gallop_risk > 20 ? COLORS.red : h.gallop_risk > 15 ? COLORS.orange : COLORS.green }}>{h.gallop_risk}%</span>
            </div>
            <div style={{ fontSize: 12, color: COLORS.textMuted, marginTop: 2 }}>
              Rekord: {h.wins} vinster av {h.races} starter • Intjänat: {h.earnings.toLocaleString("sv-SE")} kr
            </div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button style={{ padding: "8px 16px", borderRadius: 8, background: COLORS.gold, color: COLORS.bg, fontWeight: 600, fontSize: 12, border: "none", cursor: "pointer" }}>Anmäl till lopp</button>
          <button style={{ padding: "8px 16px", borderRadius: 8, background: "transparent", color: COLORS.textDim, fontWeight: 500, fontSize: 12, border: `1px solid ${COLORS.border}`, cursor: "pointer" }}>Sälj</button>
        </div>
      </Card>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 2, marginBottom: 16, background: COLORS.bgCard, borderRadius: 8, padding: 3, border: `1px solid ${COLORS.border}` }}>
        {["overview", "training", "health", "history"].map((t) => (
          <button key={t} onClick={() => setTab(t)} style={{
            flex: 1, padding: "8px 0", borderRadius: 6, border: "none", cursor: "pointer",
            background: tab === t ? COLORS.bgActive : "transparent",
            color: tab === t ? COLORS.gold : COLORS.textMuted,
            fontSize: 12, fontWeight: 600, textTransform: "uppercase", letterSpacing: 0.6, transition: "all 0.15s"
          }}>{{ overview: "Översikt", training: "Träning", health: "Hälsa & Foder", history: "Historik" }[t]}</button>
        ))}
      </div>

      {tab === "overview" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <Card>
            <div style={{ fontSize: 13, fontWeight: 600, color: COLORS.text, marginBottom: 14, textTransform: "uppercase", letterSpacing: 0.5 }}>Egenskaper</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {[
                { label: "Snabbhet", value: h.speed, color: COLORS.gold },
                { label: "Uthållighet", value: h.endurance, color: COLORS.blue },
                { label: "Mentalitet", value: h.mentality, color: COLORS.purple },
                { label: "Startförmåga", value: h.start, color: COLORS.orange },
                { label: "Spurtstyrka", value: h.sprint, color: COLORS.green },
              ].map((s, i) => (
                <StatBar key={i} value={s.value} label={s.label} color={s.color} />
              ))}
            </div>
          </Card>
          <Card>
            <div style={{ fontSize: 13, fontWeight: 600, color: COLORS.text, marginBottom: 14, textTransform: "uppercase", letterSpacing: 0.5 }}>Fysisk status</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <StatBar value={h.condition} label="Kondition" color={COLORS.green} />
              <StatBar value={h.health} label="Hälsa" color={h.health > 75 ? COLORS.green : COLORS.red} />
              <StatBar value={100 - h.gallop_risk} label="Galoppkontroll" color={h.gallop_risk > 20 ? COLORS.red : COLORS.green} />
            </div>
            <div style={{ marginTop: 16, padding: "12px", background: COLORS.bgHover, borderRadius: 8 }}>
              <div style={{ fontSize: 11, color: COLORS.textMuted, marginBottom: 6 }}>Nuvarande utrustning</div>
              <div style={{ display: "flex", gap: 12 }}>
                <div><span style={{ fontSize: 11, color: COLORS.textMuted }}>Skoning:</span> <span style={{ fontSize: 12, color: COLORS.text, fontWeight: 500 }}>{h.shoe}</span></div>
                <div><span style={{ fontSize: 11, color: COLORS.textMuted }}>Träning:</span> <span style={{ fontSize: 12, color: COLORS.text, fontWeight: 500 }}>{h.training}</span></div>
              </div>
            </div>
          </Card>
        </div>
      )}

      {tab === "training" && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
          {trainingOptions.map((t, i) => (
            <Card key={i} hover style={{ cursor: "pointer", border: t.name === h.training ? `1px solid ${COLORS.gold}60` : undefined, background: t.name === h.training ? COLORS.gold + "08" : undefined }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
                <span style={{ fontSize: 24 }}>{t.icon}</span>
                {t.name === h.training && <Badge color={COLORS.gold}>AKTIV</Badge>}
              </div>
              <div style={{ fontSize: 14, fontWeight: 600, color: COLORS.text, marginBottom: 4 }}>{t.name}</div>
              <div style={{ fontSize: 12, color: COLORS.textDim, marginBottom: 8 }}>{t.desc}</div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }}>
                <span style={{ color: COLORS.textMuted }}>{t.cost}</span>
                <span style={{ color: t.load === "Hög" ? COLORS.red : t.load === "Medel" ? COLORS.orange : COLORS.green }}>Belastning: {t.load}</span>
              </div>
            </Card>
          ))}
        </div>
      )}

      {tab === "health" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <Card>
            <div style={{ fontSize: 13, fontWeight: 600, color: COLORS.text, marginBottom: 14, textTransform: "uppercase", letterSpacing: 0.5 }}>Foderplan</div>
            {[
              { label: "Hö", value: 65, unit: "%", color: COLORS.green },
              { label: "Kraftfoder", value: 25, unit: "%", color: COLORS.orange },
              { label: "Tillskott", value: 10, unit: "%", color: COLORS.blue },
            ].map((f, i) => (
              <div key={i} style={{ marginBottom: 10 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 4 }}>
                  <span style={{ color: COLORS.textDim }}>{f.label}</span>
                  <span style={{ color: COLORS.text, fontWeight: 500 }}>{f.value}{f.unit}</span>
                </div>
                <div style={{ height: 6, background: COLORS.border, borderRadius: 3 }}>
                  <div style={{ width: `${f.value}%`, height: "100%", background: f.color, borderRadius: 3 }} />
                </div>
              </div>
            ))}
            <div style={{ marginTop: 12, padding: 10, background: COLORS.bgHover, borderRadius: 8, fontSize: 12, color: COLORS.textDim }}>
              Foderkostnad: <span style={{ color: COLORS.text, fontWeight: 500 }}>1 200 kr/v</span> • Vikt: <span style={{ color: h.weight > 495 ? COLORS.orange : COLORS.green, fontWeight: 500 }}>{h.weight} kg</span>
            </div>
          </Card>
          <Card>
            <div style={{ fontSize: 13, fontWeight: 600, color: COLORS.text, marginBottom: 14, textTransform: "uppercase", letterSpacing: 0.5 }}>Hälsologg</div>
            {[
              { date: "Vecka 34", event: "Hovvård & omskoning", status: "ok" },
              { date: "Vecka 33", event: "Veterinärkontroll — allt bra", status: "ok" },
              { date: "Vecka 31", event: "Lindrigt halt — 3 dagars vila", status: "warn" },
              { date: "Vecka 28", event: "Hovvård & omskoning", status: "ok" },
            ].map((l, i) => (
              <div key={i} style={{ display: "flex", gap: 10, padding: "8px 0", borderBottom: i < 3 ? `1px solid ${COLORS.border}20` : "none", alignItems: "center" }}>
                <div style={{ width: 8, height: 8, borderRadius: 4, background: l.status === "ok" ? COLORS.green : COLORS.orange, flexShrink: 0 }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 12, color: COLORS.text }}>{l.event}</div>
                  <div style={{ fontSize: 10.5, color: COLORS.textMuted }}>{l.date}</div>
                </div>
              </div>
            ))}
            <button style={{ marginTop: 12, width: "100%", padding: "8px", borderRadius: 6, background: COLORS.bgHover, border: `1px solid ${COLORS.border}`, color: COLORS.textDim, fontSize: 12, cursor: "pointer" }}>
              🩺 Boka veterinärkontroll — 2 500 kr
            </button>
          </Card>
        </div>
      )}

      {tab === "history" && (
        <Card>
          <div style={{ fontSize: 13, fontWeight: 600, color: COLORS.text, marginBottom: 14, textTransform: "uppercase", letterSpacing: 0.5 }}>Senaste lopp</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {[
              { date: "2024-V33", race: "Silverdivisionen Omg 8", dist: "2140m", pos: 2, time: "1.13,4", driver: "Erik Lindblom", prize: 30000 },
              { date: "2024-V31", race: "Silverdivisionen Omg 7", dist: "2140m", pos: 1, time: "1.12,8", driver: "Erik Lindblom", prize: 60000 },
              { date: "2024-V29", race: "Ungloppserie Final", dist: "1640m", pos: 4, time: "1.14,1", driver: "Anna Svensson", prize: 10000 },
              { date: "2024-V27", race: "Silverdivisionen Omg 6", dist: "2140m", pos: 1, time: "1.13,0", driver: "Erik Lindblom", prize: 60000 },
              { date: "2024-V25", race: "Silverdivisionen Omg 5", dist: "2640m", pos: 3, time: "1.14,6", driver: "Erik Lindblom", prize: 18000 },
            ].map((r, i) => (
              <div key={i} style={{
                display: "grid", gridTemplateColumns: "80px 1fr 70px 70px 120px 90px", gap: 12, padding: "10px 8px",
                borderRadius: 6, alignItems: "center",
                background: r.pos === 1 ? COLORS.gold + "08" : "transparent",
              }}>
                <span style={{ fontSize: 11, color: COLORS.textMuted }}>{r.date}</span>
                <span style={{ fontSize: 12, color: COLORS.text, fontWeight: 500 }}>{r.race}</span>
                <span style={{ fontSize: 12, color: COLORS.textDim }}>{r.dist}</span>
                <span style={{
                  fontSize: 14, fontWeight: 700,
                  color: r.pos === 1 ? COLORS.gold : r.pos <= 3 ? COLORS.green : COLORS.textDim,
                  fontFamily: "'DM Serif Display', Georgia, serif"
                }}>{r.pos}:a</span>
                <span style={{ fontSize: 12, color: COLORS.textDim }}>{r.driver} • {r.time}</span>
                <span style={{ fontSize: 12, color: COLORS.gold, fontWeight: 500, textAlign: "right" }}>+{(r.prize / 1000).toFixed(0)}k kr</span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

function RaceScreen() {
  const [livePhase, setLivePhase] = useState(0);
  const [running, setRunning] = useState(false);
  const intervalRef = useRef(null);

  const liveCommentary = [
    { dist: "START", text: "Voltstart — alla kommer iväg! Bliansen (3) tar ledningen direkt. Expressen (7) hamnar i andraläge." },
    { dist: "500m", text: "500m passerat: Bliansen (3) leder med en halv längd. Expressen (7) sitter i rygg. Guldpilen (5) tredjespår ut." },
    { dist: "1000m", text: "Halvvägs: Bliansen håller tempot. Nattsvansen (4) pressar framåt i tredjespår. Expressen sparar krafter." },
    { dist: "1500m", text: "Sista kurvan: Guldpilen (5) angriper tre bred! Bliansen tröttnar? Expressen bereder sig för spurt!" },
    { dist: "1800m", text: "300 kvar: FULL ATTACK! Expressen (7) drar ut i tredjespår! Guldpilen (5) och Bliansen (3) i kamp!" },
    { dist: "2000m", text: "200 kvar: Expressen (7) flyger förbi! Bliansen ger sig inte! Nattsvansen (4) — GALOPPERAR vid 150m kvar!" },
    { dist: "MÅL", text: "🏆 EXPRESSEN (7) vinner med en halv längd! 2:a Bliansen (3), 3:a Guldpilen (5). Tid: 1.12,4 auto." },
  ];

  const startRace = () => {
    setRunning(true);
    setLivePhase(0);
    intervalRef.current = setInterval(() => {
      setLivePhase(prev => {
        if (prev >= liveCommentary.length - 1) {
          clearInterval(intervalRef.current);
          setRunning(false);
          return prev;
        }
        return prev + 1;
      });
    }, 2200);
  };

  useEffect(() => () => clearInterval(intervalRef.current), []);

  const positions = [
    [3, 7, 5, 4, 1],
    [3, 7, 5, 1, 4],
    [3, 7, 4, 5, 1],
    [3, 5, 7, 4, 1],
    [7, 3, 5, 4, 1],
    [7, 3, 5, 4, 1],
    [7, 3, 5, 1, 4],
  ];
  const horseColors = { 1: "#EF4444", 3: COLORS.gold, 4: COLORS.purple, 5: COLORS.blue, 7: COLORS.green };
  const horseNames = { 1: "Dalero", 3: "Bliansen", 4: "Nattsvansen", 5: "Guldpilen", 7: "Expressen" };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div>
          <div style={{ fontSize: 11, color: COLORS.textMuted, textTransform: "uppercase", letterSpacing: 1.2 }}>Loppdag — Onsdag</div>
          <div style={{ fontSize: 18, fontWeight: 700, color: COLORS.text, fontFamily: "'DM Serif Display', Georgia, serif" }}>V75-1 Silverdivisionen • 2140m Volt</div>
        </div>
        {!running && livePhase === 0 && (
          <button onClick={startRace} style={{
            padding: "10px 24px", borderRadius: 8, background: `linear-gradient(135deg, ${COLORS.gold}, ${COLORS.goldDim})`,
            color: COLORS.bg, fontWeight: 700, fontSize: 13, border: "none", cursor: "pointer", letterSpacing: 0.5
          }}>▶ Simulera lopp</button>
        )}
        {running && <Badge color={COLORS.red}>● LIVE</Badge>}
        {!running && livePhase > 0 && <Badge color={COLORS.green}>✓ AVSLUTAT</Badge>}
      </div>

      {/* Track visualization */}
      <Card style={{ marginBottom: 16, padding: 20 }}>
        <div style={{ fontSize: 11, color: COLORS.textMuted, textTransform: "uppercase", letterSpacing: 1, marginBottom: 12 }}>Positioner</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {(positions[livePhase] || positions[0]).map((num, pos) => {
            const color = horseColors[num];
            const name = horseNames[num];
            const pct = livePhase === 0 ? 5 : Math.max(10, 95 - pos * (8 + Math.random() * 4));
            return (
              <div key={num} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{ width: 24, fontSize: 12, color: COLORS.textMuted, textAlign: "center", fontWeight: 600 }}>{pos + 1}</div>
                <div style={{ flex: 1, height: 28, background: COLORS.bgHover, borderRadius: 6, position: "relative", overflow: "hidden" }}>
                  <div style={{
                    position: "absolute", left: 0, top: 0, height: "100%",
                    width: `${pct}%`, background: `linear-gradient(90deg, ${color}30, ${color}60)`,
                    borderRadius: 6, transition: "width 0.8s ease", display: "flex", alignItems: "center", justifyContent: "flex-end", paddingRight: 8
                  }}>
                    <span style={{ fontSize: 11, fontWeight: 700, color, textShadow: `0 0 8px ${color}80` }}>🐴</span>
                  </div>
                  <div style={{ position: "absolute", left: 8, top: "50%", transform: "translateY(-50%)", fontSize: 11, fontWeight: 600, color: COLORS.text, zIndex: 1 }}>
                    ({num}) {name}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
        <div style={{ marginTop: 12, display: "flex", justifyContent: "space-between", fontSize: 10, color: COLORS.textMuted }}>
          <span>START</span><span>500m</span><span>1000m</span><span>1500m</span><span>MÅL</span>
        </div>
      </Card>

      {/* Live commentary */}
      <Card>
        <div style={{ fontSize: 13, fontWeight: 600, color: COLORS.text, marginBottom: 12, textTransform: "uppercase", letterSpacing: 0.5 }}>Referat</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {liveCommentary.slice(0, livePhase + 1).map((c, i) => (
            <div key={i} style={{
              display: "flex", gap: 12, padding: "10px 12px", borderRadius: 8,
              background: i === livePhase ? COLORS.gold + "08" : "transparent",
              border: i === livePhase ? `1px solid ${COLORS.gold}20` : "1px solid transparent",
              animation: i === livePhase ? "fadeIn 0.5s ease" : "none"
            }}>
              <span style={{
                fontSize: 11, fontWeight: 700, color: i === livePhase ? COLORS.gold : COLORS.textMuted,
                minWidth: 48, fontVariantNumeric: "tabular-nums"
              }}>{c.dist}</span>
              <span style={{ fontSize: 12.5, color: i === livePhase ? COLORS.text : COLORS.textDim, lineHeight: 1.5 }}>{c.text}</span>
            </div>
          ))}
        </div>
      </Card>

      {!running && livePhase >= liveCommentary.length - 1 && (
        <Card style={{ marginTop: 16 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: COLORS.text, marginBottom: 12, textTransform: "uppercase", letterSpacing: 0.5 }}>Resultat</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 12 }}>
            {[
              { pos: "1:a", name: "Expressen", time: "1.12,4", prize: "60 000 kr", color: COLORS.gold },
              { pos: "2:a", name: "Bliansen", time: "1.12,8", prize: "30 000 kr", color: "#C0C0C0" },
              { pos: "3:a", name: "Guldpilen", time: "1.13,1", prize: "18 000 kr", color: "#CD7F32" },
              { pos: "4:a", name: "Dalero", time: "1.13,6", prize: "9 000 kr", color: COLORS.textMuted },
              { pos: "DQ", name: "Nattsvansen", time: "galp.", prize: "—", color: COLORS.red },
            ].map((r, i) => (
              <div key={i} style={{ textAlign: "center", padding: 12, background: i === 0 ? COLORS.gold + "10" : COLORS.bgHover, borderRadius: 8, border: i === 0 ? `1px solid ${COLORS.gold}30` : `1px solid ${COLORS.border}` }}>
                <div style={{ fontSize: 18, fontWeight: 700, color: r.color, fontFamily: "'DM Serif Display', Georgia, serif" }}>{r.pos}</div>
                <div style={{ fontSize: 13, fontWeight: 600, color: COLORS.text, marginTop: 4 }}>{r.name}</div>
                <div style={{ fontSize: 11, color: COLORS.textDim, marginTop: 2 }}>{r.time}</div>
                <div style={{ fontSize: 12, color: COLORS.gold, fontWeight: 500, marginTop: 4 }}>{r.prize}</div>
              </div>
            ))}
          </div>
        </Card>
      )}

      <style>{`@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }`}</style>
    </div>
  );
}

function TransferScreen() {
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div>
          <div style={{ fontSize: 11, color: COLORS.textMuted, textTransform: "uppercase", letterSpacing: 1.2 }}>Transfermarknad</div>
          <div style={{ fontSize: 18, fontWeight: 700, color: COLORS.text, fontFamily: "'DM Serif Display', Georgia, serif" }}>Aktiva auktioner</div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button style={{ padding: "6px 14px", borderRadius: 6, border: `1px solid ${COLORS.gold}`, background: COLORS.gold + "15", color: COLORS.gold, fontSize: 12, cursor: "pointer", fontWeight: 500 }}>Auktioner</button>
          <button style={{ padding: "6px 14px", borderRadius: 6, border: `1px solid ${COLORS.border}`, background: "transparent", color: COLORS.textDim, fontSize: 12, cursor: "pointer" }}>Leasing</button>
          <button style={{ padding: "6px 14px", borderRadius: 6, border: `1px solid ${COLORS.border}`, background: "transparent", color: COLORS.textDim, fontSize: 12, cursor: "pointer" }}>Claiming</button>
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {[
          { name: "Stormkungen", age: 4, speed: 80, endurance: 75, bid: 182000, bids: 7, ends: "4t 22m", seller: "Bergströms Stall", highlight: true },
          { name: "Blixtra", age: 3, speed: 72, endurance: 60, bid: 95000, bids: 3, ends: "1d 8t", seller: "Lövbacken Racing", highlight: false },
          { name: "Järnmannen", age: 8, speed: 70, endurance: 88, bid: 45000, bids: 1, ends: "2d 14t", seller: "Sundsvalls Stall", highlight: false },
          { name: "Solglansen", age: 5, speed: 77, endurance: 72, bid: 155000, bids: 5, ends: "12t 30m", seller: "Elittraven AB", highlight: false },
          { name: "Vinternatt", age: 6, speed: 74, endurance: 83, bid: 120000, bids: 4, ends: "22t 15m", seller: "Norrbottens Trav", highlight: false },
        ].map((h, i) => (
          <Card key={i} hover style={{
            padding: 14,
            border: h.highlight ? `1px solid ${COLORS.gold}40` : undefined,
            background: h.highlight ? COLORS.gold + "06" : undefined
          }}>
            <div style={{ display: "grid", gridTemplateColumns: "180px 1fr 160px 120px", alignItems: "center", gap: 16 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{ width: 40, height: 40, borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", background: COLORS.gold + "10", border: `1px solid ${COLORS.gold}20`, fontSize: 20 }}>🐴</div>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: COLORS.text }}>{h.name}</div>
                  <div style={{ fontSize: 11, color: COLORS.textMuted }}>{h.age} år • {h.seller}</div>
                </div>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                <StatBar value={h.speed} label="Snabbhet" color={COLORS.gold} small />
                <StatBar value={h.endurance} label="Uthållighet" color={COLORS.blue} small />
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 16, fontWeight: 700, color: COLORS.gold, fontFamily: "'DM Serif Display', Georgia, serif" }}>{h.bid.toLocaleString("sv-SE")} kr</div>
                <div style={{ fontSize: 11, color: COLORS.textMuted }}>{h.bids} bud • slutar om {h.ends}</div>
              </div>
              <div style={{ textAlign: "right" }}>
                <button style={{
                  padding: "8px 16px", borderRadius: 6,
                  background: h.highlight ? COLORS.gold : "transparent",
                  color: h.highlight ? COLORS.bg : COLORS.gold,
                  border: `1px solid ${COLORS.gold}`,
                  fontWeight: 600, fontSize: 12, cursor: "pointer"
                }}>Lägg bud</button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

// --- Main App ---
export default function TravManager() {
  const [screen, setScreen] = useState("dashboard");
  const [selectedHorse, setSelectedHorse] = useState(null);

  const navItems = [
    { id: "dashboard", label: "Kontor", icon: "📊" },
    { id: "stable", label: "Stall", icon: "🐴" },
    { id: "race", label: "Lopp", icon: "🏁" },
    { id: "transfer", label: "Transfer", icon: "🔄" },
    { id: "breeding", label: "Avel", icon: "🧬" },
    { id: "v75", label: "V75", icon: "🎰" },
  ];

  return (
    <div style={{ minHeight: "100vh", background: COLORS.bg, color: COLORS.text, fontFamily: "'Outfit', 'Segoe UI', system-ui, sans-serif" }}>
      <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=DM+Serif+Display&display=swap" rel="stylesheet" />

      {/* Top bar */}
      <div style={{
        height: 56, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 24px",
        borderBottom: `1px solid ${COLORS.border}`, background: COLORS.bgCard,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 22 }}>🏇</span>
          <span style={{ fontSize: 18, fontWeight: 700, fontFamily: "'DM Serif Display', Georgia, serif", color: COLORS.gold, letterSpacing: 0.5 }}>TravManager</span>
          <span style={{ fontSize: 10, color: COLORS.textMuted, background: COLORS.bgHover, padding: "2px 6px", borderRadius: 4, marginLeft: 4 }}>BETA</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{ fontSize: 12, color: COLORS.textDim }}>Vecka 35 • Säsong 2024</div>
          <div style={{ width: 1, height: 20, background: COLORS.border }} />
          <div style={{ fontSize: 13, color: COLORS.gold, fontWeight: 600 }}>💰 {FINANCES.balance.toLocaleString("sv-SE")} kr</div>
          <div style={{
            width: 32, height: 32, borderRadius: 8, background: `linear-gradient(135deg, ${COLORS.gold}30, ${COLORS.gold}10)`,
            display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14,
            border: `1px solid ${COLORS.gold}25`, cursor: "pointer"
          }}>👤</div>
        </div>
      </div>

      <div style={{ display: "flex" }}>
        {/* Sidebar */}
        <div style={{ width: 180, borderRight: `1px solid ${COLORS.border}`, background: COLORS.bgCard, padding: "12px 0", minHeight: "calc(100vh - 56px)" }}>
          {navItems.map((item) => (
            <div
              key={item.id}
              onClick={() => { setScreen(item.id); setSelectedHorse(null); }}
              style={{
                display: "flex", alignItems: "center", gap: 10, padding: "10px 20px", cursor: "pointer",
                background: screen === item.id ? COLORS.bgActive : "transparent",
                borderLeft: screen === item.id ? `3px solid ${COLORS.gold}` : "3px solid transparent",
                color: screen === item.id ? COLORS.gold : COLORS.textDim,
                transition: "all 0.15s", fontSize: 13, fontWeight: screen === item.id ? 600 : 400,
              }}
            >
              <span style={{ fontSize: 16 }}>{item.icon}</span>
              {item.label}
            </div>
          ))}

          {/* Drivers in sidebar */}
          <div style={{ margin: "20px 16px 8px", borderTop: `1px solid ${COLORS.border}`, paddingTop: 16 }}>
            <div style={{ fontSize: 10, color: COLORS.textMuted, textTransform: "uppercase", letterSpacing: 1.2, marginBottom: 10 }}>Kuskar</div>
            {DRIVERS.map((d) => (
              <div key={d.id} style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 4px" }}>
                <div style={{ width: 24, height: 24, borderRadius: 6, background: COLORS.bgHover, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12 }}>👤</div>
                <div>
                  <div style={{ fontSize: 11.5, color: COLORS.text, fontWeight: 500 }}>{d.name}</div>
                  <div style={{ fontSize: 10, color: COLORS.textMuted }}>{d.salary.toLocaleString("sv-SE")} kr/m</div>
                </div>
              </div>
            ))}
          </div>

          {/* Facility */}
          <div style={{ margin: "12px 16px 0" }}>
            <div style={{ fontSize: 10, color: COLORS.textMuted, textTransform: "uppercase", letterSpacing: 1.2, marginBottom: 10 }}>Anläggning</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
              {[
                { icon: "🏠", label: "Stall", active: true },
                { icon: "🛤️", label: "Bana", active: true },
                { icon: "🚀", label: "Start", active: false },
                { icon: "🏊", label: "Pool", active: false },
                { icon: "🩺", label: "Vet", active: false },
              ].map((f, i) => (
                <div key={i} style={{
                  fontSize: 16, padding: 4, borderRadius: 4, opacity: f.active ? 1 : 0.3,
                  background: f.active ? COLORS.bgHover : "transparent",
                  cursor: "pointer", title: f.label
                }}>{f.icon}</div>
              ))}
            </div>
          </div>
        </div>

        {/* Main content */}
        <div style={{ flex: 1, padding: 24, maxWidth: 960, overflowY: "auto", maxHeight: "calc(100vh - 56px)" }}>
          {screen === "dashboard" && <DashboardScreen onNavigate={setScreen} />}
          {screen === "stable" && !selectedHorse && <StableScreen onSelectHorse={setSelectedHorse} />}
          {screen === "stable" && selectedHorse && <HorseDetailScreen horse={selectedHorse} onBack={() => setSelectedHorse(null)} />}
          {screen === "race" && <RaceScreen />}
          {screen === "transfer" && <TransferScreen />}
          {screen === "breeding" && (
            <Card style={{ textAlign: "center", padding: 48 }}>
              <span style={{ fontSize: 48 }}>🧬</span>
              <div style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, marginTop: 16, fontFamily: "'DM Serif Display', Georgia, serif" }}>Avelsanläggning</div>
              <div style={{ fontSize: 13, color: COLORS.textDim, marginTop: 8 }}>Kräver uppgradering — 85 000 kr</div>
              <button style={{ marginTop: 16, padding: "10px 24px", borderRadius: 8, background: COLORS.gold + "20", border: `1px solid ${COLORS.gold}40`, color: COLORS.gold, fontWeight: 600, fontSize: 13, cursor: "pointer" }}>Bygg avelsanläggning</button>
            </Card>
          )}
          {screen === "v75" && (
            <Card style={{ textAlign: "center", padding: 48 }}>
              <span style={{ fontSize: 48 }}>🎰</span>
              <div style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, marginTop: 16, fontFamily: "'DM Serif Display', Georgia, serif" }}>V75-tippning</div>
              <div style={{ fontSize: 13, color: COLORS.textDim, marginTop: 8, maxWidth: 400, margin: "8px auto 0" }}>Tippa på lördagens lopp mot andra managers. Lottdragning baserad på alla spelares hästar!</div>
              <div style={{ fontSize: 12, color: COLORS.textMuted, marginTop: 12 }}>Nästa omgång: Lördag 15:00</div>
              <button style={{ marginTop: 16, padding: "10px 24px", borderRadius: 8, background: COLORS.gold, border: "none", color: COLORS.bg, fontWeight: 600, fontSize: 13, cursor: "pointer" }}>Visa kupong</button>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
