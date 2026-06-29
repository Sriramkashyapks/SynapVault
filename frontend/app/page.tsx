"use client";

import { useEffect, useState } from "react";

interface SystemHealth {
  status: string;
  database: string;
}

export default function Dashboard() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const apiURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiURL}/health`);
      if (!response.ok) {
        throw new Error(`Server returned status: ${response.status}`);
      }
      const data = await response.json();
      setHealth(data);
    } catch (err: any) {
      setError(err.message || "Failed to contact SynapVault server");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="space-y-8">
      {/* Welcome banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-indigo-900/40 via-purple-900/20 to-zinc-900 border border-zinc-800 animate-fade-in">
        <h2 className="text-2xl font-bold tracking-tight text-white mb-2">Welcome to SynapVault</h2>
        <p className="text-zinc-400 max-w-xl text-sm leading-relaxed">
          Your secure, neural network enterprise brain. Monitor infrastructure health, ingest corporate documentation, and conduct natural language queries securely.
        </p>
      </div>

      {/* Health Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* API STATUS CARD */}
        <div className="p-6 rounded-xl border border-zinc-800 bg-zinc-900/30 backdrop-blur-sm transition hover:border-zinc-700">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-zinc-400 font-medium text-sm uppercase tracking-wider">FastAPI Backend Status</h3>
            {loading ? (
              <span className="text-xs text-zinc-500 animate-pulse">Checking...</span>
            ) : error ? (
              <span className="flex items-center gap-1.5 text-xs text-red-500">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500"></span> Offline
              </span>
            ) : (
              <span className="flex items-center gap-1.5 text-xs text-green-400">
                <span className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse"></span> Active
              </span>
            )}
          </div>
          <p className="text-3xl font-extrabold text-white">
            {loading ? "..." : error ? "CONNECTION FAILED" : "HEALTHY"}
          </p>
          <p className="text-xs text-zinc-500 mt-2">
            URL: {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
          </p>
        </div>

        {/* DATABASE STATUS CARD */}
        <div className="p-6 rounded-xl border border-zinc-800 bg-zinc-900/30 backdrop-blur-sm transition hover:border-zinc-700">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-zinc-400 font-medium text-sm uppercase tracking-wider">PostgreSQL Vector DB</h3>
            {loading ? (
              <span className="text-xs text-zinc-500 animate-pulse">Checking...</span>
            ) : error || health?.database !== "connected" ? (
              <span className="flex items-center gap-1.5 text-xs text-red-500">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500"></span> Disconnected
              </span>
            ) : (
              <span className="flex items-center gap-1.5 text-xs text-green-400">
                <span className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse"></span> Connected
              </span>
            )}
          </div>
          <p className="text-3xl font-extrabold text-white text-wrap">
            {loading ? "..." : error ? "UNAVAILABLE" : health?.database === "connected" ? "STABLE" : "ERROR"}
          </p>
          {health?.database !== "connected" && !loading && (
            <p className="text-xs text-red-400 mt-2 line-clamp-1">{health?.database || error}</p>
          )}
          {health?.database === "connected" && (
            <p className="text-xs text-zinc-500 mt-2">pgvector extension enabled & listening on port 5432</p>
          )}
        </div>

      </div>

      {/* Manual refresh button */}
      <div className="flex justify-end">
        <button
          onClick={fetchHealth}
          disabled={loading}
          className="px-5 py-2.5 rounded-lg bg-indigo-600 text-white font-medium text-sm hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 disabled:opacity-50 transition cursor-pointer"
        >
          {loading ? "Refreshing..." : "🔄 Refresh Control Status"}
        </button>
      </div>
    </div>
  );
}
