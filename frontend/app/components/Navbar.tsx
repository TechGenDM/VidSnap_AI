"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Sparkles, Film, Settings, Menu, X, Plus } from "lucide-react";

export default function Navbar() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { href: "/create", label: "Studio" },
    { href: "/templates", label: "Templates" },
    { href: "/projects", label: "Projects" },
    { href: "/#why-vidsnap", label: "Features" },
    { href: "/#how-it-works", label: "How It Works" },
    { href: "/settings", label: "Engine" },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-white/[0.08] bg-[#07080b]/90 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-3 sm:px-6 lg:px-8">
        {/* Left: Logo + STUDIO Badge */}
        <Link
          href="/"
          className="flex items-center gap-2 group focus-visible:ring-2 focus-visible:ring-purple-400 rounded-xl shrink-0"
          aria-label="VidSnap AI Home"
        >
          <div className="flex h-8 w-8 sm:h-9 sm:w-9 items-center justify-center rounded-xl bg-gradient-to-br from-purple-500 via-indigo-600 to-pink-500 text-white shadow-md shadow-purple-500/25 group-hover:scale-105 transition-transform">
            <Film className="h-4 w-4 sm:h-5 sm:w-5" />
          </div>
          <div className="flex items-center gap-1.5 sm:gap-2">
            <span className="text-base sm:text-lg font-extrabold tracking-tight text-white">VidSnap</span>
            <span className="hidden min-[360px]:inline-block rounded-md bg-purple-500/15 px-1.5 sm:px-2 py-0.5 text-[9px] sm:text-[10px] font-bold tracking-wider text-purple-300 border border-purple-500/30 uppercase">
              STUDIO
            </span>
          </div>
        </Link>

        {/* Center: Desktop Navigation Links */}
        <nav className="hidden lg:flex items-center gap-1 xl:gap-2" aria-label="Main Navigation">
          {navLinks.map((link) => {
            const isInternalPage = link.href.startsWith("/") && !link.href.includes("#");
            const isActive = isInternalPage && (pathname === link.href || (link.href !== "/" && pathname.startsWith(`${link.href}/`)));
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all ${
                  isActive
                    ? "bg-white/[0.08] text-white border border-white/[0.12] shadow-sm"
                    : "text-zinc-400 hover:text-white hover:bg-white/[0.04]"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        {/* Right: Action CTAs */}
        <div className="flex items-center gap-1.5 sm:gap-3 shrink-0">
          <Link
            href="/settings"
            className="hidden sm:flex h-9 w-9 items-center justify-center rounded-xl border border-white/[0.08] bg-white/[0.03] text-zinc-400 hover:text-white hover:border-purple-500/40 hover:bg-purple-500/10 transition-all"
            title="Engine Settings"
            aria-label="Engine Settings"
          >
            <Settings className="h-4 w-4" />
          </Link>

          <Link
            href="/create"
            title="Create New Reel"
            className="flex items-center gap-1.5 sm:gap-2 rounded-xl bg-gradient-to-r from-purple-500 via-indigo-600 to-pink-500 px-3 sm:px-4 py-2 text-xs sm:text-sm font-semibold text-white shadow-lg shadow-purple-500/25 hover:from-purple-400 hover:to-pink-400 hover:shadow-purple-500/40 transition-all active:scale-98"
          >
            <Sparkles className="h-4 w-4 shrink-0" />
            <span className="hidden min-[380px]:inline">New Reel</span>
            <span className="min-[380px]:hidden">New</span>
          </Link>

          {/* Mobile Menu Toggle Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden flex h-9 w-9 items-center justify-center rounded-xl border border-white/[0.08] bg-white/[0.03] text-zinc-400 hover:text-white hover:bg-white/[0.08] transition-colors"
            aria-label="Toggle Mobile Navigation Menu"
            aria-expanded={mobileMenuOpen}
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-t border-white/[0.08] bg-[#07080b]/98 px-4 pt-3 pb-5 backdrop-blur-2xl">
          <nav className="flex flex-col gap-1.5" aria-label="Mobile Navigation">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium text-zinc-300 hover:text-white hover:bg-white/[0.06] transition-colors"
              >
                <span>{link.label}</span>
              </Link>
            ))}
            <div className="pt-2 border-t border-white/[0.08] mt-2">
              <Link
                href="/create"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center justify-center gap-2 w-full py-2.5 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-sm font-bold text-white shadow-md shadow-purple-500/25"
              >
                <Plus className="h-4 w-4" />
                <span>Open Studio</span>
              </Link>
            </div>
          </nav>
        </div>
      )}
    </header>
  );
}
