"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuthStore } from "@/lib/auth";
import { Button } from "@/components/ui/Button";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const login = useAuthStore((s) => s.login);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await api.login(username, password);
      login(res.access_token, res.refresh_token, username);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Inloggning misslyckades");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-trav-bg">
      {/* Subtle radial glow behind card */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="w-[500px] h-[500px] bg-trav-gold/[0.03] rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-sm bg-trav-card border border-trav-border rounded-2xl p-8 shadow-card">
        {/* Logo */}
        <div className="flex items-center gap-2.5 mb-6">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-trav-gold to-trav-gold-dim flex items-center justify-center shadow-gold-glow">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0C0E13" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z" />
              <line x1="4" y1="22" x2="4" y2="15" />
            </svg>
          </div>
          <div>
            <h1 className="text-xl font-bold text-trav-gold leading-tight">TravManager</h1>
            <p className="text-[11px] text-gray-500 font-medium">Logga in till ditt stall</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3.5">
          <div>
            <label className="text-[11px] font-medium text-gray-500 uppercase tracking-wider mb-1.5 block">Anvandarnamn</label>
            <input
              type="text"
              placeholder="Ditt anvandarnamn"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-trav-bg border border-trav-border rounded-lg text-sm text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-trav-gold/60 focus:ring-1 focus:ring-trav-gold/20 transition-colors"
            />
          </div>
          <div>
            <label className="text-[11px] font-medium text-gray-500 uppercase tracking-wider mb-1.5 block">Losenord</label>
            <input
              type="password"
              placeholder="Ditt losenord"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-trav-bg border border-trav-border rounded-lg text-sm text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-trav-gold/60 focus:ring-1 focus:ring-trav-gold/20 transition-colors"
            />
          </div>
          {error && (
            <div className="flex items-center gap-2 text-red-400 text-xs bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="15" y1="9" x2="9" y2="15" />
                <line x1="9" y1="9" x2="15" y2="15" />
              </svg>
              {error}
            </div>
          )}
          <Button type="submit" disabled={loading} className="w-full mt-1">
            {loading ? "Loggar in..." : "Logga in"}
          </Button>
        </form>
        <p className="text-center text-xs text-gray-500 mt-5">
          Inget konto?{" "}
          <a href="/register" className="text-trav-gold hover:text-trav-gold-bright font-medium transition-colors">Registrera</a>
        </p>
      </div>
    </div>
  );
}
