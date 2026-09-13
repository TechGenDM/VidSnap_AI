import Link from "next/link";
import { Layers, Plus, Sparkles, ArrowRight } from "lucide-react";

export default function TemplatesPage() {
  const templates = [
    {
      id: "tech_breakdown",
      title: "Tech Breakdown",
      description: "Fast-paced educational reel with high-contrast text overlays and punchy intro hook.",
      tag: "Educational",
      duration: "30s",
    },
    {
      id: "product_showcase",
      title: "Product Showcase",
      description: "Clean aesthetic with smooth pan/zoom and ambient music for physical or digital products.",
      tag: "E-Commerce",
      duration: "15s",
    },
    {
      id: "founder_story",
      title: "Founder Journey",
      description: "Personal storytelling format with warm narrative voice and documentary pacing.",
      tag: "Storytelling",
      duration: "45s",
    },
  ];

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-10 w-full">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white mb-1">
            Templates
          </h1>
          <p className="text-sm text-zinc-400">
            Curated frameworks for high-retention short-form videos.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {templates.map((tpl) => (
          <div
            key={tpl.id}
            className="glass-card rounded-2xl p-6 flex flex-col justify-between group hover:border-indigo-500/40 transition-all"
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-bold text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-2.5 py-1 rounded-full">
                  {tpl.tag}
                </span>
                <span className="text-xs font-mono text-zinc-500">{tpl.duration}</span>
              </div>
              <h3 className="text-lg font-bold text-white mb-2">{tpl.title}</h3>
              <p className="text-xs text-zinc-400 leading-relaxed mb-6">
                {tpl.description}
              </p>
            </div>

            <Link
              href="/create?mode=quick"
              className="w-full flex items-center justify-center gap-1.5 py-2.5 rounded-xl bg-zinc-900 border border-zinc-800 hover:border-indigo-500 hover:bg-zinc-800 text-xs font-semibold text-white transition-all"
            >
              <span>Use Template</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}
