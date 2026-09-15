"use client";

import { useState, useRef, useEffect, forwardRef, useImperativeHandle } from "react";
import { Play, Pause, Volume2, VolumeX, Sparkles, CheckCircle2, MessageSquareText } from "lucide-react";

export interface HeroProductVisualHandle {
  playVideo: () => void;
  pauseVideo: () => void;
  scrollIntoView: () => void;
}

const HeroProductVisual = forwardRef<HeroProductVisualHandle>((_, ref) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useImperativeHandle(ref, () => ({
    playVideo: () => {
      if (videoRef.current) {
        videoRef.current.play().catch(() => {});
        setIsPlaying(true);
      }
    },
    pauseVideo: () => {
      if (videoRef.current) {
        videoRef.current.pause();
        setIsPlaying(false);
      }
    },
    scrollIntoView: () => {
      containerRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    },
  }));

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
      setIsPlaying(false);
    } else {
      videoRef.current.play().catch(() => {});
      setIsPlaying(true);
    }
  };

  const toggleMute = () => {
    if (!videoRef.current) return;
    videoRef.current.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  useEffect(() => {
    // Attempt non-intrusive muted autoplay when component mounts
    if (videoRef.current) {
      videoRef.current.muted = true;
      setIsMuted(true);
      videoRef.current
        .play()
        .then(() => setIsPlaying(true))
        .catch(() => {
          // Autoplay was prevented by browser policy; wait for user tap
          setIsPlaying(false);
        });
    }
  }, []);

  return (
    <div
      ref={containerRef}
      id="demo-preview"
      className="relative w-full flex flex-col items-center justify-center py-4 lg:py-6"
    >
      {/* Ambient Radial Backdrop Glow */}
      <div className="absolute inset-0 -z-10 flex items-center justify-center pointer-events-none overflow-hidden">
        <div className="w-[320px] sm:w-[460px] h-[460px] rounded-full bg-purple-600/15 blur-[90px]" />
        <div className="w-[260px] sm:w-[360px] h-[360px] rounded-full bg-indigo-500/10 blur-[80px]" />
      </div>

      {/* Floating Card 1: Desktop Left/Top ("Idea -> Reel") */}
      <div className="hidden lg:flex flex-col gap-1 absolute lg:-left-16 xl:-left-20 top-12 z-40 p-3.5 rounded-2xl bg-[#0e111a]/90 backdrop-blur-xl border border-purple-500/30 shadow-2xl shadow-purple-950/50 max-w-[210px] animate-float-slow">
        <div className="flex items-center gap-1.5 text-[11px] font-bold text-purple-300">
          <Sparkles className="h-3.5 w-3.5 text-purple-400" />
          <span>Idea → Reel</span>
        </div>
        <p className="text-xs font-medium text-white line-clamp-1">
          “Explain vector databases”
        </p>
        <div className="flex items-center gap-1 text-[10px] font-semibold text-emerald-400 mt-0.5">
          <CheckCircle2 className="h-3 w-3" />
          <span>4 scenes generated</span>
        </div>
      </div>

      {/* Floating Card 2: Desktop Left/Bottom ("Ask VidSnap") */}
      <div className="hidden lg:flex flex-col gap-1 absolute lg:-left-20 xl:-left-24 bottom-24 z-40 p-3.5 rounded-2xl bg-[#0e111a]/90 backdrop-blur-xl border border-pink-500/30 shadow-2xl shadow-pink-950/50 max-w-[220px] animate-float-delayed">
        <div className="flex items-center gap-1.5 text-[11px] font-bold text-pink-300">
          <MessageSquareText className="h-3.5 w-3.5 text-pink-400" />
          <span>Ask VidSnap</span>
        </div>
        <p className="text-xs font-medium text-white">
          “Make the hook stronger”
        </p>
        <span className="text-[10px] font-medium text-zinc-400">
          Rephrased & timing synced
        </span>
      </div>

      {/* Floating Card 3: Desktop Right/Center ("Captions synced") */}
      <div className="hidden lg:flex flex-col gap-1 absolute lg:-right-12 xl:-right-16 top-36 z-40 p-3.5 rounded-2xl bg-[#0e111a]/90 backdrop-blur-xl border border-cyan-500/30 shadow-2xl shadow-cyan-950/50 max-w-[200px] animate-float-slow">
        <div className="flex items-center gap-1.5 text-[11px] font-bold text-cyan-300">
          <CheckCircle2 className="h-3.5 w-3.5 text-cyan-400" />
          <span>Captions Synced ✓</span>
        </div>
        <p className="text-xs font-medium text-zinc-200">
          Word-level kinetic timing
        </p>
      </div>

      {/* Desktop Handwritten Style Annotation */}
      <div className="hidden xl:block absolute -right-24 bottom-14 z-30 pointer-events-none text-right">
        <span className="font-mono text-xs text-purple-300/80 tracking-wide">
          Ideas, Notes, Scripts <br />→ Finished Reels ✦
        </span>
        <svg
          className="w-14 h-10 ml-auto mt-1 text-purple-400/60"
          viewBox="0 0 60 40"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M 50 5 Q 15 15 10 32" />
          <path d="M 5 25 L 10 32 L 18 30" />
        </svg>
      </div>

      {/* Main Vertical Phone Frame */}
      <div className="phone-mockup relative z-20 border border-white/[0.12]">
        <div className="phone-notch" />

        {/* Video Reel Container */}
        <div className="relative w-full h-full bg-black flex flex-col justify-between overflow-hidden">
          <video
            ref={videoRef}
            src="/media/reels/8de29a47-df82-48b3-a1ad-7f99190f36a1.mp4"
            className="absolute inset-0 w-full h-full object-cover"
            loop
            playsInline
            muted={isMuted}
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
          />

          {/* Top Status Bar Simulator */}
          <div className="relative z-30 pt-3.5 px-6 flex justify-between items-center text-[11px] font-semibold text-white/80">
            <span>9:41</span>
            <div className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
              <span className="text-[10px] tracking-wide uppercase font-mono text-emerald-300">1080p HD</span>
            </div>
          </div>

          {/* Center Click-to-Play/Pause Overlay */}
          <div
            onClick={togglePlay}
            className="relative z-30 flex-1 flex items-center justify-center cursor-pointer group"
            aria-label={isPlaying ? "Pause sample reel" : "Play sample reel"}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                togglePlay();
              }
            }}
          >
            {!isPlaying && (
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-black/65 text-white backdrop-blur-md border border-white/20 shadow-2xl group-hover:scale-110 transition-transform">
                <Play className="h-7 w-7 fill-current translate-x-0.5 text-purple-300" />
              </div>
            )}
          </div>

          {/* Kinetic Caption Overlay (Matching ASS Subtitle Specs) */}
          <div className="phone-caption-overlay pointer-events-none">
            <p className="phone-caption-text">
              TURN <span className="phone-caption-active-word">IDEAS</span> INTO{" "}
              <span className="phone-caption-emphasis-word">IMPACT</span>
            </p>
          </div>

          {/* Bottom HUD: Creator details and sound controls */}
          <div className="relative z-30 p-4 bg-gradient-to-t from-black/95 via-black/60 to-transparent flex flex-col gap-2.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="flex h-6 w-6 rounded-full bg-purple-500/40 text-[10px] font-bold text-purple-200 items-center justify-center border border-purple-400/30">
                  AI
                </span>
                <span className="text-xs font-semibold text-white tracking-wide">
                  @vidsnap.ai
                </span>
              </div>

              <button
                onClick={toggleMute}
                className="p-1.5 rounded-full bg-black/60 text-white/90 hover:text-white backdrop-blur-md border border-white/15 transition-colors focus-visible:ring-1 focus-visible:ring-purple-400"
                aria-label={isMuted ? "Unmute sample video" : "Mute sample video"}
              >
                {isMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4 text-purple-300" />}
              </button>
            </div>

            <p className="text-[11px] text-zinc-200 line-clamp-1">
              ✨ Speech-synced narration & kinetic captions.
            </p>
          </div>
        </div>
      </div>

      {/* Mobile-Only Docked Feature Cards (Ensures 0px horizontal overflow) */}
      <div className="lg:hidden flex flex-wrap items-center justify-center gap-2 mt-5 max-w-sm px-2 w-full">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/25 text-[11px] font-medium text-purple-300">
          <Sparkles className="h-3 w-3 text-purple-400" />
          <span>Idea → 4 Scenes</span>
        </div>
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-pink-500/10 border border-pink-500/25 text-[11px] font-medium text-pink-300">
          <MessageSquareText className="h-3 w-3 text-pink-400" />
          <span>Ask VidSnap Hook Refinement</span>
        </div>
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/25 text-[11px] font-medium text-cyan-300">
          <CheckCircle2 className="h-3 w-3 text-cyan-400" />
          <span>Speech-Synced Captions</span>
        </div>
      </div>
    </div>
  );
});

HeroProductVisual.displayName = "HeroProductVisual";

export default HeroProductVisual;
