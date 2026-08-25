"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

// ─── Typer ───────────────────────────────────────────────────────
interface Position {
  id: string;
  n: string;    // hästnamn
  pos: number;  // position i meter
  e: number;    // energi
  spd: number;  // fart
  g: boolean;   // galopperar
  dq: boolean;  // diskad
  r: number;    // placering just nu
  ln?: number;  // spår: 0 inner, 1 mitt, 2 ytter
  post?: number; // spårnummer i programmet
  box?: boolean; // instängd
}

interface Snapshot {
  d: number;
  p: Position[];
}

interface Finisher {
  position: number;
  horse_name: string;
  horse_id: string;
  is_npc: boolean;
  km_time: string;
  prize_money: number;
  stable_color?: string;
}

interface RaceEventItem {
  type: string;
  horse: string;
  text: string;
  distance: number;
}

interface CommentaryLine {
  d: number;
  phase: string;
  text: string;
  horse_id: string | null;
  tone: string;
}

interface RaceReplayProps {
  snapshots: Snapshot[];
  finishers: Finisher[];
  distance: number;
  raceName: string;
  events?: RaceEventItem[];
  commentary?: CommentaryLine[];
  onSkipToResult?: () => void;
}

// ─── Konstanter ──────────────────────────────────────────────────
const CANVAS_W = 820;
const CANVAS_H = 430;
const CENTER_X = CANVAS_W / 2;
const CENTER_Y = CANVAS_H / 2;
const RX_OUTER = 288;
const RY_OUTER = 148;
const RX_INNER = 202;
const RY_INNER = 88;

const HORSE_COLORS = [
  "#E63946", "#457B9D", "#2A9D8F", "#E9C46A",
  "#F4A261", "#7B8CDE", "#A8DADC", "#9C6ADE",
  "#B5838D", "#FF8FA3", "#6A994E", "#BC6C25",
];

const SPEED_OPTIONS = [1, 2, 4];
const FRAME_MS = 620;

// Motorns `pos` är en abstrakt progresspoäng — bara SKILLNADERNA mellan
// hästar är riktiga meter (motorn räknar självt tid ur `gap × 0.075 s/m`).
// Fältets faktiska position i banan är i stället snapshotens `d`.
// Ett fält som ligger inom 20 m blir 0,9 % av ovalen, alltså osynligt,
// så avstånden förstoras visuellt. Positionslistan visar sanna meter.
const GAP_SCALE = 8;

const PHASE_LABELS: Record<string, string> = {
  opening: "Öppning",
  middle: "Mittfas",
  curve: "Sista kurvan",
  stretch: "Upploppet",
  finish: "Mållinjen",
  summary: "Efter loppet",
};

const EVENT_STYLE: Record<string, { label: string; color: string }> = {
  gallop_minor: { label: "Felsteg", color: "#FB923C" },
  gallop_major: { label: "Galopp", color: "#EF4444" },
  gallop_dq: { label: "Diskad", color: "#EF4444" },
  hidden_gear: { label: "Extra växel", color: "#4ADE80" },
  instinct_surge: { label: "Tävlingsinstinkt", color: "#F0C864" },
  driver_tactical_move: { label: "Kuskdrag", color: "#7B8CDE" },
};

