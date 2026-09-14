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
                <span>Idea-to-Explainer Video Studio</span>
              </div>

              <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-white leading-[1.08] mb-6">
                From raw idea <br className="hidden sm:inline" />
                to <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-300 to-pink-400">high-retention Reel.</span>
              </h1>

              <p className="text-lg sm:text-xl text-zinc-400 max-w-2xl mb-8 leading-relaxed">
                VidSnap helps solo creators, technical builders, and educators create short-form explainers{" "}
                <span className="text-zinc-200 font-medium">significantly faster than manual timeline editors like CapCut.</span>
              </p>

              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 w-full sm:w-auto mb-6">
                <Link
                  href="/create"
                  className="flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 px-7 py-3.5 text-base font-semibold text-white shadow-xl shadow-indigo-500/25 hover:from-indigo-600 hover:to-purple-700 hover:shadow-indigo-500/40 transition-all active:scale-98"
                >
                  <Zap className="h-5 w-5" />
                  <span>Start Creating Free</span>
                  <ArrowRight className="h-4 w-4 ml-1" />
                </Link>

                <a
                  href="#how-it-works"
                  className="flex items-center justify-center gap-2 rounded-xl border border-zinc-800 bg-zinc-900/60 px-6 py-3.5 text-base font-medium text-zinc-300 hover:bg-zinc-850 hover:text-white hover:border-zinc-700 transition-all"
                >
                  <span>See how it works</span>
                </a>
              </div>

              {/* 1-Click Starter Prompts for immediate creator activation */}
              <div className="w-full max-w-xl">
                <span className="block text-[11px] font-medium text-zinc-400 uppercase tracking-wider mb-2.5">
                  ⚡ 1-Click Starter Topics (Jump directly into studio):
                </span>
                <div className="flex flex-wrap gap-2">
                  <Link
                    href="/create?prompt=How%20Vector%20Databases%20Actually%20Work&preset=tech_creator"
                    className="inline-flex items-center gap-1.5 text-xs text-zinc-300 hover:text-white bg-zinc-900/80 hover:bg-indigo-950/40 border border-zinc-800 hover:border-indigo-500/50 rounded-lg px-3 py-1.5 transition-all"
                  >
                    <span>⚡ Vector Databases</span>
                  </Link>
                  <Link
                    href="/create?prompt=The%20Feynman%20Technique%20for%20Rapid%20Learning&preset=educational"
                    className="inline-flex items-center gap-1.5 text-xs text-zinc-300 hover:text-white bg-zinc-900/80 hover:bg-indigo-950/40 border border-zinc-800 hover:border-indigo-500/50 rounded-lg px-3 py-1.5 transition-all"
                  >
                    <span>🎓 Feynman Technique</span>
                  </Link>
                  <Link
                    href="/create?prompt=Why%2090%25%20of%20Startups%20Fail%20at%20Distribution&preset=product_showcase"
                    className="inline-flex items-center gap-1.5 text-xs text-zinc-300 hover:text-white bg-zinc-900/80 hover:bg-indigo-950/40 border border-zinc-800 hover:border-indigo-500/50 rounded-lg px-3 py-1.5 transition-all"
                  >
                    <span>🚀 Startup Distribution</span>
                  </Link>
                  <Link
                    href="/create?prompt=What%20Nobody%20Tells%20You%20About%20Creative%20Burnout&preset=personal_story"
                    className="inline-flex items-center gap-1.5 text-xs text-zinc-300 hover:text-white bg-zinc-900/80 hover:bg-indigo-950/40 border border-zinc-800 hover:border-indigo-500/50 rounded-lg px-3 py-1.5 transition-all"
                  >
                    <span>🎙️ Creator Burnout</span>
                  </Link>
                </div>
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

                    <div className="flex items-center justify-between text-[10px] text-zinc-400 pt-1 border-t border-white/10">
                      <span className="flex items-center gap-1">
                        <Wand2 className="h-3 w-3 text-indigo-400" />
                        <span>Voice: Adam (ElevenLabs)</span>
                      </span>
                      <span>Music: Ambient Chill</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Process Section (#how-it-works) */}
      <section id="how-it-works" className="w-full py-24 border-t border-zinc-850 bg-zinc-950">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-xs font-bold uppercase tracking-widest text-indigo-400 mb-3">
              How It Works
            </h2>
            <h3 className="text-3xl sm:text-4xl font-bold tracking-tight text-white mb-4">
              From thought to finished video in 4 steps
            </h3>
            <p className="text-zinc-400 text-base sm:text-lg">
              VidSnap replaces hours of timeline slicing with intelligent audio-visual story composition.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                step: "01",
                title: "Tell VidSnap",
                description: "Type an idea, paste a script, or drop your existing photos.",
                icon: Zap,
              },
              {
                step: "02",
                title: "AI Builds the Story",
                description: "The engine structures your hook, timing, and scene breakdown.",
                icon: Bot,
              },
              {
                step: "03",
                title: "VidSnap Renders It",
                description: "ElevenLabs voice narration, kinetic captions, and music ducking.",
                icon: Wand2,
              },
              {
                step: "04",
                title: "Publish",
                description: "Download a ready-to-share 1080×1920 MP4 for Reels, Shorts, and TikTok.",
                icon: Share2,
              },
            ].map((item) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.step}
                  className="glass-card rounded-2xl p-6 flex flex-col justify-between group"
                >
                  <div>
                    <div className="flex items-center justify-between mb-6">
                      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 group-hover:scale-105 transition-transform">
                        <Icon className="h-6 w-6" />
                      </div>
                      <span className="text-2xl font-mono font-bold text-zinc-700 group-hover:text-indigo-400/50 transition-colors">
                        {item.step}
                      </span>
                    </div>
                    <h4 className="text-lg font-bold text-white mb-2">{item.title}</h4>
                    <p className="text-sm text-zinc-400 leading-relaxed">{item.description}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Creation Modes Preview Section */}
      <section className="w-full py-24 border-t border-zinc-850 bg-zinc-900/30">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h3 className="text-3xl font-bold tracking-tight text-white mb-4">
              Three Creation Modes. Zero Timelines.
            </h3>
            <p className="text-zinc-400 text-base">
              Choose the workflow that matches where you are starting from.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Quick Reel */}
            <div className="glass-card rounded-2xl p-7 border-indigo-500/30 relative flex flex-col justify-between">
              <div className="absolute top-4 right-4 rounded-full bg-indigo-500/20 px-2.5 py-0.5 text-[10px] font-bold text-indigo-300 border border-indigo-500/30">
                ACTIVE
              </div>
              <div>
                <div className="h-10 w-10 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center mb-5">
                  <Zap className="h-5 w-5" />
                </div>
                <h4 className="text-xl font-bold text-white mb-2">Quick Reel</h4>
                <p className="text-sm text-zinc-400 mb-6 leading-relaxed">
                  I have my own photos or visual assets. Drop in images, write a script, pick a voice, and render in seconds.
                </p>
                <ul className="space-y-2.5 text-xs text-zinc-300 mb-8">
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                    <span>Multi-image drag & drop with reordering</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                    <span>Dynamic speech-driven slide timing</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                    <span>Blurred background 9:16 portrait framing</span>
                  </li>
                </ul>
              </div>
              <Link
                href="/create?mode=quick"
                className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-center text-sm font-semibold transition-colors flex items-center justify-center gap-1.5"
              >
                <span>Launch Quick Reel</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>

            {/* AI Reel */}
            <div className="glass-card rounded-2xl p-7 flex flex-col justify-between">
              <div>
                <div className="h-10 w-10 rounded-lg bg-purple-500/20 text-purple-400 flex items-center justify-center mb-5">
                  <Bot className="h-5 w-5" />
                </div>
                <h4 className="text-xl font-bold text-white mb-2">AI Reel</h4>
                <p className="text-sm text-zinc-400 mb-6 leading-relaxed">
                  I have an idea. Prompt VidSnap with a topic and audience to generate structured hooks, scenes, and narration.
                </p>
                <ul className="space-y-2.5 text-xs text-zinc-300 mb-8">
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-purple-400" />
                    <span>Idea to hook & script decomposition</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-purple-400" />
                    <span>Audience and tone tuning</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-purple-400" />
                    <span>Automatic scene scheduling</span>
                  </li>
                </ul>
              </div>
              <Link
                href="/create?mode=ai"
                className="w-full py-2.5 rounded-lg border border-zinc-700 bg-zinc-800 hover:bg-zinc-750 text-white text-center text-sm font-semibold transition-colors flex items-center justify-center gap-1.5"
              >
                <span>Try AI Reel</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>

            {/* Repurpose */}
            <div className="glass-card rounded-2xl p-7 flex flex-col justify-between opacity-80 border-dashed">
              <div>
                <div className="h-10 w-10 rounded-lg bg-zinc-800 text-zinc-400 flex items-center justify-center mb-5">
                  <Repeat className="h-5 w-5" />
                </div>
                <div className="flex items-center gap-2 mb-2">
                  <h4 className="text-xl font-bold text-white">Repurpose</h4>
                  <span className="text-[10px] font-bold text-zinc-500 bg-zinc-800 px-2 py-0.5 rounded">ROADMAP</span>
                </div>
                <p className="text-sm text-zinc-400 mb-6 leading-relaxed">
                  I already have long-form content. Paste a YouTube URL, article, or podcast to extract viral vertical highlights.
                </p>
                <ul className="space-y-2.5 text-xs text-zinc-500 mb-8">
                  <li className="flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-zinc-600" />
                    <span>Highlight extraction</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-zinc-600" />
                    <span>Automatic 9:16 smart crop</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-zinc-600" />
                    <span>Multi-format social export</span>
                  </li>
                </ul>
              </div>
              <button
                disabled
                className="w-full py-2.5 rounded-lg border border-zinc-850 bg-zinc-900 text-zinc-500 text-center text-sm font-semibold cursor-not-allowed"
              >
                Coming in Phase 2
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Bottom CTA Banner */}
      <section className="w-full py-20 border-t border-zinc-850 bg-gradient-to-b from-zinc-950 to-zinc-900 text-center">
        <div className="mx-auto max-w-4xl px-4 sm:px-6">
          <h3 className="text-3xl sm:text-4xl font-extrabold text-white mb-4">
            Ready to create your first Reel?
          </h3>
          <p className="text-zinc-400 text-base max-w-xl mx-auto mb-8">
            No video editing background required. Turn your photos and ideas into high-engagement vertical content now.
          </p>
          <Link
            href="/create"
            className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 px-8 py-4 text-base font-bold text-white shadow-xl shadow-indigo-500/30 hover:from-indigo-600 hover:to-purple-700 transition-all active:scale-98"
          >
            <Zap className="h-5 w-5" />
            <span>Launch Reel Creator</span>
            <ArrowRight className="h-4 w-4 ml-1" />
          </Link>
        </div>
      </section>
    </div>
  );
}
