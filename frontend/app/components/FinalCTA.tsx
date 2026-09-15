import Link from "next/link";
import { Sparkles, ArrowRight } from "lucide-react";

export default function FinalCTA() {
  return (
    <section className="w-full py-20 sm:py-28 relative overflow-hidden">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="relative rounded-3xl p-8 sm:p-14 lg:p-16 border border-purple-500/30 bg-gradient-to-b from-[#111424] to-[#07080b] shadow-2xl shadow-purple-950/40 text-center overflow-hidden">
          {/* Ambient Glow in Card */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-96 bg-gradient-to-br from-purple-600/25 to-pink-600/20 rounded-full blur-[100px] pointer-events-none" />

          {/* Eyebrow Badge */}
          <div className="inline-flex items-center gap-1.5 rounded-full border border-purple-500/30 bg-purple-500/10 px-3.5 py-1 text-xs font-bold uppercase tracking-wider text-purple-300 mb-6">
            <Sparkles className="h-3.5 w-3.5 text-purple-400" />
            <span>Ready to Create?</span>
          </div>

          {/* Headline */}
          <h2 className="text-3xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white mb-5 leading-tight">
            Your next Reel starts with one idea.
          </h2>

          {/* Supporting Subline */}
          <p className="text-base sm:text-xl text-zinc-300 max-w-xl mx-auto mb-10 leading-relaxed">
            Turn what you know into something worth watching. No timeline editing required.
          </p>

          {/* Primary CTA Button */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/create"
              className="inline-flex items-center gap-2.5 rounded-2xl bg-gradient-to-r from-purple-500 via-indigo-600 to-pink-500 px-8 py-4 text-base sm:text-lg font-bold text-white shadow-xl shadow-purple-500/30 hover:from-purple-400 hover:to-pink-400 hover:shadow-purple-500/50 transition-all active:scale-98"
            >
              <span>Start Creating Free</span>
              <ArrowRight className="h-5 w-5" />
            </Link>
          </div>

          {/* Handwritten Style Motto */}
          <div className="mt-8 flex items-center justify-center gap-2 text-xs font-mono text-purple-300/80">
            <span>Create</span>
            <span>•</span>
            <span>Share</span>
            <span>•</span>
            <span>Grow ✦</span>
          </div>
        </div>
      </div>
    </section>
  );
}
