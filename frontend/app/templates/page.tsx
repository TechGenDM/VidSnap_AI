import Link from "next/link";
import { Layers, Sparkles, ArrowRight } from "lucide-react";

export default function TemplatesPage() {
  const templates = [
    {
      id: "tech_breakdown",
      title: "Tech Breakdown",
      description: "Fast-paced educational reel with high-contrast text overlays and punchy intro hook.",
      tag: "Educational",
      duration: "30s",
      style: "Cinematic",
    },
    {
      id: "product_showcase",
      title: "Product Showcase",
      description: "Clean aesthetic with smooth pan/zoom and ambient music for physical or digital products.",
      tag: "Showcase",
      duration: "15s",
      style: "Clean Dynamic",
    },
    {
      id: "founder_story",
      title: "Founder Journey",
      description: "Personal storytelling format with warm narrative voice and documentary pacing.",
      tag: "Storytelling",
      duration: "45s",
      style: "Documentary",
    },
  ];

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-10 w-full">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold uppercase tracking-wider text-cyan-400 font-mono">
              Curated Presets
            </span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white mb-1">
            Studio Templates
          </h1>
          <p className="text-sm text-zinc-400">
            High-retention creative frameworks calibrated for vertical video.
          </p>
        </div>

        <Link
          href="/create"
          className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 via-indigo-600 to-purple-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-cyan-500/20 hover:from-cyan-400 hover:to-indigo-500 transition-all self-start sm:self-auto active:scale-98"
        >
          <Sparkles className="h-4 w-4" />
          <span>New Custom Reel</span>
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {templates.map((tpl) => (
          <div
            key={tpl.id}
            className="glass-card rounded-2xl p-6 flex flex-col justify-between group border-white/[0.08] hover:border-cyan-500/40 transition-all shadow-xl"
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-bold text-cyan-400 bg-cyan-500/10 border border-cyan-500/25 px-2.5 py-1 rounded-full">
                  {tpl.tag}
                </span>
                <span className="text-xs font-mono text-zinc-500">{tpl.duration}</span>
              </div>
              <h3 className="text-lg font-bold text-white mb-2 group-hover:text-cyan-300 transition-colors">
                {tpl.title}
              </h3>
              <p className="text-xs text-zinc-400 leading-relaxed mb-6">
                {tpl.description}
              </p>
            </div>

            <Link
              href={`/create?mode=quick&template=${tpl.id}`}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-white/[0.03] border border-white/[0.1] hover:border-cyan-500/50 hover:bg-cyan-500/10 text-xs font-bold text-white transition-all group-hover:shadow-md"
            >
              <span>Use Template in Studio</span>
              <ArrowRight className="h-3.5 w-3.5 text-cyan-400" />
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}
