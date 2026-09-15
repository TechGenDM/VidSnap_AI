import { FileText, Wand2, Sliders, Upload } from "lucide-react";

export default function HowItWorks() {
  const steps = [
    {
      number: "01",
      title: "Tell VidSnap your idea",
      description: "Type a topic, paste a script, or start from a creator preset.",
      icon: FileText,
      badgeColor: "bg-purple-500 text-white shadow-purple-500/30",
      iconColor: "text-purple-400 bg-purple-500/10 border-purple-500/20",
    },
    {
      number: "02",
      title: "AI creates the story",
      description: "VidSnap creates hook, scenes, narration, visuals, and captions.",
      icon: Wand2,
      badgeColor: "bg-pink-500 text-white shadow-pink-500/30",
      iconColor: "text-pink-400 bg-pink-500/10 border-pink-500/20",
    },
    {
      number: "03",
      title: "Preview & customize",
      description: "Edit scenes, change hooks, replace visuals, or ask VidSnap to revise.",
      icon: Sliders,
      badgeColor: "bg-blue-500 text-white shadow-blue-500/30",
      iconColor: "text-blue-400 bg-blue-500/10 border-blue-500/20",
    },
    {
      number: "04",
      title: "Export & share",
      description: "Generate the final 1080×1920 Reel ready for publishing.",
      icon: Upload,
      badgeColor: "bg-emerald-500 text-white shadow-emerald-500/30",
      iconColor: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    },
  ];

  return (
    <section id="how-it-works" className="w-full py-20 sm:py-28 border-t border-white/[0.06] bg-[#07080b] relative">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-2xl mx-auto mb-16 sm:mb-20">
          <div className="inline-flex items-center gap-1.5 rounded-full border border-purple-500/30 bg-purple-500/10 px-3 py-1 text-xs font-bold uppercase tracking-wider text-purple-300 mb-4">
            <span>How It Works</span>
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-white mb-4">
            From thought to finished video in 4 steps
          </h2>
          <p className="text-base sm:text-lg text-zinc-400 leading-relaxed">
            No editing skills. No complicated timeline tools. Just your idea, and AI takes care of the rest.
          </p>
        </div>

        {/* 4 Steps Flow */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 relative">
          {steps.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div
                key={item.number}
                className="glass-card rounded-2xl p-6 sm:p-7 flex flex-col justify-between group relative border-white/[0.08] hover:border-purple-500/30 transition-all duration-300 shadow-xl"
              >
                <div>
                  {/* Step Number Pill & Icon */}
                  <div className="flex items-center justify-between mb-6">
                    <span className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-extrabold shadow-md ${item.badgeColor}`}>
                      {item.number}
                    </span>
                    <div className={`flex h-10 w-10 items-center justify-center rounded-xl border ${item.iconColor} group-hover:scale-110 transition-transform`}>
                      <Icon className="h-5 w-5" />
                    </div>
                  </div>

                  <h3 className="text-lg font-bold text-white mb-2.5 group-hover:text-purple-200 transition-colors">
                    {item.title}
                  </h3>
                  <p className="text-xs sm:text-sm text-zinc-400 leading-relaxed">
                    {item.description}
                  </p>
                </div>

                {/* Dotted indicator on desktop between cards */}
                {idx < steps.length - 1 && (
                  <div className="hidden lg:block absolute -right-3 top-1/2 -translate-y-1/2 z-20 pointer-events-none text-zinc-600 font-mono text-xs">
                    ···›
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
