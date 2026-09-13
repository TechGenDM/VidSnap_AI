"use client";

import { useState, useRef } from "react";
import Link from "next/link";
import {
  Sparkles,
  Play,
  Pause,
  Volume2,
  VolumeX,
  ArrowRight,
  Zap,
  Bot,
  Repeat,
  CheckCircle2,
  Share2,
  Wand2,
} from "lucide-react";

export default function HomePage() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
      setIsPlaying(false);
    } else {
      videoRef.current.play();
      setIsPlaying(true);
    }
  };

  const toggleMute = () => {
    if (!videoRef.current) return;
    videoRef.current.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  return (
    <div className="flex flex-col items-center">
      {/* Hero Section */}
      <section className="relative w-full overflow-hidden pt-20 pb-28 md:pt-28 md:pb-36 radial-glow">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
            {/* Left Content */}
            <div className="lg:col-span-7 flex flex-col items-start text-left">
              <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/20 bg-indigo-500/10 px-3.5 py-1 text-xs font-semibold text-indigo-400 mb-6">
                <Sparkles className="h-3.5 w-3.5 text-indigo-400 animate-pulse" />
                <span>Next-Gen Video Generation Engine</span>
              </div>

              <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-white leading-[1.08] mb-6">
                Turn your ideas <br className="hidden sm:inline" />
                into <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-300 to-pink-400">videos.</span>
              </h1>

              <p className="text-lg sm:text-xl text-zinc-400 max-w-2xl mb-10 leading-relaxed">
                Create polished short-form videos with AI-generated narration, captions, motion and music —{" "}
                <span className="text-zinc-200 font-medium">without editing timelines.</span>
              </p>

              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 w-full sm:w-auto">
                <Link
                  href="/create"
                  className="flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 px-7 py-3.5 text-base font-semibold text-white shadow-xl shadow-indigo-500/25 hover:from-indigo-600 hover:to-purple-700 hover:shadow-indigo-500/40 transition-all active:scale-98"
                >
                  <Zap className="h-5 w-5" />
                  <span>Create a Reel</span>
                  <ArrowRight className="h-4 w-4 ml-1" />
                </Link>

                <a
                  href="#how-it-works"
                  className="flex items-center justify-center gap-2 rounded-xl border border-zinc-800 bg-zinc-900/60 px-6 py-3.5 text-base font-medium text-zinc-300 hover:bg-zinc-850 hover:text-white hover:border-zinc-700 transition-all"
                >
                  <span>See how it works</span>
                </a>
              </div>

              {/* Trust/Philosophy Badge */}
              <div className="mt-12 flex items-center gap-3 pt-6 border-t border-zinc-850 text-xs text-zinc-400">
                <span className="flex h-2 w-2 rounded-full bg-emerald-400 ring-4 ring-emerald-400/20" />
                <span>Product Principle: <strong>VidSnap edits the story, not the timeline.</strong></span>
              </div>
            </div>

            {/* Right: Phone-Shaped Interactive Showcase */}
            <div className="lg:col-span-5 flex justify-center lg:justify-end">
              <div className="phone-mockup relative">
                <div className="phone-notch" />

                {/* Video / Demo Reel inside Phone */}
                <div className="relative w-full h-full bg-zinc-900 flex flex-col justify-between">
                  <video
                    ref={videoRef}
                    src="/media/reels/8de29a47-df82-48b3-a1ad-7f99190f36a1.mp4"
                    className="absolute inset-0 w-full h-full object-cover"
                    loop
                    playsInline
                    onPlay={() => setIsPlaying(true)}
                    onPause={() => setIsPlaying(false)}
                  />

                  {/* Top Status Bar Simulator */}
                  <div className="relative z-30 pt-4 px-6 flex justify-between items-center text-[11px] font-semibold text-white/70">
                    <span>9:41</span>
                    <div className="flex items-center gap-1.5">
                      <div className="h-2 w-2 rounded-full bg-emerald-400" />
                      <span>HD 1080p</span>
                    </div>
                  </div>

                  {/* Center Play Overlay Trigger */}
                  <div
                    onClick={togglePlay}
                    className="relative z-30 flex-1 flex items-center justify-center cursor-pointer group"
                  >
                    {!isPlaying && (
                      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-black/60 text-white backdrop-blur-md border border-white/20 shadow-2xl group-hover:scale-110 transition-transform">
                        <Play className="h-7 w-7 fill-current translate-x-0.5" />
                      </div>
                    )}
                  </div>

                  {/* Bottom Video HUD */}
                  <div className="relative z-30 p-5 bg-gradient-to-t from-black/90 via-black/40 to-transparent flex flex-col gap-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="flex h-6 w-6 rounded-full bg-indigo-500/40 text-[10px] font-bold text-indigo-200 items-center justify-center border border-indigo-400/30">
                          AI
                        </span>
                        <span className="text-xs font-semibold text-white tracking-wide">
                          @vidsnap.ai
                        </span>
                      </div>

                      <button
                        onClick={toggleMute}
                        className="p-1.5 rounded-full bg-black/50 text-white/80 hover:text-white backdrop-blur-sm border border-white/10"
                      >
                        {isMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
                      </button>
                    </div>

                    <p className="text-xs text-zinc-200 line-clamp-2">
                      ✨ Auto-synchronized narration & kinetic captions with speech-driven scene timing.
                    </p>
</div>
</div>
);}
