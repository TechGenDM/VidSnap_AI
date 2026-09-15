export default function PlatformSignalStrip() {
  const platforms = [
    {
      name: "YouTube Shorts",
      svg: (
        <svg className="h-4 w-4 fill-current text-red-400 group-hover:text-red-300" viewBox="0 0 24 24">
          <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
        </svg>
      ),
    },
    {
      name: "Instagram Reels",
      svg: (
        <svg className="h-4 w-4 fill-none stroke-current stroke-2 text-pink-400 group-hover:text-pink-300" viewBox="0 0 24 24">
          <rect x="2" y="2" width="20" height="20" rx="5" ry="5"/>
          <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/>
          <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/>
        </svg>
      ),
    },
    {
      name: "TikTok",
      svg: (
        <svg className="h-4 w-4 fill-current text-cyan-400 group-hover:text-cyan-300" viewBox="0 0 24 24">
          <path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-1.01-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.24 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/>
        </svg>
      ),
    },
    {
      name: "LinkedIn Video",
      svg: (
        <svg className="h-4 w-4 fill-current text-blue-400 group-hover:text-blue-300" viewBox="0 0 24 24">
          <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
        </svg>
      ),
    },
  ];

  return (
    <section className="w-full py-12 sm:py-16 border-y border-white/[0.06] bg-[#090b12]/60 backdrop-blur-sm">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6 md:gap-8">
          {/* Section Label */}
          <div className="text-center md:text-left shrink-0">
            <span className="text-[11px] font-bold uppercase tracking-widest text-purple-400">
              Output Formats
            </span>
            <h3 className="text-base sm:text-lg font-bold text-white mt-0.5">
              Built for short-form video
            </h3>
          </div>

          {/* Platform Badges */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 w-full md:w-auto">
            {platforms.map((platform) => (
              <div
                key={platform.name}
                className="group flex items-center justify-center sm:justify-start gap-2.5 px-4 py-2.5 rounded-xl bg-white/[0.03] border border-white/[0.07] hover:border-purple-500/40 hover:bg-purple-950/20 transition-all shadow-sm"
              >
                {platform.svg}
                <span className="text-xs font-semibold text-zinc-300 group-hover:text-white transition-colors">
                  {platform.name}
                </span>
              </div>
            ))}
          </div>

          {/* Right Tagline */}
          <div className="hidden xl:flex items-center gap-2 text-xs font-mono text-purple-300/80 shrink-0">
            <span>Same idea. More reach. ⚡</span>
          </div>
        </div>
      </div>
    </section>
  );
}
