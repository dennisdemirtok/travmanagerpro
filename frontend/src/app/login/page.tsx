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
      <div className="w-full max-w-sm bg-trav-card border border-trav-border rounded-xl p-8">
        <h1 className="text-2xl font-bold text-trav-gold mb-1">TravManager</h1>
        <p className="text-gray-500 text-sm mb-6">Logga in till ditt stall</p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            placeholder="Anvandarnamn"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full px-3 py-2 bg-trav-bg border border-trav-border rounded-lg text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-trav-gold"
          />
          <input
            type="password"
            placeholder="Losenord"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-3 py-2 bg-trav-bg border border-trav-border rounded-lg text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-trav-gold"
          />
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <Button type="submit" disabled={loading} className="w-full">
            {loading ? "Loggar in..." : "Logga in"}
          </Button>
        </form>
        <p className="text-center text-sm text-gray-500 mt-4">
          Inget konto?{" "}
          <a href="/register" className="text-trav-gold hover:underline">Registrera</a>
        </p>
      </div>
    </div>
  );
}
