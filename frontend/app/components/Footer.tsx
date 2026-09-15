import Link from "next/link";
import { Film, Sparkles } from "lucide-react";

export default function Footer() {
  return (
    <footer className="w-full border-t border-white/[0.08] bg-[#050608] py-14 sm:py-16 mt-auto">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10 pb-12 border-b border-white/[0.08]">
          {/* Col 1: Brand & Philosophy */}
          <div className="md:col-span-1 flex flex-col items-start gap-4">
            <Link href="/" className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-purple-500 via-indigo-600 to-pink-500 text-white shadow-md shadow-purple-500/20">
                <Film className="h-4 w-4" />
              </div>
              <span className="text-base font-extrabold text-white">VidSnap AI</span>
              <span className="rounded-md bg-purple-500/10 px-1.5 py-0.5 text-[9px] font-bold text-purple-300 border border-purple-500/20 uppercase">
                STUDIO
              </span>
            </Link>
            <p className="text-xs text-zinc-400 leading-relaxed max-w-xs">
              Turn raw ideas into polished short-form Reels. VidSnap edits the story, not the timeline.
            </p>
            <div className="flex items-center gap-3 pt-1">
              <a
                href="https://github.com/TechGenDM/VidSnap_AI"
                target="_blank"
                rel="noreferrer"
                className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/[0.04] hover:bg-white/[0.08] text-zinc-400 hover:text-white border border-white/[0.08] transition-colors"
                aria-label="GitHub Repository"
              >
                <svg className="h-4 w-4 fill-current" viewBox="0 0 24 24">
                  <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
                </svg>
              </a>
            </div>
          </div>

          {/* Col 2: Studio & Product */}
          <div className="flex flex-col gap-3">
            <span className="text-xs font-bold uppercase tracking-wider text-zinc-300">
              Product
            </span>
            <div className="flex flex-col gap-2 text-xs text-zinc-400">
              <Link href="/create" className="hover:text-purple-300 transition-colors">
                AI Story Studio
              </Link>
              <Link href="/create?mode=quick" className="hover:text-purple-300 transition-colors">
                Quick Reel
              </Link>
              <Link href="/templates" className="hover:text-purple-300 transition-colors">
                Templates Gallery
              </Link>
              <Link href="/projects" className="hover:text-purple-300 transition-colors">
                Creator Projects
              </Link>
            </div>
          </div>

          {/* Col 3: Engine & Settings */}
          <div className="flex flex-col gap-3">
            <span className="text-xs font-bold uppercase tracking-wider text-zinc-300">
              Capabilities
            </span>
            <div className="flex flex-col gap-2 text-xs text-zinc-400">
              <Link href="/#why-vidsnap" className="hover:text-purple-300 transition-colors">
                AI Script Generation
              </Link>
              <Link href="/#story-editor" className="hover:text-purple-300 transition-colors">
                Ask VidSnap Creative Refinement
              </Link>
              <Link href="/#how-it-works" className="hover:text-purple-300 transition-colors">
                Speech-Synced Captions
              </Link>
              <Link href="/settings" className="hover:text-purple-300 transition-colors">
                Engine Diagnostics
              </Link>
            </div>
          </div>

          {/* Col 4: Creator Focus */}
          <div className="flex flex-col gap-3">
            <span className="text-xs font-bold uppercase tracking-wider text-zinc-300">
              Short-Form Studio
            </span>
            <div className="flex flex-col gap-2 text-xs text-zinc-400">
              <span className="text-zinc-500">YouTube Shorts 1080×1920</span>
              <span className="text-zinc-500">Instagram Reels 9:16</span>
              <span className="text-zinc-500">TikTok Fast-Paced Video</span>
              <div className="pt-2">
                <Link
                  href="/create"
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-purple-400 hover:text-purple-300 transition-colors"
                >
                  <Sparkles className="h-3 w-3" />
                  <span>Start Creating Free</span>
                </Link>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Copyright & Guarantee */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-zinc-500">
          <div>
            <span>© 2026 VidSnap AI. All rights reserved.</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-zinc-400">Made with ♥ for short-form creators.</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
