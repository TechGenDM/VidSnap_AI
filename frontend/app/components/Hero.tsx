"use client";

import Link from "next/link";
import { Sparkles, ArrowRight, Play, Zap, BookOpen, Rocket, Mic } from "lucide-react";

interface HeroProps {
  onWatchDemo?: () => void;
}

export default function Hero({ onWatchDemo }: HeroProps) {
  const starterTopics = [
    {
      title: "Vector Databases",
      icon: Zap,
      href: "/create?prompt=How%20Vector%20Databases%20Actually%20Work&preset=tech_creator",
    },
    {
      title: "Feynman Technique",
      icon: BookOpen,
      href: "/create?prompt=The%20Feynman%20Technique%20for%20Rapid%20Learning&preset=educational",
    },
    {
      title: "Startup Distribution",
      icon: Rocket,
      href: "/create?prompt=Why%2090%25%20of%20Startups%20Fail%20at%20Distribution&preset=product_showcase",
    },
    {
      title: "Creator Burnout",
      icon: Mic,
      href: "/create?prompt=What%20Nobody%20Tells%20You%20About%20Creative%20Burnout&preset=personal_story",
    },
  ];

  return (
    <div className="flex flex-col items-start text-left w-full">
      {/* Eyebrow Badge */}
      <div className="inline-flex items-center gap-2 rounded-full border border-purple-500/30 bg-purple-500/10 px-3.5 py-1 text-xs font-semibold text-purple-300 mb-6 shadow-sm shadow-purple-500/10">
        <Sparkles className="h-3.5 w-3.5 text-purple-400 animate-pulse" />
        <span>Turn Ideas Into Reels</span>
      </div>

      {/* Hero Headline */}
      <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold tracking-tight text-white leading-[1.08] mb-6">
        From raw idea <br className="hidden sm:inline" />
        to{" "}
        <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-400 to-indigo-300">
          scroll-stopping Reel.
        </span>
      </h1>

      {/* Subheadline */}
      <p className="text-base sm:text-lg lg:text-xl text-zinc-300 max-w-2xl mb-8 leading-relaxed">
        Turn an idea, note, or script into a polished short-form video with AI-written stories, matched visuals,
        voice, and captions.
      </p>

      {/* Capability Signals */}
      <div className="flex flex-wrap items-center gap-4 sm:gap-6 text-xs sm:text-sm font-medium text-zinc-300 mb-8">
        <div className="flex items-center gap-1.5">
          <span className="text-purple-400">⚡</span>
          <span>AI-Powered</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-pink-400">✦</span>
          <span>Story-First Editing</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-indigo-400">♥</span>
          <span>Built for Creators</span>
        </div>
      </div>

      {/* Dual CTAs */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3.5 w-full sm:w-auto mb-5">
        <Link
          href="/create"
          className="flex items-center justify-center gap-2.5 rounded-xl bg-gradient-to-r from-purple-500 via-indigo-600 to-pink-500 px-7 py-3.5 text-base font-semibold text-white shadow-xl shadow-purple-500/25 hover:from-purple-400 hover:to-pink-400 hover:shadow-purple-500/40 transition-all active:scale-98"
        >
          <span>Start Creating Free</span>
          <ArrowRight className="h-4 w-4" />
        </Link>

        <button
          onClick={onWatchDemo}
          className="flex items-center justify-center gap-2 rounded-xl border border-white/[0.12] bg-white/[0.04] px-6 py-3.5 text-base font-medium text-zinc-200 hover:bg-white/[0.08] hover:text-white hover:border-purple-500/40 transition-all"
        >
          <Play className="h-4 w-4 fill-current text-purple-400" />
          <span>Watch Demo</span>
        </button>
      </div>

      {/* Truthful Assurance Text */}
      <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-xs text-zinc-400 mb-9">
        <span>No credit card required</span>
        <span className="text-zinc-600">•</span>
        <span>Instant browser preview</span>
        <span className="text-zinc-600">•</span>
        <span>Ready-to-share 1080×1920 MP4</span>
      </div>

      {/* 1-Click Starter Topics */}
      <div className="w-full max-w-xl pt-4 border-t border-white/[0.08]">
        <span className="block text-[11px] font-semibold text-zinc-400 uppercase tracking-wider mb-2.5">
          ⚡ 1-Click Topics to Jump Into Studio:
        </span>
        <div className="flex flex-wrap gap-2">
          {starterTopics.map((topic) => {
            const Icon = topic.icon;
            return (
              <Link
                key={topic.title}
                href={topic.href}
                className="inline-flex items-center gap-1.5 text-xs text-zinc-300 hover:text-white bg-white/[0.04] hover:bg-purple-950/40 border border-white/[0.08] hover:border-purple-500/50 rounded-lg px-3 py-1.5 transition-all shadow-sm"
              >
                <Icon className="h-3 w-3 text-purple-400" />
                <span>{topic.title}</span>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
