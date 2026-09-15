"use client";

import { useState } from "react";
import { Sparkles, MessageSquareText, RefreshCw, CheckCircle2, ArrowRight } from "lucide-react";
import Link from "next/link";

export default function StoryFirstDemo() {
  const [isEnhanced, setIsEnhanced] = useState(true);

  const hookBefore = "Today I will discuss vector databases and why they matter for search.";
  const hookAfter = "Stop storing embeddings in relational tables. Here is why.";

  const captionBefore = "VECTOR DATABASES EXPLAINED";
  const captionAfter = "STOP USING RELATIONAL TABLES";

  return (
    <section id="story-editor" className="w-full py-20 sm:py-28 border-t border-white/[0.06] bg-[#090b12]/70 relative overflow-hidden">
      {/* Background Subtle Ambient Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-purple-600/10 rounded-full blur-[120px] pointer-events-none" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-1.5 rounded-full border border-purple-500/30 bg-purple-500/10 px-3 py-1 text-xs font-bold uppercase tracking-wider text-purple-300 mb-4">
            <span>The VidSnap Differentiator</span>
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-white mb-4">
            VidSnap edits the story, not the timeline.
          </h2>
          <p className="text-base sm:text-lg text-zinc-400 leading-relaxed">
            Traditional video editors force you into tracks, cuts, and keyframes. VidSnap lets you refine the narrative,
            recalculating audio timing and captions automatically.
          </p>
        </div>

        {/* Interactive Showcase: Storyboard on Left, Live Phone on Right */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center max-w-6xl mx-auto">
          {/* Left: Storyboard & Ask VidSnap Interface */}
          <div className="lg:col-span-7 flex flex-col gap-5">
            {/* Interactive Toggle Pill Bar */}
            <div className="flex items-center gap-2 p-1.5 rounded-xl bg-white/[0.04] border border-white/[0.08] self-start">
              <button
                onClick={() => setIsEnhanced(false)}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  !isEnhanced
                    ? "bg-white/[0.12] text-white shadow-sm"
                    : "text-zinc-400 hover:text-white"
                }`}
              >
                1. Original Hook
              </button>
              <button
                onClick={() => setIsEnhanced(true)}
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  isEnhanced
                    ? "bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-md shadow-purple-500/25"
                    : "text-zinc-400 hover:text-white"
                }`}
              >
                <Sparkles className="h-3 w-3" />
                <span>2. Ask VidSnap: Stronger Hook</span>
              </button>
            </div>

            {/* Storyboard Card */}
            <div className="glass-card rounded-2xl p-6 sm:p-7 border-purple-500/20 shadow-2xl space-y-6">
              {/* Scene 1 Hook Block */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="flex h-5 w-5 rounded-md bg-purple-500/20 text-purple-300 font-mono text-[10px] font-bold items-center justify-center border border-purple-500/30">
                      01
                    </span>
                    <span className="text-xs font-bold uppercase tracking-wider text-zinc-300">
                      Opening Scene Hook
                    </span>
                  </div>
                  <span className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full ${
                    isEnhanced
                      ? "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30"
                      : "bg-zinc-800 text-zinc-400 border border-zinc-700"
                  }`}>
                    {isEnhanced ? "Stronger Hook Applied ✓" : "Standard Hook"}
                  </span>
                </div>

                <div className="p-4 rounded-xl bg-black/40 border border-white/[0.08] transition-all">
                  <p className="text-sm sm:text-base font-medium text-white leading-relaxed">
                    “{isEnhanced ? hookAfter : hookBefore}”
                  </p>
                </div>
              </div>

              {/* Ask VidSnap Prompt Bar */}
              <div className="p-4 rounded-xl bg-gradient-to-r from-purple-950/30 via-indigo-950/20 to-transparent border border-purple-500/25">
                <div className="flex items-center gap-2 text-xs font-bold text-purple-300 mb-2">
                  <MessageSquareText className="h-3.5 w-3.5 text-purple-400" />
                  <span>Ask VidSnap Creative Direction</span>
                </div>
                <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
                  <span className="text-xs text-zinc-300 font-mono italic">
                    “Make this hook more provocative.”
                  </span>
                  <button
                    onClick={() => setIsEnhanced(!isEnhanced)}
                    className="flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-500/20 hover:bg-purple-500/30 text-purple-200 border border-purple-500/40 text-xs font-semibold transition-colors shrink-0"
                  >
                    <RefreshCw className="h-3 w-3 text-purple-400" />
                    <span>{isEnhanced ? "Reset Hook" : "Apply Stronger Hook"}</span>
                  </button>
                </div>
              </div>

              {/* Automatic Pipeline Sync Indicators */}
              <div className="grid grid-cols-3 gap-3 pt-2 border-t border-white/[0.06] text-[11px] text-zinc-400">
                <div className="flex items-center gap-1.5">
                  <CheckCircle2 className="h-3 w-3 text-emerald-400 shrink-0" />
                  <span>Voice regenerated</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <CheckCircle2 className="h-3 w-3 text-emerald-400 shrink-0" />
                  <span>Captions re-synced</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <CheckCircle2 className="h-3 w-3 text-emerald-400 shrink-0" />
                  <span>0 keyframes touched</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-4 text-xs text-zinc-400 pt-2">
              <Link
                href="/create"
                className="inline-flex items-center gap-1.5 text-purple-400 hover:text-purple-300 font-semibold transition-colors"
              >
                <span>Try the story editor in Studio</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </div>

          {/* Right: Companion Phone Preview Showing Updated Scene */}
          <div className="lg:col-span-5 flex justify-center">
            <div className="w-full max-w-[280px] sm:max-w-[310px] aspect-[9/18] rounded-[36px] bg-black border-[6px] border-[#1f2333] shadow-2xl relative overflow-hidden flex flex-col justify-between p-4">
              {/* Top Notch */}
              <div className="absolute top-2 left-1/2 -translate-x-1/2 w-20 h-4 bg-black rounded-full z-40 border border-white/10" />

              {/* Header inside phone */}
              <div className="relative z-30 flex justify-between items-center text-[10px] font-mono text-zinc-400 pt-2 px-2">
                <span>SCENE 1 / 4</span>
                <span className="text-purple-400 font-bold">STORY-SYNCED</span>
              </div>

              {/* Center Kinetic Caption Simulation */}
              <div className="relative z-30 text-center px-3 py-6 my-auto">
                <span className="text-[10px] font-mono uppercase tracking-widest text-purple-400/90 block mb-2">
                  {isEnhanced ? "STRONGER HOOK PREVIEW" : "ORIGINAL HOOK PREVIEW"}
                </span>
                <h4 className="text-base sm:text-lg font-black uppercase text-white tracking-wide leading-tight drop-shadow-md">
                  {isEnhanced ? (
                    <>
                      STOP USING <br />
                      <span className="text-cyan-400 drop-shadow-[0_0_8px_rgba(0,240,255,0.8)]">
                        RELATIONAL
                      </span>{" "}
                      <span className="text-yellow-400">TABLES</span>
                    </>
                  ) : (
                    <>
                      VECTOR DATABASES <br />
                      <span className="text-zinc-300">EXPLAINED</span>
                    </>
                  )}
                </h4>
              </div>

              {/* Bottom Scene Status HUD */}
              <div className="relative z-30 p-3 rounded-xl bg-white/[0.06] backdrop-blur-md border border-white/[0.1] flex flex-col gap-1.5 text-[10px]">
                <div className="flex items-center justify-between text-zinc-300 font-semibold">
                  <span>Narration Duration:</span>
                  <span className="font-mono text-white">{isEnhanced ? "3.8s" : "4.2s"}</span>
                </div>
                <div className="flex items-center justify-between text-zinc-400">
                  <span>Speech-Synced Word Sync:</span>
                  <span className="text-emerald-400 font-bold">100% Locked</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
