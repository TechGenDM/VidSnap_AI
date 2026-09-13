import Link from "next/link";
import { Film, Globe, Code2 } from "lucide-react";

export default function Footer() {
  return (
    <footer className="w-full border-t border-zinc-800/60 bg-zinc-950/60 py-10 mt-auto">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-6">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-zinc-800 text-zinc-300">
            <Film className="h-4 w-4" />
          </div>
          <span className="text-sm font-semibold text-zinc-300">VidSnap AI</span>
          <span className="text-xs text-zinc-500">© 2026. Edit the story, not the timeline.</span>
        </div>

        <div className="flex items-center gap-6 text-sm text-zinc-500">
          <Link href="/create" className="hover:text-zinc-300 transition-colors">
            Quick Reel
          </Link>
          <Link href="/projects" className="hover:text-zinc-300 transition-colors">
            Projects
          </Link>
          <Link href="/templates" className="hover:text-zinc-300 transition-colors">
            Templates
          </Link>
          <Link href="/settings" className="hover:text-zinc-300 transition-colors">
            Settings
          </Link>
        </div>
      </div>
    </footer>
  );
}
