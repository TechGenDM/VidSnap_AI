"use client";

import { useState, useEffect } from "react";
import { Settings as SettingsIcon, Key, Sliders, Shield, CheckCircle2, AlertCircle, RefreshCw, Cpu } from "lucide-react";

interface HealthStatus {
  status: string;
  app: string;
  version: string;
  ffmpeg: boolean;
  ffprobe: boolean;
  elevenlabs_configured: boolean;
}

export default function SettingsPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [latency, setLatency] = useState<number | null>(null);
  const [isChecking, setIsChecking] = useState(false);

  const checkHealth = async () => {
    setIsChecking(true);
    const start = performance.now();
    try {
      const res = await fetch("/api/health");
      const elapsed = Math.round(performance.now() - start);
      setLatency(elapsed);
      if (res.ok) {
        setHealth(await res.json());
      }
    } catch (e) {
      console.error("Health check failed", e);
    } finally {
      setIsChecking(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  return (
    <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-10 w-full">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold uppercase tracking-wider text-cyan-400 font-mono">
              System Telemetry
            </span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white mb-1">
            Engine Diagnostics
          </h1>
          <p className="text-sm text-zinc-400">
            Real-time status for ElevenLabs voice synthesis, FFmpeg video rendering, and storage.
          </p>
        </div>

        <button
          onClick={checkHealth}
          disabled={isChecking}
          className="flex items-center gap-2 rounded-xl bg-white/[0.04] border border-white/[0.1] hover:border-cyan-500/40 hover:bg-cyan-500/10 px-4 py-2.5 text-xs font-bold text-zinc-200 hover:text-white transition-all self-start sm:self-auto disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 text-cyan-400 ${isChecking ? "animate-spin" : ""}`} />
          <span>{isChecking ? "Pinging Engine..." : "Ping Engine"}</span>
        </button>
      </div>

      <div className="space-y-6">
        {/* Live Diagnostics Card */}
        <div className="glass-card rounded-2xl p-6 border-white/[0.08]">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                <Cpu className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Backend Status</h3>
                <p className="text-xs text-zinc-400">
                  FastAPI service on 127.0.0.1:8000
                </p>
              </div>
            </div>

            {health?.status === "healthy" ? (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-400">
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>Healthy • {latency ? `${latency}ms` : "Active"}</span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-red-500/30 bg-red-500/10 px-3 py-1 text-xs font-semibold text-red-400">
                <AlertCircle className="h-3.5 w-3.5" />
                <span>Unreachable</span>
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
            <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.06] flex items-center justify-between">
              <span className="text-xs text-zinc-400">ElevenLabs TTS</span>
              <span className={`text-xs font-bold ${health?.elevenlabs_configured ? "text-emerald-400" : "text-amber-400"}`}>
                {health?.elevenlabs_configured ? "Configured" : "Local Engine"}
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.06] flex items-center justify-between">
              <span className="text-xs text-zinc-400">FFmpeg 8.0</span>
              <span className={`text-xs font-bold ${health?.ffmpeg ? "text-emerald-400" : "text-red-400"}`}>
                {health?.ffmpeg ? "Active" : "Missing"}
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.06] flex items-center justify-between">
              <span className="text-xs text-zinc-400">FFprobe</span>
              <span className={`text-xs font-bold ${health?.ffprobe ? "text-emerald-400" : "text-red-400"}`}>
                {health?.ffprobe ? "Active" : "Missing"}
              </span>
            </div>
          </div>
        </div>

        {/* Speech Synthesis Provider Card */}
        <div className="glass-card rounded-2xl p-6 border-white/[0.08]">
          <div className="flex items-center gap-3 mb-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Key className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Speech Synthesis Architecture</h3>
              <p className="text-xs text-zinc-400">
                ElevenLabs Turbo v2.5 with local fallback engine.
              </p>
            </div>
          </div>
          <p className="text-xs text-zinc-400 leading-relaxed">
            VidSnap automatically inspects <code className="text-cyan-300">ELEVENLABS_API_KEY</code> from environment variables. When valid, high-fidelity 44.1kHz studio narration is streamed. If the key is absent or quota exceeded, the built-in local synthesizer runs seamlessly without halting your workflow.
          </p>
        </div>

        {/* Video Engine Card */}
        <div className="glass-card rounded-2xl p-6 border-white/[0.08]">
          <div className="flex items-center gap-3 mb-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
              <Sliders className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Video Rendering Specifications</h3>
              <p className="text-xs text-zinc-400">
                1080×1920 (9:16 Portrait Canvas) • 30 FPS • H.264
              </p>
            </div>
          </div>
          <p className="text-xs text-zinc-400 leading-relaxed">
            Canvas compilation applies dynamic blurred background padding, sample aspect ratio normalization (<code className="text-purple-300">setsar=1</code>), speech-synchronized word-level kinetic captions, smooth audio crossfading, and background music ducking.
          </p>
        </div>
      </div>
    </div>
  );
}
