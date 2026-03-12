import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatOre(ore: number): string {
  const kr = ore / 100;
  return kr.toLocaleString("sv-SE") + " kr";
}

export function formatStat(value: number): string {
  return String(Math.round(value));
}

export function statColor(value: number): string {
  if (value >= 85) return "#4ADE80";
  if (value >= 70) return "#D4A853";
  if (value >= 55) return "#FB923C";
  return "#F87171";
}
