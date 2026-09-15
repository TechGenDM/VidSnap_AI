import { Sparkles, Film, Volume2, Share2 } from "lucide-react";

export default function WhyVidSnap() {
  const features = [
    {
      title: "AI Script Generation",
      description: "Turn your idea, notes, or topic into a structured short-form story with clear scene beats.",
      icon: Sparkles,
      iconBg: "bg-purple-500/15 text-purple-400 border-purple-500/30",
      accentGlow: "group-hover:border-purple-500/40 group-hover:shadow-purple-500/10",
    },
    {
      title: "Auto Visuals & B-Rolls",
      description: "Generate matched visuals or upload custom B-roll clips framed cleanly for 9:16 vertical viewports.",
      icon: Film,
      iconBg: "bg-pink-500/15 text-pink-400 border-pink-500/30",
      accentGlow: "group-hover:border-pink-500/40 group-hover:shadow-pink-500/10",
    },
    {
      title: "AI Voice & Captions",
      description: "Natural voices with speech-synced narration, kinetic captions, and dynamic music ducking.",
      icon: Volume2,
      iconBg: "bg-blue-500/15 text-blue-400 border-blue-500/30",
      accentGlow: "group-hover:border-blue-500/40 group-hover:shadow-blue-500/10",
    },
    {
      title: "One-Click Export",
      description: "Render a ready-to-share 1080×1920 vertical Reel ready for YouTube Shorts, Reels, and TikTok.",
      icon: Share2,
      iconBg: "bg-indigo-500/15 text-indigo-400 border-indigo-500/30",
      accentGlow: "group-hover:border-indigo-500/40 group-hover:shadow-indigo-500/10",
    },
  ];

  return (
    <section id="why-vidsnap" className="w-full py-20 sm:py-28 relative">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center max-w-2xl mx-auto mb-16">
          <div className="inline-flex items-center gap-1.5 rounded-full border border-purple-500/30 bg-purple-500/10 px-3 py-1 text-xs font-bold uppercase tracking-wider text-purple-300 mb-4">
            <span>Why VidSnap AI?</span>
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-white mb-4">
            Create better content, faster.
          </h2>
          <p className="text-base sm:text-lg text-zinc-400 leading-relaxed">
            Everything you need to go from idea to finished Reel in one place.
          </p>
        </div>

        {/* 4 Feature Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.title}
                className={`glass-card rounded-2xl p-6 sm:p-7 flex flex-col justify-between group relative overflow-hidden transition-all duration-300 shadow-xl ${item.accentGlow}`}
              >
                <div>
                  <div className={`flex h-12 w-12 items-center justify-center rounded-2xl border mb-6 group-hover:scale-105 transition-transform ${item.iconBg}`}>
                    <Icon className="h-6 w-6" />
                  </div>
                  <h3 className="text-lg font-bold text-white mb-2.5 group-hover:text-purple-200 transition-colors">
                    {item.title}
                  </h3>
                  <p className="text-xs sm:text-sm text-zinc-400 leading-relaxed">
                    {item.description}
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
