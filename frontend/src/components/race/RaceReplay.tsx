"use client";

import { useCallback, useEffect, useRef, useState } from "react";

// ─── Types ───────────────────────────────────────────────────────
interface Position {
  id: string;
  n: string;   // horse name
  pos: number;  // position in meters
  e: number;    // energy
  spd: number;  // speed
  g: boolean;   // galloping
  dq: boolean;  // disqualified
  r: number;    // rank
}

interface Snapshot {
  d: number;          // distance marker (meters into race)
  p: Position[];      // positions
}

interface Finisher {
  position: number;
  horse_name: string;
  horse_id: string;
  is_npc: boolean;
  km_time: string;
  prize_money: number;
}

interface RaceReplayProps {
  snapshots: Snapshot[];
  finishers: Finisher[];
  distance: number;
  raceName: string;
}

// ─── Constants ───────────────────────────────────────────────────
const CANVAS_W = 800;
const CANVAS_H = 440;
const CENTER_X = CANVAS_W / 2;
const CENTER_Y = CANVAS_H / 2 - 10;
const TRACK_RX_OUTER = 310;
const TRACK_RY_OUTER = 155;
const TRACK_RX_INNER = 240;
const TRACK_RY_INNER = 105;
const TRACK_RX_MID = (TRACK_RX_OUTER + TRACK_RX_INNER) / 2;
const TRACK_RY_MID = (TRACK_RY_OUTER + TRACK_RY_INNER) / 2;
const LANE_WIDTH = (TRACK_RX_OUTER - TRACK_RX_INNER);

const HORSE_COLORS = [
  "#E63946", "#457B9D", "#2A9D8F", "#E9C46A",
  "#F4A261", "#264653", "#A8DADC", "#6D6875",
  "#B5838D", "#FFB4A2", "#6A994E", "#BC6C25",
];

const SPEED_OPTIONS = [0.5, 1, 2, 4];

