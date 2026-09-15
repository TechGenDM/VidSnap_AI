"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  FolderKanban,
  Search,
  Plus,
  Play,
  Download,
  Trash2,
  Calendar,
  CheckCircle2,
  AlertCircle,
  Film,
  Sliders,
  Sparkles,
  ArrowRight,
  Copy,
  Loader2,
} from "lucide-react";

interface ProjectItem {
  id: string;
  title: string;
  created_at: string;
  status: string;
  lifecycle_state?: string;
  duration_seconds: number;
  video_url?: string;
  thumbnail_url?: string;
  voice: string;
  music?: string;
  style: string;
  script: string;
  mode: string;
  scenes: any[];
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [duplicatingId, setDuplicatingId] = useState<string | null>(null);
  const [actionNotice, setActionNotice] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const fetchProjects = async () => {
    setIsLoading(true);
    try {
      const res = await fetch("/api/projects");
      if (res.ok) {
        const data = await res.json();
        setProjects(data);
      }
    } catch (e) {
      console.error("Failed to fetch projects", e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this project?")) return;

    try {
      const res = await fetch(`/api/projects/${id}`, { method: "DELETE" });
      if (res.ok) {
        setProjects((prev) => prev.filter((p) => p.id !== id));
      }
    } catch (err) {
      console.error("Failed to delete project", err);
    }
  };

  const handleDuplicate = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDuplicatingId(id);
    setActionNotice(null);

    try {
      const res = await fetch(`/api/projects/${id}/duplicate`, { method: "POST" });
      if (res.ok) {
        const newProj = await res.json();
        setProjects((prev) => [newProj, ...prev]);
        setActionNotice(`Created independent duplicate "${newProj.title}"`);
        setTimeout(() => setActionNotice(null), 4000);
      }
    } catch (err) {
      console.error("Failed to duplicate project", err);
    } finally {
      setDuplicatingId(null);
    }
  };

  const getLifecycleBadge = (lifecycle?: string, status?: string) => {
    const state = (lifecycle || status || "draft").toLowerCase();
    if (state === "ready" || state === "completed") {
      return { label: "Ready", color: "bg-emerald-950/80 text-emerald-400 border-emerald-500/30", icon: CheckCircle2 };
    }
    if (state === "rendering" || state === "processing") {
      return { label: "Rendering...", color: "bg-amber-950/80 text-amber-300 border-amber-500/30 animate-pulse", icon: Loader2 };
    }
    if (state === "story_ready" || state === "planned") {
      return { label: "Story Ready", color: "bg-indigo-950/80 text-indigo-300 border-indigo-500/30", icon: Sparkles };
    }
    if (state === "failed") {
      return { label: "Failed", color: "bg-rose-950/80 text-rose-400 border-rose-500/30", icon: AlertCircle };
    }
    return { label: "Draft", color: "bg-zinc-900/80 text-zinc-300 border-zinc-700/40", icon: Film };
  };

  const filteredProjects = projects.filter((p) => {
    const matchesSearch =
      p.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.script.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || p.status === statusFilter || p.lifecycle_state === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-10 w-full">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white mb-1">
            Projects
          </h1>
          <p className="text-sm text-zinc-400">
            Your library of short-form video reels and story drafts.
          </p>
        </div>

        <Link
          href="/create"
          className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 via-indigo-600 to-purple-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-cyan-500/20 hover:from-cyan-400 hover:to-indigo-500 transition-all self-start sm:self-auto active:scale-98"
        >
          <Plus className="h-4 w-4" />
          <span>New Reel</span>
        </Link>
      </div>

      {/* Action Notice Banner */}
      {actionNotice && (
        <div className="mb-6 p-3 rounded-xl bg-cyan-950/60 border border-cyan-500/40 text-cyan-200 text-xs flex items-center gap-2 animate-fadeIn">
          <CheckCircle2 className="h-4 w-4 text-cyan-400 shrink-0" />
          <span>{actionNotice}</span>
        </div>
      )}

      {/* Search & Filters */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 mb-8">
        <div className="relative max-w-md w-full">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by title or topic..."
            aria-label="Search projects"
            className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] pl-10 pr-4 py-2.5 text-sm text-white placeholder-zinc-500 focus:border-cyan-400 focus:outline-none transition-all"
          />
        </div>

        <div className="flex items-center gap-1 bg-white/[0.03] border border-white/[0.08] p-1 rounded-xl self-start sm:self-auto max-w-full overflow-x-auto">
          {["all", "ready", "story_ready", "rendering"].map((f) => (
            <button
              key={f}
              onClick={() => setStatusFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-all ${
                statusFilter === f
                  ? "bg-white/[0.1] text-white shadow-sm border border-white/[0.12]"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              {f.replace("_", " ")}
            </button>
          ))}
        </div>
      </div>

      {/* Projects Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="glass-card rounded-2xl aspect-[9/16] animate-pulse bg-white/[0.02]"
            />
          ))}
        </div>
      ) : filteredProjects.length === 0 ? (
        /* Focused Empty State */
        <div className="glass-card rounded-3xl p-16 text-center max-w-md mx-auto border-white/[0.08] shadow-2xl">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 mx-auto mb-5">
            <Film className="h-7 w-7" />
          </div>
          <h3 className="text-xl font-bold text-white mb-2">
            Your next Reel starts here.
          </h3>
          <p className="text-xs text-zinc-400 mb-8 leading-relaxed max-w-xs mx-auto">
            {searchQuery
              ? "No projects match your search query."
              : "Transform your ideas or photos into high-retention vertical videos in seconds."}
          </p>
          <Link
            href="/create"
            className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 px-6 py-3 text-sm font-bold text-white hover:from-cyan-400 hover:to-indigo-500 shadow-xl shadow-cyan-500/20 transition-all active:scale-98"
          >
            <span>Create your first Reel</span>
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      ) : (
        /* Visual-First Cards: Thumbnail Dominates */
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredProjects.map((p) => {
            const badge = getLifecycleBadge(p.lifecycle_state, p.status);
            const BadgeIcon = badge.icon;
            const dateStr = new Date(p.created_at).toLocaleDateString(undefined, {
              month: "short",
              day: "numeric",
              year: "numeric",
            });

            return (
              <div
                key={p.id}
                className="glass-card rounded-2xl overflow-hidden flex flex-col justify-between group border-white/[0.08] hover:border-cyan-500/40 transition-all"
              >
                {/* Visual Thumbnail: Dominates the Card */}
                <div className="relative aspect-[9/14] w-full bg-zinc-950 overflow-hidden">
                  {p.thumbnail_url ? (
                    <img
                      src={p.thumbnail_url}
                      alt={p.title}
                      loading="lazy"
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                  ) : (
                    <div className="w-full h-full flex flex-col items-center justify-center text-zinc-600 bg-zinc-900/60 p-4 text-center">
                      <Film className="h-10 w-10 mb-2 text-zinc-700" />
                      <span className="text-xs text-zinc-500">Storyboard Draft</span>
                    </div>
                  )}

                  {/* Duration Badge */}
                  {p.duration_seconds > 0 && (
                    <div className="absolute top-3 right-3 rounded-md bg-black/80 backdrop-blur-md px-2 py-0.5 text-[11px] font-mono font-bold text-white border border-white/10">
                      {Math.round(p.duration_seconds)}s
                    </div>
                  )}

                  {/* Canonical Lifecycle Badge */}
                  <div className="absolute top-3 left-3">
                    <span
                      className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[10px] font-bold uppercase backdrop-blur-md border ${badge.color}`}
                    >
                      <BadgeIcon className="h-3 w-3 shrink-0" />
                      <span>{badge.label}</span>
                    </span>
                  </div>

                  {/* Hover Play Button */}
                  <Link
                    href={`/projects/${p.id}`}
                    className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity backdrop-blur-[2px]"
                    aria-label={`Open editor for ${p.title}`}
                  >
                    <div className="flex h-12 w-12 items-center justify-center rounded-full bg-cyan-500 text-black font-bold shadow-xl shadow-cyan-500/40 group-hover:scale-110 transition-transform">
                      <Play className="h-5 w-5 fill-current translate-x-0.5" />
                    </div>
                  </Link>
                </div>

                {/* Primary Card Information: Title, Status, Duration, Date */}
                <div className="p-4 flex flex-col justify-between gap-3 bg-[#0a0c13]">
                  <div>
                    <h3 className="text-sm font-bold text-white truncate max-w-full group-hover:text-cyan-300 transition-colors">
                      {p.title}
                    </h3>
                    <div className="flex items-center gap-2 mt-1 text-[11px] text-zinc-500">
                      <span>{dateStr}</span>
                      <span>•</span>
                      <span className="capitalize">{p.mode} Reel</span>
                    </div>
                  </div>

                  {/* Secondary Actions */}
                  <div className="pt-2.5 border-t border-white/[0.06] flex items-center justify-between">
                    <Link
                      href={`/projects/${p.id}`}
                      className="text-xs font-semibold text-zinc-400 hover:text-white flex items-center gap-1 transition-colors"
                    >
                      <Sliders className="h-3.5 w-3.5 text-cyan-400" />
                      <span>Edit Story</span>
                    </Link>

                    <div className="flex items-center gap-1">
                      {/* Duplicate Project Action */}
                      <button
                        onClick={(e) => handleDuplicate(p.id, e)}
                        title="Duplicate as independent variant"
                        disabled={duplicatingId === p.id}
                        aria-label={`Duplicate ${p.title}`}
                        className="p-1.5 rounded-lg text-zinc-400 hover:text-cyan-300 hover:bg-cyan-500/10 transition-colors disabled:opacity-50"
                      >
                        {duplicatingId === p.id ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin text-cyan-400" />
                        ) : (
                          <Copy className="h-3.5 w-3.5" />
                        )}
                      </button>

                      {p.video_url && (
                        <a
                          href={p.video_url}
                          download={`${p.title}.mp4`}
                          title="Download MP4"
                          aria-label={`Download ${p.title} video`}
                          className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.06] transition-colors"
                        >
                          <Download className="h-3.5 w-3.5" />
                        </a>
                      )}
                      <button
                        onClick={(e) => handleDelete(p.id, e)}
                        title="Delete Reel"
                        aria-label={`Delete ${p.title}`}
                        className="p-1.5 rounded-lg text-zinc-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
