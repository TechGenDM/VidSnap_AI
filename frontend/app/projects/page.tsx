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
  Clock,
  Calendar,
  CheckCircle2,
  AlertCircle,
  Film,
  Sliders,
  Sparkles,
} from "lucide-react";

interface ProjectItem {
  id: string;
  title: string;
  created_at: string;
  status: string;
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

  const filteredProjects = projects.filter((p) => {
    const matchesSearch =
      p.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.script.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || p.status === statusFilter;
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
            All your generated Reels and story projects.
          </p>
        </div>

        <Link
          href="/create"
          className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/20 hover:from-indigo-600 hover:to-purple-700 transition-all self-start sm:self-auto"
        >
          <Plus className="h-4 w-4" />
          <span>Create Reel</span>
        </Link>
      </div>

      {/* Search & Filters */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 mb-8">
        <div className="relative max-w-md w-full">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search projects or scripts..."
            className="w-full rounded-xl border border-zinc-800 bg-zinc-900/70 pl-10 pr-4 py-2 text-sm text-white placeholder-zinc-500 focus:border-indigo-500 focus:outline-none"
          />
        </div>

        <div className="flex items-center gap-1 bg-zinc-900/70 border border-zinc-800 p-1 rounded-xl self-start sm:self-auto">
          {["all", "completed", "queued"].map((f) => (
            <button
              key={f}
              onClick={() => setStatusFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-all ${
                statusFilter === f
                  ? "bg-zinc-800 text-white shadow-sm"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Projects Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="glass-card rounded-2xl h-80 animate-pulse bg-zinc-900/30"
            />
          ))}
        </div>
      ) : filteredProjects.length === 0 ? (
        <div className="glass-card rounded-2xl p-16 text-center max-w-md mx-auto">
          <Film className="h-12 w-12 text-zinc-600 mx-auto mb-4" />
          <h3 className="text-lg font-bold text-white mb-2">No projects found</h3>
          <p className="text-sm text-zinc-400 mb-6">
            {searchQuery
              ? "Try adjusting your search terms."
              : "You haven't generated any Reels yet."}
          </p>
          <Link
            href="/create"
            className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-indigo-500 transition-colors"
          >
            <Plus className="h-4 w-4" />
            <span>Create your first Reel</span>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProjects.map((p) => {
            const isCompleted = p.status === "completed";
            const dateStr = new Date(p.created_at).toLocaleDateString(undefined, {
              month: "short",
              day: "numeric",
              year: "numeric",
            });

            return (
              <div
                key={p.id}
                className="glass-card rounded-2xl overflow-hidden flex flex-col justify-between group"
              >
                {/* Media Thumbnail Container */}
                <div className="relative aspect-[9/16] max-h-72 w-full bg-zinc-900 overflow-hidden border-b border-zinc-800/80">
                  {p.thumbnail_url ? (
                    <img
                      src={p.thumbnail_url}
                      alt={p.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                  ) : (
                    <div className="w-full h-full flex flex-col items-center justify-center text-zinc-600 bg-zinc-900">
                      <Film className="h-10 w-10 mb-2" />
                      <span className="text-xs">No thumbnail</span>
                    </div>
                  )}

                  {/* Duration Badge */}
                  {p.duration_seconds > 0 && (
                    <div className="absolute top-3 right-3 rounded-md bg-black/70 backdrop-blur-md px-2 py-0.5 text-[11px] font-mono font-bold text-white border border-white/10">
                      {p.duration_seconds}s
                    </div>
                  )}

                  {/* Mode Badge */}
                  <div className="absolute top-3 left-3 rounded-md bg-zinc-900/80 backdrop-blur-md px-2 py-0.5 text-[10px] font-bold text-zinc-300 uppercase border border-white/10">
                    {p.mode} Reel
                  </div>

                  {/* Play Overlay if Completed */}
                  {isCompleted && p.video_url && (
                    <Link
                      href={`/projects/${p.id}`}
                      className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity backdrop-blur-[2px]"
                    >
                      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-indigo-600 text-white shadow-xl shadow-indigo-600/40">
                        <Play className="h-5 w-5 fill-current translate-x-0.5" />
                      </div>
                    </Link>
                  )}
                </div>

                {/* Card Content */}
                <div className="p-5 flex flex-col flex-1 justify-between">
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <h3 className="text-base font-bold text-white truncate max-w-[200px]">
                        {p.title}
                      </h3>
                      <span
                        className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full border ${
                          isCompleted
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                            : p.status === "failed"
                            ? "bg-red-500/10 text-red-400 border-red-500/20"
                            : "bg-indigo-500/10 text-indigo-400 border-indigo-500/20"
                        }`}
                      >
                        {p.status}
                      </span>
                    </div>

                    <p className="text-xs text-zinc-400 line-clamp-2 mb-4">
                      {p.script}
                    </p>
                  </div>

                  <div className="pt-3 border-t border-zinc-800/60 flex items-center justify-between text-xs text-zinc-500">
                    <span className="flex items-center gap-1.5">
                      <Calendar className="h-3.5 w-3.5" />
                      <span>{dateStr}</span>
                    </span>

                    <div className="flex items-center gap-2">
                      {p.video_url && (
                        <a
                          href={p.video_url}
                          download={`${p.title}.mp4`}
                          title="Download MP4"
                          className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800"
                        >
                          <Download className="h-3.5 w-3.5" />
                        </a>
                      )}
                      <Link
                        href={`/projects/${p.id}`}
                        title="Edit Story"
                        className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800"
                      >
                        <Sliders className="h-3.5 w-3.5" />
                      </Link>
                      <button
                        onClick={(e) => handleDelete(p.id, e)}
                        title="Delete"
                        className="p-1.5 rounded-lg text-zinc-500 hover:text-red-400 hover:bg-red-500/10"
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