// ─── Component ───────────────────────────────────────────────────
export function RaceReplay({ snapshots, finishers, distance, raceName }: RaceReplayProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);
  const lastTimeRef = useRef<number>(0);

  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [fraction, setFraction] = useState(0);
  const [isFinished, setIsFinished] = useState(false);

  const FRAME_MS = 250; // ms per snapshot at 1x speed
  const totalFrames = snapshots.length;

  // Build horse→color map from first snapshot
  const horseColorMap = useRef<Map<string, string>>(new Map());
  const horseIndexMap = useRef<Map<string, number>>(new Map());
  if (snapshots.length > 0 && horseColorMap.current.size === 0) {
    snapshots[0].p.forEach((p, i) => {
      horseColorMap.current.set(p.id, HORSE_COLORS[i % HORSE_COLORS.length]);
      horseIndexMap.current.set(p.id, i);
    });
  }

  // Check if a horse is the player's
  const playerHorseIds = new Set(
    finishers.filter((f) => !f.is_npc).map((f) => f.horse_id)
  );

  // ─── Drawing ─────────────────────────────────────────────────
  const draw = useCallback(
    (frameIdx: number, frac: number) => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      const current = snapshots[frameIdx];
      const next = snapshots[Math.min(frameIdx + 1, totalFrames - 1)];
      if (!current) return;

      // Clear
      ctx.clearRect(0, 0, CANVAS_W, CANVAS_H);

      // Background
      ctx.fillStyle = "#0f1923";
      ctx.fillRect(0, 0, CANVAS_W, CANVAS_H);

      // Inner grass area
      ctx.beginPath();
      ctx.ellipse(CENTER_X, CENTER_Y, TRACK_RX_INNER - 4, TRACK_RY_INNER - 4, 0, 0, Math.PI * 2);
      ctx.fillStyle = "#1a3a1a";
      ctx.fill();

      // Track surface
      ctx.beginPath();
      ctx.ellipse(CENTER_X, CENTER_Y, TRACK_RX_OUTER, TRACK_RY_OUTER, 0, 0, Math.PI * 2);
      ctx.fillStyle = "#4a3c2e";
      ctx.fill();
      ctx.beginPath();
      ctx.ellipse(CENTER_X, CENTER_Y, TRACK_RX_INNER, TRACK_RY_INNER, 0, 0, Math.PI * 2);
      ctx.fillStyle = "#1a3a1a";
      ctx.fill();

      // Track border lines
      ctx.strokeStyle = "#6b5a47";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.ellipse(CENTER_X, CENTER_Y, TRACK_RX_OUTER, TRACK_RY_OUTER, 0, 0, Math.PI * 2);
      ctx.stroke();
      ctx.beginPath();
      ctx.ellipse(CENTER_X, CENTER_Y, TRACK_RX_INNER, TRACK_RY_INNER, 0, 0, Math.PI * 2);
      ctx.stroke();

      // Find max position for normalization
      const allPositions = current.p.map((p) => p.pos);
      const nextPositions = next.p.map((p) => p.pos);
      const maxPos = Math.max(...allPositions, ...nextPositions, distance);

      // Sprint zone highlight (last 400m)
      const sprintStart = Math.max(0, distance - 400);
      drawSprintZone(ctx, sprintStart, distance, maxPos);

      // Start/finish line
      const finishAngle = -Math.PI / 2;
      const fx1 = CENTER_X + TRACK_RX_INNER * Math.cos(finishAngle);
      const fy1 = CENTER_Y + TRACK_RY_INNER * Math.sin(finishAngle);
      const fx2 = CENTER_X + TRACK_RX_OUTER * Math.cos(finishAngle);
      const fy2 = CENTER_Y + TRACK_RY_OUTER * Math.sin(finishAngle);
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 3;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(fx1, fy1);
      ctx.lineTo(fx2, fy2);
      ctx.stroke();
      ctx.setLineDash([]);

      // Distance markers every 500m
      ctx.fillStyle = "#555";
      ctx.font = "10px sans-serif";
      ctx.textAlign = "center";
      for (let dm = 500; dm < distance; dm += 500) {
        const dAngle = (dm / distance) * Math.PI * 2 - Math.PI / 2;
        const dx = CENTER_X + (TRACK_RX_OUTER + 14) * Math.cos(dAngle);
        const dy = CENTER_Y + (TRACK_RY_OUTER + 14) * Math.sin(dAngle);
        ctx.fillText(`${dm}m`, dx, dy + 3);

        // Small tick on track edge
        const tx1 = CENTER_X + TRACK_RX_OUTER * Math.cos(dAngle);
        const ty1 = CENTER_Y + TRACK_RY_OUTER * Math.sin(dAngle);
        const tx2 = CENTER_X + (TRACK_RX_OUTER + 6) * Math.cos(dAngle);
        const ty2 = CENTER_Y + (TRACK_RY_OUTER + 6) * Math.sin(dAngle);
        ctx.strokeStyle = "#555";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(tx1, ty1);
        ctx.lineTo(tx2, ty2);
        ctx.stroke();
      }

      // Draw horses
      const horses = current.p.slice().sort((a, b) => a.r - b.r);
      for (const horse of horses) {
        const nextHorse = next.p.find((p) => p.id === horse.id);
        const pos1 = horse.pos;
        const pos2 = nextHorse ? nextHorse.pos : pos1;
        const interpPos = pos1 + (pos2 - pos1) * frac;

        // Map to oval position
        const angle = (interpPos / maxPos) * Math.PI * 2 - Math.PI / 2;

        // Spread horses across lanes based on rank to avoid overlap
        const rank = horse.r;
        const totalHorses = current.p.length;
        const laneOffset = ((rank - 1) / Math.max(1, totalHorses - 1)) * 0.7 + 0.15;
        const rx = TRACK_RX_INNER + LANE_WIDTH * laneOffset;
        const ry = TRACK_RY_INNER + LANE_WIDTH * (laneOffset * TRACK_RY_OUTER / TRACK_RX_OUTER);

        const hx = CENTER_X + rx * Math.cos(angle);
        const hy = CENTER_Y + ry * Math.sin(angle);

        const color = horseColorMap.current.get(horse.id) || "#888";
        const isPlayer = playerHorseIds.has(horse.id);
        const radius = isPlayer ? 10 : 8;

        // Gallop indicator: pulsing red ring
        if (horse.g && !horse.dq) {
          ctx.beginPath();
          ctx.arc(hx, hy, radius + 5, 0, Math.PI * 2);
          ctx.strokeStyle = "#EF4444";
          ctx.lineWidth = 3;
          ctx.globalAlpha = 0.6 + Math.sin(Date.now() / 150) * 0.4;
          ctx.stroke();
          ctx.globalAlpha = 1;
        }

        // Player glow
        if (isPlayer) {
          ctx.beginPath();
          ctx.arc(hx, hy, radius + 4, 0, Math.PI * 2);
          ctx.strokeStyle = "#D4A853";
          ctx.lineWidth = 2;
          ctx.globalAlpha = 0.5;
          ctx.stroke();
          ctx.globalAlpha = 1;
        }

        // Horse circle
        ctx.beginPath();
        ctx.arc(hx, hy, radius, 0, Math.PI * 2);
        ctx.fillStyle = horse.dq ? "#555" : color;
        ctx.fill();
        ctx.strokeStyle = isPlayer ? "#D4A853" : "#222";
        ctx.lineWidth = isPlayer ? 2 : 1;
        ctx.stroke();

        // Rank number
        ctx.fillStyle = "#fff";
        ctx.font = `bold ${isPlayer ? 11 : 9}px monospace`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        if (horse.dq) {
          ctx.fillText("✕", hx, hy);
        } else {
          ctx.fillText(String(horse.r), hx, hy);
        }
      }

      // Race info overlay
      const raceProgress = current.d / distance;
      ctx.fillStyle = "#9CA3AF";
      ctx.font = "13px sans-serif";
      ctx.textAlign = "left";
      ctx.textBaseline = "top";
      ctx.fillText(`${current.d}m / ${distance}m`, 12, 12);

      // Progress bar at bottom
      const barY = CANVAS_H - 16;
      const barW = CANVAS_W - 24;
      ctx.fillStyle = "#333";
      ctx.fillRect(12, barY, barW, 6);
      ctx.fillStyle = "#D4A853";
      ctx.fillRect(12, barY, barW * raceProgress, 6);

      // Sprint zone label
      if (raceProgress > (distance - 400) / distance) {
        ctx.fillStyle = "#F97316";
        ctx.font = "bold 12px sans-serif";
        ctx.textAlign = "right";
        ctx.fillText("SPURT!", CANVAS_W - 12, 12);
      }
    },
    [snapshots, totalFrames, distance, playerHorseIds]
  );

  // Sprint zone overlay
  function drawSprintZone(
    ctx: CanvasRenderingContext2D,
    startM: number,
    endM: number,
    maxPos: number
  ) {
    const startAngle = (startM / maxPos) * Math.PI * 2 - Math.PI / 2;
    const endAngle = (endM / maxPos) * Math.PI * 2 - Math.PI / 2;

    ctx.globalAlpha = 0.15;
    ctx.fillStyle = "#F97316";

    // Draw arc sector between inner and outer ellipse
    ctx.beginPath();
    ctx.ellipse(CENTER_X, CENTER_Y, TRACK_RX_OUTER, TRACK_RY_OUTER, 0, startAngle, endAngle);
    // Now trace back along inner
    const steps = 30;
    for (let i = steps; i >= 0; i--) {
      const a = startAngle + (endAngle - startAngle) * (i / steps);
      const x = CENTER_X + TRACK_RX_INNER * Math.cos(a);
      const y = CENTER_Y + TRACK_RY_INNER * Math.sin(a);
      ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fill();
    ctx.globalAlpha = 1;
  }

  // ─── Animation loop ──────────────────────────────────────────
  useEffect(() => {
    if (!isPlaying || totalFrames < 2) return;

    const animate = (time: number) => {
      if (lastTimeRef.current === 0) lastTimeRef.current = time;
      const dt = time - lastTimeRef.current;
      lastTimeRef.current = time;

      setFraction((prev) => {
        let next = prev + (dt / FRAME_MS) * speed;
        if (next >= 1) {
          const overflow = Math.floor(next);
          setCurrentFrame((prevFrame) => {
            const newFrame = prevFrame + overflow;
            if (newFrame >= totalFrames - 1) {
              setIsPlaying(false);
              setIsFinished(true);
              return totalFrames - 1;
            }
            return newFrame;
          });
          return next - overflow;
        }
        return next;
      });

      animRef.current = requestAnimationFrame(animate);
    };

    lastTimeRef.current = 0;
    animRef.current = requestAnimationFrame(animate);

    return () => cancelAnimationFrame(animRef.current);
  }, [isPlaying, speed, totalFrames]);

  // ─── Draw on state change ─────────────────────────────────────
  useEffect(() => {
    draw(currentFrame, fraction);
  }, [currentFrame, fraction, draw]);

  // Initial draw
  useEffect(() => {
    draw(0, 0);
  }, []);

  // ─── Controls ─────────────────────────────────────────────────
  const handlePlayPause = () => {
    if (isFinished) {
      // Restart
      setCurrentFrame(0);
      setFraction(0);
      setIsFinished(false);
      setIsPlaying(true);
    } else {
      setIsPlaying(!isPlaying);
    }
  };

  const handleSeek = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const frame = Math.floor(pct * (totalFrames - 1));
    setCurrentFrame(frame);
    setFraction(0);
    setIsFinished(false);
  };

  // Current positions for leaderboard
  const currentSnap = snapshots[currentFrame];
  const sortedHorses = currentSnap
    ? [...currentSnap.p].sort((a, b) => a.r - b.r)
    : [];

  const leaderPos = sortedHorses[0]?.pos || 0;

  if (!snapshots.length) return null;

  return (
    <div className="space-y-3">
      {/* Canvas */}
      <div className="bg-[#0f1923] rounded-lg overflow-hidden border border-trav-border">
        <canvas
          ref={canvasRef}
          width={CANVAS_W}
          height={CANVAS_H}
          className="w-full"
          style={{ imageRendering: "auto" }}
        />
      </div>

      {/* Controls */}
      <div className="flex items-center gap-3">
        <button
          onClick={handlePlayPause}
          className="px-4 py-1.5 rounded bg-trav-gold text-black font-bold text-sm hover:bg-trav-gold/90 transition-colors"
        >
          {isFinished ? "⟳ Om" : isPlaying ? "⏸ Paus" : "▶ Spela"}
        </button>

        <div className="flex items-center gap-1">
          {SPEED_OPTIONS.map((s) => (
            <button
              key={s}
              onClick={() => setSpeed(s)}
              className={`px-2 py-1 rounded text-xs font-mono ${
                speed === s
                  ? "bg-trav-gold text-black"
                  : "bg-trav-dark-2 text-gray-400 hover:text-white"
              }`}
            >
              {s}×
            </button>
          ))}
        </div>

        {/* Seekbar */}
        <div
          className="flex-1 h-2 bg-trav-dark-2 rounded cursor-pointer relative"
          onClick={handleSeek}
        >
          <div
            className="h-full bg-trav-gold/60 rounded"
            style={{
              width: `${((currentFrame + fraction) / Math.max(1, totalFrames - 1)) * 100}%`,
            }}
          />
        </div>

        <span className="text-xs text-gray-500 tabular-nums min-w-[60px] text-right">
          {currentSnap?.d || 0}m / {distance}m
        </span>
      </div>

      {/* Live leaderboard */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        {sortedHorses.slice(0, 12).map((h) => {
          const color = horseColorMap.current.get(h.id) || "#888";
          const isPlayer = playerHorseIds.has(h.id);
          const gap = leaderPos - h.pos;

          return (
            <div
              key={h.id}
              className={`flex items-center gap-2 px-2 py-1 rounded ${
                isPlayer
                  ? "bg-trav-gold/10 border border-trav-gold/30"
                  : "bg-trav-dark-2"
              }`}
            >
              <span className="font-bold text-gray-300 w-4">{h.r}</span>
              <span
                className="w-3 h-3 rounded-full flex-shrink-0"
                style={{ backgroundColor: color }}
              />
              <span
                className={`flex-1 truncate ${
                  isPlayer ? "text-trav-gold font-semibold" : "text-gray-400"
                }`}
              >
                {h.n}
              </span>
              {h.dq ? (
                <span className="text-red-400 text-[10px]">DQ</span>
              ) : h.g ? (
                <span className="text-red-400 text-[10px]">GALP</span>
              ) : (
                <span className="text-gray-600 tabular-nums">
                  {h.r === 1 ? "" : `+${gap.toFixed(1)}m`}
                </span>
              )}
              {/* Energy bar */}
              <div className="w-10 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all"
                  style={{
                    width: `${Math.max(0, h.e)}%`,
                    backgroundColor:
                      h.e > 50 ? "#22c55e" : h.e > 25 ? "#eab308" : "#ef4444",
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
