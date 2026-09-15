import Link from "next/link";
import { ArrowRight, Sparkles } from "lucide-react";

export default function TemplateGallery() {
  const templates = [
    {
      id: "tech_creator",
      title: "Tech Explainer",
      badge: "Cinematic",
      displayTitle: "Tech Made Simple.",
      duration: "30s",
      bgGradient: "from-blue-900/60 via-purple-900/40 to-black",
      coverImage: "/media/templates/1.jpg",
      presetParam: "tech_creator",
    },
    {
      id: "personal_story",
      title: "Motivational",
      badge: "Personal",
      displayTitle: "Better You Everyday",
      duration: "30s",
      bgGradient: "from-indigo-900/60 via-slate-900/40 to-black",
      coverImage: "/media/templates/2.jpg",
      presetParam: "personal_story",
    },
    {
      id: "product_showcase",
      title: "Product Demo",
      badge: "Launch",
      displayTitle: "Ideas into Impact",
      duration: "20s",
      bgGradient: "from-pink-900/60 via-purple-900/40 to-black",
      coverImage: "/media/templates/3.jpg",
      presetParam: "product_showcase",
    },
    {
      id: "educational",
      title: "Educational",
      badge: "Concept",
      displayTitle: "Learn Grow Repeat",
      duration: "30s",
      bgGradient: "from-emerald-900/60 via-teal-900/40 to-black",
      coverImage: "/media/templates/4.jpg",
      presetParam: "educational",
    },
    {
      id: "news_update",
      title: "News Update",
      badge: "Fast Breakdown",
      displayTitle: "What's Happening Today?",
      duration: "30s",
      bgGradient: "from-sky-900/60 via-indigo-900/40 to-black",
      coverImage: "/media/templates/5.jpg",
      presetParam: "tech_creator",
    },
    {
      id: "quote_reel",
      title: "Quote Reel",
      badge: "Reflective",
      displayTitle: "One Small Step",
      duration: "15s",
      bgGradient: "from-amber-900/60 via-orange-900/40 to-black",
      coverImage: "/media/templates/1.jpg",
      presetParam: "storytelling",
    },
  ];

  return (
    <section id="templates" className="w-full py-20 sm:py-28 border-t border-white/[0.06] bg-[#07080b]">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Header with Browse Link */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-14">
          <div>
            <div className="inline-flex items-center gap-1.5 rounded-full border border-purple-500/30 bg-purple-500/10 px-3 py-1 text-xs font-bold uppercase tracking-wider text-purple-300 mb-4">
              <Sparkles className="h-3.5 w-3.5 text-purple-400" />
              <span>Popular Templates</span>
            </div>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-white mb-2">
              Ready-to-use templates for every idea.
            </h2>
            <p className="text-base sm:text-lg text-zinc-400">
              Choose a style, drop your content, and let AI do the rest.
            </p>
          </div>

          <Link
            href="/templates"
            className="inline-flex items-center gap-2 text-sm font-bold text-purple-400 hover:text-purple-300 transition-colors self-start md:self-auto group shrink-0"
          >
            <span>Browse All Templates</span>
            <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>

        {/* 6 Template Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 sm:gap-5">
          {templates.map((tpl) => (
            <Link
              key={tpl.id}
              href={`/create?preset=${tpl.presetParam}`}
              className="group relative rounded-2xl overflow-hidden aspect-[9/16] bg-zinc-900 border border-white/[0.08] hover:border-purple-500/50 transition-all duration-300 shadow-xl hover:-translate-y-1 hover:shadow-purple-500/10 flex flex-col justify-between p-4"
            >
              {/* Background Image with Ambient Gradient Overlay */}
              <div
                className="absolute inset-0 bg-cover bg-center transition-transform duration-500 group-hover:scale-105"
                style={{ backgroundImage: `url(${tpl.coverImage})` }}
              />
              <div className={`absolute inset-0 bg-gradient-to-t ${tpl.bgGradient} opacity-90 group-hover:opacity-80 transition-opacity`} />
              <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-transparent to-black/90" />

              {/* Top Tag & Duration */}
              <div className="relative z-20 flex items-center justify-between text-[10px]">
                <span className="px-2 py-0.5 rounded-md bg-black/60 backdrop-blur-md border border-white/10 text-zinc-200 font-semibold">
                  {tpl.badge}
                </span>
                <span className="font-mono text-zinc-400 font-semibold">{tpl.duration}</span>
              </div>

              {/* Center Catchphrase */}
              <div className="relative z-20 text-center my-auto px-1">
                <p className="text-sm sm:text-base font-black uppercase text-white leading-snug drop-shadow-lg tracking-wide group-hover:text-purple-200 transition-colors">
                  {tpl.displayTitle}
                </p>
              </div>

              {/* Bottom Label & Hover Indicator */}
              <div className="relative z-20 pt-2 border-t border-white/10 flex items-center justify-between">
                <span className="text-xs font-bold text-zinc-200 truncate">
                  {tpl.title}
                </span>
                <ArrowRight className="h-3 w-3 text-purple-400 group-hover:translate-x-0.5 transition-transform" />
              </div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
