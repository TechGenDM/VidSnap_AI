"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Sparkles, Film, FolderKanban, Layers, Plus, Settings } from "lucide-react";

export default function Navbar() {
  const pathname = usePathname();

  const navLinks = [
    { href: "/create", label: "Studio", icon: Plus },
    { href: "/projects", label: "Projects", icon: FolderKanban },
    { href: "/templates", label: "Templates", icon: Layers },
    { href: "/settings", label: "Engine", icon: Settings },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-white/[0.07] bg-[#07080b]/85 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-3 group focus-visible:ring-2 focus-visible:ring-cyan-400 rounded-xl" aria-label="VidSnap AI Home">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500 via-indigo-600 to-purple-600 text-white shadow-md shadow-cyan-500/20 group-hover:scale-105 transition-transform">
            <Film className="h-5 w-5" />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold tracking-tight text-white">VidSnap</span>
            <span className="rounded-md bg-cyan-500/10 px-1.5 py-0.5 text-[10px] font-bold tracking-wider text-cyan-300 border border-cyan-500/25 uppercase">STUDIO</span>
          </div>
        </Link>

        {/* Navigation Links */}
        <nav className="flex items-center gap-1 sm:gap-2" aria-label="Main Navigation">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive = pathname === link.href || (link.href !== "/" && pathname.startsWith(`${link.href}/`));
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`flex items-center gap-1.5 px-3 sm:px-3.5 py-1.5 sm:py-2 rounded-lg text-xs sm:text-sm font-medium transition-all ${
                  isActive
                    ? "bg-white/[0.08] text-white border border-white/[0.12] shadow-sm shadow-cyan-500/10"
                    : "text-zinc-400 hover:text-white hover:bg-white/[0.04]"
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{link.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Right CTA */}
        <div className="flex items-center gap-3">
          <Link
            href="/create"
            className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 via-indigo-600 to-purple-600 px-3.5 sm:px-4 py-2 text-xs sm:text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 hover:from-cyan-400 hover:to-purple-500 hover:shadow-cyan-500/30 transition-all active:scale-98"
          >
            <Sparkles className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
            <span className="hidden xs:inline">New Reel</span>
            <span className="xs:hidden">New</span>
          </Link>
        </div>
      </div>
    </header>
  );
}
