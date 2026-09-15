import { Layers, Clock, Type } from "lucide-react";

export default function CreatorProof() {
  const benefits = [
    {
      title: "Zero Timeline Fatigue",
      highlight: "Story-Driven Automation",
      description:
        "“Change a sentence in your script and the entire Reel adjusts. Audio narration, subtitles, and scene timings re-sync without ever slicing a video track.”",
      icon: Layers,
      accent: "border-purple-500/25 bg-purple-500/10 text-purple-400",
    },
    {
      title: "Pacing Calibrated for Short-Form",
      highlight: "Clear Narrative Momentum",
      description:
        "“Every scene is generated with intentional structure: a clean opening hook, dynamic visual movement, and concise narrative payoff tailored for mobile screens.”",
      icon: Clock,
      accent: "border-pink-500/25 bg-pink-500/10 text-pink-400",
    },
    {
      title: "Speech-Synced Word Captions",
      highlight: "Word-Level Alignment",
      description:
        "“No manual subtitle transcription or keyframing. Precise speech-driven timing with highlighted active words keeps mobile viewers locked into your story.”",
      icon: Type,
      accent: "border-cyan-500/25 bg-cyan-500/10 text-cyan-400",
    },
  ];

  return (
    <section className="w-full py-20 sm:py-28 border-t border-white/[0.06] bg-[#090b12]/60">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center max-w-2xl mx-auto mb-16">
          <div className="inline-flex items-center gap-1.5 rounded-full border border-purple-500/30 bg-purple-500/10 px-3 py-1 text-xs font-bold uppercase tracking-wider text-purple-300 mb-4">
            <span>Story-First Workflow</span>
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-white mb-4">
            Built for creators who value their time.
          </h2>
          <p className="text-base sm:text-lg text-zinc-400 leading-relaxed">
            Why solo creators, technical builders, and educators choose story-first video creation over manual timelines.
          </p>
        </div>

        {/* 3 Benefit Cards (Testimonial Architecture Shell) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {benefits.map((card) => {
            const Icon = card.icon;
            return (
              <div
                key={card.title}
                className="glass-card rounded-2xl p-6 sm:p-7 flex flex-col justify-between border-white/[0.08] hover:border-purple-500/30 transition-all duration-300 shadow-xl"
              >
                <div>
                  <div className="flex items-center justify-between mb-5">
                    <div className={`flex h-10 w-10 items-center justify-center rounded-xl border ${card.accent}`}>
                      <Icon className="h-5 w-5" />
                    </div>
                    <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-purple-300/80 bg-purple-500/10 px-2.5 py-1 rounded-full border border-purple-500/20">
                      {card.highlight}
                    </span>
                  </div>

                  <h3 className="text-lg font-bold text-white mb-3">
                    {card.title}
                  </h3>
                  <p className="text-xs sm:text-sm text-zinc-300 leading-relaxed italic">
                    {card.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