// ─── Komponent ───────────────────────────────────────────────────
export function RaceReplay({
  snapshots, finishers, distance, raceName, events = [], commentary = [],
}: RaceReplayProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);
  const lastTimeRef = useRef<number>(0);
  const feedRef = useRef<HTMLDivElement>(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [fraction, setFraction] = useState(0);
  const [isFinished, setIsFinished] = useState(false);
  const [followMine, setFollowMine] = useState(true);

  const totalFrames = snapshots.length;

  const playerHorseIds = useMemo(
    () => new Set(finishers.filter((f) => !f.is_npc).map((f) => f.horse_id)),
    [finishers]
  );

  // Färg och spårnummer per häst — stabilt över hela loppet.
  // Spelarstall med egen stallfärg (kosmetik) använder den i banan.
  const horseMeta = useMemo(() => {
    const map = new Map<string, { color: string; post: number }>();
    const stableColors = new Map<string, string>();
    finishers.forEach((f: any) => {
      if (f.stable_color) stableColors.set(f.horse_id, f.stable_color);
    });
    if (snapshots.length > 0) {
      const first = [...snapshots[0].p].sort((a, b) => (a.post ?? a.r) - (b.post ?? b.r));
      first.forEach((p, i) => {
        map.set(p.id, {
          color: stableColors.get(p.id) || HORSE_COLORS[i % HORSE_COLORS.length],
          post: p.post || i + 1,
        });
      });
    }
    return map;
  }, [snapshots, finishers]);

  const currentSnap = snapshots[currentFrame];
  const currentMeters = currentSnap
    ? currentSnap.d + (snapshots[currentFrame + 1] ? (snapshots[currentFrame + 1].d - currentSnap.d) * fraction : 0)
    : 0;

  // Kommentar fram till nuvarande position
  const visibleCommentary = useMemo(
    () => commentary.filter((l) => l.d <= currentMeters + 1),
    [commentary, currentMeters]
  );

  // Aktiv händelse-banner: händelser inom de senaste 120 metrarna
  const activeEvents = useMemo(
    () => events.filter(
      (e) => EVENT_STYLE[e.type] && e.distance <= currentMeters && e.distance > currentMeters - 120
    ),
    [events, currentMeters]
  );
  const flaggedHorses = useMemo(
    () => new Set(activeEvents.map((e) => e.horse)),
    [activeEvents]
  );

  useEffect(() => {
    if (feedRef.current) feedRef.current.scrollTop = feedRef.current.scrollHeight;
  }, [visibleCommentary.length]);

  // ─── Ritning ───────────────────────────────────────────────
  const draw = useCallback(
    (frameIdx: number, frac: number) => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      const current = snapshots[frameIdx];
      const next = snapshots[Math.min(frameIdx + 1, totalFrames - 1)];
      if (!current) return;

      ctx.clearRect(0, 0, CANVAS_W, CANVAS_H);
      ctx.fillStyle = "#0B0E14";
      ctx.fillRect(0, 0, CANVAS_W, CANVAS_H);

      // Fältets position i banan (interpolerad mellan snapshots)
      const fieldMeters = current.d + (next.d - current.d) * frac;

      // Ledarens progresspoäng, interpolerad — referens för luckorna
      const leadNow = Math.max(...current.p.map((p) => p.pos));
      const leadNext = Math.max(...next.p.map((p) => p.pos));
      const leadRef = leadNow + (leadNext - leadNow) * frac;

      type Drawn = Position & { m: number; gap: number; angle: number; lane: number };
      const drawn: Drawn[] = current.p.map((h) => {
        const nh = next.p.find((p) => p.id === h.id);
        const prog = h.pos + ((nh ? nh.pos : h.pos) - h.pos) * frac;
        const gap = leadRef - prog;                       // sanna meter efter ledaren
        const m = Math.max(0, fieldMeters - gap * GAP_SCALE);
        return {
          ...h,
          m,
          gap,
          angle: (m / distance) * Math.PI * 2 - Math.PI / 2,
          lane: h.ln ?? 1,
        };
      });

      // Kamera: följ spelarens häst eller täten
      let focus = drawn.find((h) => playerHorseIds.has(h.id) && !h.dq);
      if (!followMine || !focus) {
        focus = drawn.slice().sort((a, b) => a.r - b.r)[0];
      }
      const zoom = followMine ? 1.3 : 1.12;
      ctx.save();
      if (focus) {
        const fx = CENTER_X + RX_OUTER * Math.cos(focus.angle);
        const fy = CENTER_Y + RY_OUTER * Math.sin(focus.angle);
        ctx.translate(CENTER_X, CENTER_Y);
        ctx.scale(zoom, zoom);
        ctx.translate(-CENTER_X - (fx - CENTER_X) * 0.26, -CENTER_Y - (fy - CENTER_Y) * 0.26);
      }

      drawTrack(ctx, distance);

      // Anti-överlapp: hästar i samma spår som ligger nära varandra fjädras isär
      const byLane = new Map<number, Drawn[]>();
      drawn.forEach((h) => {
        const arr = byLane.get(h.lane) || [];
        arr.push(h);
        byLane.set(h.lane, arr);
      });
      const laneNudge = new Map<string, number>();
      byLane.forEach((group) => {
        const sorted = group.slice().sort((a, b) => b.m - a.m);
        sorted.forEach((h, i) => {
          const tooClose = sorted.filter((o, j) => j < i && Math.abs(o.m - h.m) < 26).length;
          laneNudge.set(h.id, tooClose * 11);
        });
      });

      // Rita bakifrån och fram så att ledaren hamnar överst
      const ordered = drawn.slice().sort((a, b) => b.r - a.r);
      for (const h of ordered) {
        const laneBase = [0.16, 0.5, 0.84][h.lane] ?? 0.5;
        const spanX = RX_OUTER - RX_INNER;
        const spanY = RY_OUTER - RY_INNER;
        const nudge = (laneNudge.get(h.id) || 0) / Math.max(1, spanX);
        const t = Math.min(0.94, laneBase + nudge);

        const rx = RX_INNER + spanX * t;
        const ry = RY_INNER + spanY * t;
        const x = CENTER_X + rx * Math.cos(h.angle);
        const y = CENTER_Y + ry * Math.sin(h.angle);

        const meta = horseMeta.get(h.id);
        const color = meta?.color || "#888";
        const isPlayer = playerHorseIds.has(h.id);
        const flagged = flaggedHorses.has(h.n);

        drawSulky(ctx, x, y, h.angle, {
          color,
          post: meta?.post || h.r,
          isPlayer,
          galloping: h.g,
          dq: h.dq,
          flagged,
        });
      }

      ctx.restore();

      // HUD
      const progress = Math.min(1, fieldMeters / distance);
      ctx.fillStyle = "rgba(11,14,20,0.85)";
      ctx.fillRect(0, 0, CANVAS_W, 30);
      ctx.fillStyle = "#9AA0AE";
      ctx.font = "12px Inter, sans-serif";
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      ctx.fillText(`${Math.round(fieldMeters)} m av ${distance} m`, 14, 15);
      ctx.fillStyle = "#4B5563";
      ctx.font = "10px Inter, sans-serif";
      ctx.fillText(`avstånd förstorade ×${GAP_SCALE}`, 150, 15);

      const remaining = Math.max(0, distance - fieldMeters);
      if (remaining <= 400 && remaining > 0) {
        ctx.fillStyle = "#F0C864";
        ctx.font = "bold 12px Inter, sans-serif";
        ctx.textAlign = "right";
        ctx.fillText(`UPPLOPP — ${Math.round(remaining)} m kvar`, CANVAS_W - 14, 15);
      }

      const barY = CANVAS_H - 5;
      ctx.fillStyle = "#252A3A";
      ctx.fillRect(0, barY, CANVAS_W, 5);
      ctx.fillStyle = "#D4A853";
      ctx.fillRect(0, barY, CANVAS_W * progress, 5);
    },
    [snapshots, totalFrames, distance, playerHorseIds, horseMeta, followMine, flaggedHorses]
  );

  function drawTrack(ctx: CanvasRenderingContext2D, dist: number) {
    ctx.beginPath();
    ctx.ellipse(CENTER_X, CENTER_Y, RX_OUTER, RY_OUTER, 0, 0, Math.PI * 2);
    ctx.fillStyle = "#3E3125";
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(CENTER_X, CENTER_Y, RX_INNER, RY_INNER, 0, 0, Math.PI * 2);
    ctx.fillStyle = "#16261A";
    ctx.fill();

    // Spårlinjer
    ctx.strokeStyle = "rgba(255,255,255,0.06)";
    ctx.lineWidth = 1;
    [0.33, 0.66].forEach((t) => {
      ctx.beginPath();
      ctx.ellipse(
        CENTER_X, CENTER_Y,
        RX_INNER + (RX_OUTER - RX_INNER) * t,
        RY_INNER + (RY_OUTER - RY_INNER) * t,
        0, 0, Math.PI * 2
      );
      ctx.stroke();
    });

    ctx.strokeStyle = "#5C4B3A";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.ellipse(CENTER_X, CENTER_Y, RX_OUTER, RY_OUTER, 0, 0, Math.PI * 2);
    ctx.stroke();

    // Upploppszon (sista 400 m)
    const a1 = ((dist - 400) / dist) * Math.PI * 2 - Math.PI / 2;
    const a2 = Math.PI * 2 - Math.PI / 2;
    ctx.globalAlpha = 0.16;
    ctx.fillStyle = "#F0C864";
    ctx.beginPath();
    ctx.ellipse(CENTER_X, CENTER_Y, RX_OUTER, RY_OUTER, 0, a1, a2);
    for (let i = 30; i >= 0; i--) {
      const a = a1 + (a2 - a1) * (i / 30);
      ctx.lineTo(CENTER_X + RX_INNER * Math.cos(a), CENTER_Y + RY_INNER * Math.sin(a));
    }
    ctx.closePath();
    ctx.fill();
    ctx.globalAlpha = 1;

    // Mållinje
    const fa = -Math.PI / 2;
    ctx.strokeStyle = "#FFFFFF";
    ctx.lineWidth = 3;
    ctx.setLineDash([5, 4]);
    ctx.beginPath();
    ctx.moveTo(CENTER_X + RX_INNER * Math.cos(fa), CENTER_Y + RY_INNER * Math.sin(fa));
    ctx.lineTo(CENTER_X + RX_OUTER * Math.cos(fa), CENTER_Y + RY_OUTER * Math.sin(fa));
    ctx.stroke();
    ctx.setLineDash([]);

    // Distansmarkeringar
    ctx.fillStyle = "#6B7280";
    ctx.font = "9px Inter, sans-serif";
    ctx.textAlign = "center";
    for (let dm = 500; dm < dist; dm += 500) {
      const a = (dm / dist) * Math.PI * 2 - Math.PI / 2;
      ctx.fillText(
        `${dm}`,
        CENTER_X + (RX_OUTER + 15) * Math.cos(a),
        CENTER_Y + (RY_OUTER + 15) * Math.sin(a) + 3
      );
    }
  }

  function drawSulky(
    ctx: CanvasRenderingContext2D,
    x: number, y: number, angle: number,
    o: { color: string; post: number; isPlayer: boolean; galloping: boolean; dq: boolean; flagged: boolean }
  ) {
    const w = o.isPlayer ? 26 : 23;
    const h = o.isPlayer ? 15 : 13;

    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(angle + Math.PI / 2);

    if (o.flagged || o.galloping) {
      ctx.beginPath();
      ctx.arc(0, 0, w * 0.85, 0, Math.PI * 2);
      ctx.strokeStyle = o.galloping ? "#EF4444" : "#F0C864";
      ctx.lineWidth = 2.5;
      ctx.globalAlpha = 0.75;
      ctx.stroke();
      ctx.globalAlpha = 1;
    }

    // Sulkyhjul
    ctx.strokeStyle = o.dq ? "#4B5563" : "rgba(0,0,0,0.55)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(-w * 0.42, h * 0.5, 3.4, 0, Math.PI * 2);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(w * 0.42, h * 0.5, 3.4, 0, Math.PI * 2);
    ctx.stroke();

    // Kropp
    const r = 4;
    ctx.beginPath();
    ctx.moveTo(-w / 2 + r, -h / 2);
    ctx.arcTo(w / 2, -h / 2, w / 2, h / 2, r);
    ctx.arcTo(w / 2, h / 2, -w / 2, h / 2, r);
    ctx.arcTo(-w / 2, h / 2, -w / 2, -h / 2, r);
    ctx.arcTo(-w / 2, -h / 2, w / 2, -h / 2, r);
    ctx.closePath();
    ctx.fillStyle = o.dq ? "#374151" : o.color;
    ctx.fill();
    ctx.strokeStyle = o.isPlayer ? "#F0C864" : "rgba(0,0,0,0.5)";
    ctx.lineWidth = o.isPlayer ? 2.2 : 1;
    ctx.stroke();

    // Spårnummer
    ctx.rotate(-(angle + Math.PI / 2));
    ctx.fillStyle = o.dq ? "#9CA3AF" : "#0B0E14";
    ctx.font = `bold ${o.isPlayer ? 12 : 10}px Inter, sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(o.dq ? "✕" : String(o.post), 0, 0);
    ctx.restore();
  }

  // ─── Uppspelning ───────────────────────────────────────────
  useEffect(() => {
    if (!isPlaying || totalFrames < 2) return;
    const animate = (time: number) => {
      if (lastTimeRef.current === 0) lastTimeRef.current = time;
      const dt = time - lastTimeRef.current;
      lastTimeRef.current = time;
      setFraction((prev) => {
        const nextVal = prev + (dt / FRAME_MS) * speed;
        if (nextVal >= 1) {
          const overflow = Math.floor(nextVal);
          setCurrentFrame((pf) => {
            const nf = pf + overflow;
            if (nf >= totalFrames - 1) {
              setIsPlaying(false);
              setIsFinished(true);
              return totalFrames - 1;
            }
            return nf;
          });
          return nextVal - overflow;
        }
        return nextVal;
      });
      animRef.current = requestAnimationFrame(animate);
    };
    lastTimeRef.current = 0;
    animRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animRef.current);
  }, [isPlaying, speed, totalFrames]);

  useEffect(() => { draw(currentFrame, fraction); }, [currentFrame, fraction, draw]);

  const handlePlayPause = () => {
    if (isFinished) {
      setCurrentFrame(0); setFraction(0); setIsFinished(false); setIsPlaying(true);
    } else setIsPlaying(!isPlaying);
  };

  const skipToResult = () => {
    setIsPlaying(false);
    setCurrentFrame(totalFrames - 1);
    setFraction(0);
    setIsFinished(true);
  };

  const handleSeek = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    setCurrentFrame(Math.floor(pct * (totalFrames - 1)));
    setFraction(0);
    setIsFinished(false);
  };

  const ranked = currentSnap ? [...currentSnap.p].sort((a, b) => a.r - b.r) : [];
  const leaderPos = ranked[0]?.pos || 0;

  if (!snapshots.length) return null;

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-1 lg:grid-cols-[220px_1fr] gap-3">
        {/* Positionslista */}
        <div className="bg-trav-card border border-trav-border rounded-xl p-2 space-y-1 order-2 lg:order-1">
          <div className="section-label px-1 pb-1">Position</div>
          {ranked.map((h) => {
            const meta = horseMeta.get(h.id);
            const isPlayer = playerHorseIds.has(h.id);
            const gap = leaderPos - h.pos;
            return (
              <div
                key={h.id}
                className={`flex items-center gap-1.5 px-1.5 py-1 rounded-md text-[11px] ${
                  isPlayer ? "bg-trav-gold/10 border border-trav-gold/25" : "bg-trav-hover/40"
                }`}
              >
                <span className="w-4 font-bold text-gray-400 tabular-nums">{h.r}</span>
                <span
                  className="w-4 h-4 rounded-[3px] flex items-center justify-center text-[9px] font-bold shrink-0"
                  style={{ backgroundColor: meta?.color || "#888", color: "#0B0E14" }}
                >
                  {meta?.post ?? h.r}
                </span>
                <span className={`flex-1 truncate ${isPlayer ? "text-trav-gold font-semibold" : "text-gray-400"}`}>
                  {h.n}
                </span>
                <span className="tabular-nums text-[10px] w-11 text-right">
                  {h.dq ? (
                    <span className="text-red-400">DISK</span>
                  ) : h.g ? (
                    <span className="text-red-400">GALP</span>
                  ) : h.box ? (
                    <span className="text-orange-400">instängd</span>
                  ) : h.r === 1 ? (
                    <span className="text-trav-gold">tät</span>
                  ) : (
                    <span className="text-gray-600">{gap.toFixed(0)} m</span>
                  )}
                </span>
                <div className="w-8 h-1.5 bg-trav-border rounded-full overflow-hidden shrink-0">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${Math.max(0, Math.min(100, h.e))}%`,
                      backgroundColor: h.e > 50 ? "#4ADE80" : h.e > 25 ? "#E9C46A" : "#EF4444",
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>

        {/* Bana */}
        <div className="relative order-1 lg:order-2">
          <div className="bg-[#0B0E14] rounded-xl overflow-hidden border border-trav-border">
            <canvas ref={canvasRef} width={CANVAS_W} height={CANVAS_H} className="w-full block" />
          </div>

          {/* Händelsebanner */}
          <div className="absolute left-3 right-3 top-9 flex flex-col gap-1 pointer-events-none">
            {activeEvents.slice(-2).map((e, i) => {
              const st = EVENT_STYLE[e.type];
              return (
                <div
                  key={`${e.distance}-${e.horse}-${i}`}
                  className="self-start rounded-lg px-2.5 py-1 text-[11px] font-semibold border backdrop-blur-sm"
                  style={{
                    color: st.color,
                    borderColor: st.color + "55",
                    backgroundColor: st.color + "18",
                  }}
                >
                  {st.label}: {e.horse}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Kontroller */}
      <div className="flex flex-wrap items-center gap-2">
        <button
          onClick={handlePlayPause}
          className="px-4 py-1.5 rounded-lg bg-gradient-to-b from-trav-gold to-trav-gold-dim text-trav-bg font-bold text-sm active:scale-[0.98] transition-transform"
        >
          {isFinished ? "Spela om" : isPlaying ? "Paus" : "Spela"}
        </button>

        <div className="flex items-center gap-1">
          {SPEED_OPTIONS.map((s) => (
            <button
              key={s}
              onClick={() => setSpeed(s)}
              className={`px-2 py-1 rounded-md text-xs font-semibold tabular-nums transition-colors ${
                speed === s
                  ? "bg-trav-gold text-trav-bg"
                  : "bg-trav-active border border-trav-border text-gray-400 hover:text-gray-200"
              }`}
            >
              {s}×
            </button>
          ))}
        </div>

        <button
          onClick={() => setFollowMine((v) => !v)}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors ${
            followMine
              ? "bg-trav-gold/15 border-trav-gold/40 text-trav-gold"
              : "bg-trav-active border-trav-border text-gray-400 hover:text-gray-200"
          }`}
        >
          {followMine ? "Följer min häst" : "Följ min häst"}
        </button>

        <button
          onClick={skipToResult}
          className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-trav-active border border-trav-border text-gray-400 hover:text-gray-200"
        >
          Hoppa till resultat
        </button>

        <div className="flex-1 h-2 bg-trav-border rounded-full cursor-pointer relative min-w-[120px]" onClick={handleSeek}>
          <div
            className="h-full bg-trav-gold/70 rounded-full"
            style={{ width: `${((currentFrame + fraction) / Math.max(1, totalFrames - 1)) * 100}%` }}
          />
        </div>

        <span className="text-xs text-gray-500 tabular-nums min-w-[86px] text-right">
          {Math.round(currentMeters)} / {distance} m
        </span>
      </div>

      {/* Kommentatorsflöde */}
      {commentary.length > 0 && (
        <div className="bg-trav-card border border-trav-border rounded-xl">
          <div className="section-label px-3 pt-3 pb-1">Loppkommentar</div>
          <div ref={feedRef} className="max-h-52 overflow-y-auto px-3 pb-3 space-y-1">
            {visibleCommentary.map((l, i) => {
              const isLast = i === visibleCommentary.length - 1;
              return (
                <div
                  key={`${l.d}-${i}`}
                  className={`text-[13px] leading-snug flex gap-2 transition-opacity ${
                    isLast ? "opacity-100" : "opacity-70"
                  }`}
                >
                  <span className="text-[10px] text-gray-600 tabular-nums w-14 shrink-0 pt-0.5">
                    {PHASE_LABELS[l.phase] ? `${l.d} m` : `${l.d} m`}
                  </span>
                  <span
                    className={
                      l.tone === "player"
                        ? "text-trav-gold font-medium"
                        : l.tone === "drama"
                        ? "text-gray-100"
                        : "text-gray-400"
                    }
                  >
                    {l.text}
                  </span>
                </div>
              );
            })}
            {visibleCommentary.length === 0 && (
              <p className="text-xs text-gray-600">Starta uppspelningen för att följa loppet.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
