"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Zap,
  Bot,
  Repeat,
  UploadCloud,
  Image as ImageIcon,
  X,
  ArrowUp,
  ArrowDown,
  Sparkles,
  Music,
  Mic,
  Sliders,
  Play,
  Download,
  RotateCcw,
  CheckCircle2,
  Circle,
  Clock,
  ArrowRight,
  AlertCircle,
  Eye,
} from "lucide-react";

interface UploadedFileItem {
  id: string;
  file: File;
  previewUrl: string;
}

const RENDER_STEPS = [
  { key: "understanding", label: "Understanding your idea" },
  { key: "script", label: "Writing the script & scene flow" },
  { key: "voice", label: "Generating ElevenLabs narration" },
  { key: "captions", label: "Creating kinetic captions & timing" },
  { key: "visuals", label: "Designing blurred background framing" },
  { key: "rendering", label: "Rendering 1080x1920 vertical video" },
];

function CreatePageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialMode = searchParams.get("mode") === "ai" ? "ai" : "quick";

  const [activeMode, setActiveMode] = useState<"quick" | "ai" | "repurpose">(initialMode);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Quick Reel State
  const [uploadedImages, setUploadedImages] = useState<UploadedFileItem[]>([]);
  const [script, setScript] = useState(
    "Welcome to VidSnap AI. Creating high-retention vertical reels has never been faster. Drop in your photos, write your message, and watch the story come to life."
  );
  const [voice, setVoice] = useState("adam");
  const [music, setMusic] = useState("ambient_chill");
  const [style, setStyle] = useState("cinematic");

  // AI Reel State
  const [aiPrompt, setAiPrompt] = useState("");
  const [aiAudience, setAiAudience] = useState("Tech Creators");
  const [aiTone, setAiTone] = useState("Thought-Provoking");
  const [aiLength, setAiLength] = useState("30s");
  const [aiStyle, setAiStyle] = useState("Cinematic Photography");
  const [aiVoice, setAiVoice] = useState("adam");

  // Rendering & Job State
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string | null>(null);
  const [jobStep, setJobStep] = useState<string>("Initializing render...");
  const [jobProgress, setJobProgress] = useState<number>(0);
  const [renderedVideoUrl, setRenderedVideoUrl] = useState<string | null>(null);

  // Word count & duration calculation
  const wordCount = script.trim() ? script.trim().split(/\s+/).length : 0;
  const estimatedDurationSecs = Math.max(3, Math.round((wordCount / 140) * 60));

  // Handle Multi-Image Upload
  const handleFileSelect = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setErrorMsg(null);

    const newItems: UploadedFileItem[] = [];
    for (let i = 0; i < files.length; i++) {
      const f = files[i];
      if (!f.type.startsWith("image/")) {
        setErrorMsg(`"${f.name}" is not an image. Only JPG, PNG, and WebP are allowed.`);
        continue;
      }
      newItems.push({
        id: `${Date.now()}_${i}_${Math.random().toString(36).substr(2, 9)}`,
        file: f,
        previewUrl: URL.createObjectURL(f),
      });
    }

    setUploadedImages((prev) => [...prev, ...newItems]);
  };

  // Reordering helpers
  const moveImage = (index: number, direction: "up" | "down") => {
    const targetIndex = direction === "up" ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= uploadedImages.length) return;

    setUploadedImages((prev) => {
      const copy = [...prev];
      const [moved] = copy.splice(index, 1);
      copy.splice(targetIndex, 0, moved);
      return copy;
    });
  };

  const removeImage = (index: number) => {
    setUploadedImages((prev) => {
      const copy = [...prev];
      URL.revokeObjectURL(copy[index].previewUrl);
      copy.splice(index, 1);
      return copy;
    });
  };

  // Submit Quick Reel
  const handleQuickReelSubmit = async () => {
    if (uploadedImages.length === 0) {
      setErrorMsg("Please upload at least one image.");
      return;
    }
    if (!script.trim()) {
      setErrorMsg("Please provide a narration script.");
      return;
    }

    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      const formData = new FormData();
      formData.append("script", script);
      formData.append("voice", voice);
      formData.append("music", music);
      formData.append("style", style);

      // Append files
      uploadedImages.forEach((item) => {
        formData.append("images", item.file);
      });

      const res = await fetch("/api/reels/quick", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to submit Quick Reel.");
      }

      const data = await res.json();
      setActiveJobId(data.job_id);
      setActiveProjectId(data.project_id);
      setJobStatus("queued");
      setJobProgress(5);
    } catch (err: any) {
      setErrorMsg(err.message || "An error occurred while creating reel.");
      setIsSubmitting(false);
    }
  };

  // Submit AI Reel
  const handleAiReelSubmit = async () => {
    if (!aiPrompt.trim()) {
      setErrorMsg("Please describe what you want to create.");
      return;
    }

    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      const res = await fetch("/api/reels/ai", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: aiPrompt,
          audience: aiAudience,
          tone: aiTone,
          length: aiLength,
          visual_style: aiStyle,
          voice: aiVoice,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to create AI Reel plan.");
      }

      const data = await res.json();
      router.push(`/projects/${data.project_id}`);
    } catch (err: any) {
      setErrorMsg(err.message || "Could not plan AI Reel.");
      setIsSubmitting(false);
    }
  };

  // Poll Job Progress
  useEffect(() => {
    if (!activeJobId || jobStatus === "completed" || jobStatus === "failed") return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/jobs/${activeJobId}`);
        if (!res.ok) return;
        const data = await res.json();

        setJobStatus(data.status);
        setJobStep(data.step);
        setJobProgress(data.progress_percent || 10);

        if (data.status === "completed") {
          setRenderedVideoUrl(data.video_url);
          setIsSubmitting(false);
          clearInterval(interval);
        } else if (data.status === "failed") {
          setErrorMsg(data.error_message || "Video rendering encountered an error.");
          setIsSubmitting(false);
          clearInterval(interval);
        }
      } catch (e) {
        console.error("Failed to poll job status", e);
      }
    }, 800);

    return () => clearInterval(interval);
  }, [activeJobId, jobStatus]);

  const getStepStatus = (stepIndex: number) => {
    const activeIndex =
      jobProgress >= 100
        ? 6
        : jobProgress >= 75
        ? 5
        : jobProgress >= 60
        ? 4
        : jobProgress >= 45
        ? 3
        : jobProgress >= 30
        ? 2
        : jobProgress >= 15
        ? 1
        : 0;

    if (stepIndex < activeIndex) return "completed";
    if (stepIndex === activeIndex) return "active";
    return "pending";
  };

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-10 w-full">
      {/* Top Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold tracking-tight text-white mb-2">
          What are we creating today?
        </h1>
        <p className="text-sm text-zinc-400">
          Pick your starting point. VidSnap automates voice, captions, music, and vertical framing.
        </p>
      </div>

      {/* Creation Mode Tabs */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
        {/* Mode 1: Quick Reel */}
        <button
          onClick={() => {
            setActiveMode("quick");
            setErrorMsg(null);
          }}
          className={`flex flex-col text-left p-5 rounded-xl border transition-all ${
            activeMode === "quick"
              ? "bg-indigo-950/30 border-indigo-500/60 shadow-lg shadow-indigo-500/10"
              : "bg-zinc-900/50 border-zinc-800 hover:border-zinc-700 text-zinc-400"
          }`}
        >
          <div className="flex items-center justify-between w-full mb-3">
            <div
              className={`flex h-8 w-8 items-center justify-center rounded-lg ${
                activeMode === "quick"
                  ? "bg-indigo-500 text-white"
                  : "bg-zinc-800 text-zinc-400"
              }`}
            >
              <Zap className="h-4 w-4" />
            </div>
            <span className="text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
              READY
            </span>
          </div>
          <h3 className="text-base font-bold text-white mb-1">Quick Reel</h3>
          <p className="text-xs text-zinc-400 leading-relaxed">
            I have my own photos or visual assets.
          </p>
        </button>

        {/* Mode 2: AI Reel */}
        <button
          onClick={() => {
            setActiveMode("ai");
            setErrorMsg(null);
          }}
          className={`flex flex-col text-left p-5 rounded-xl border transition-all ${
            activeMode === "ai"
              ? "bg-purple-950/30 border-purple-500/60 shadow-lg shadow-purple-500/10"
              : "bg-zinc-900/50 border-zinc-800 hover:border-zinc-700 text-zinc-400"
          }`}
        >
          <div className="flex items-center justify-between w-full mb-3">
            <div
              className={`flex h-8 w-8 items-center justify-center rounded-lg ${
                activeMode === "ai"
                  ? "bg-purple-500 text-white"
                  : "bg-zinc-800 text-zinc-400"
              }`}
            >
              <Bot className="h-4 w-4" />
            </div>
            <span className="text-[11px] font-semibold text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded-full border border-purple-500/20">
              AI STORY
            </span>
          </div>
          <h3 className="text-base font-bold text-white mb-1">AI Reel</h3>
          <p className="text-xs text-zinc-400 leading-relaxed">
            I have an idea. Generate story hooks and scenes.
          </p>
        </button>

        {/* Mode 3: Repurpose */}
        <button
          disabled
          className="flex flex-col text-left p-5 rounded-xl border border-zinc-850 bg-zinc-900/20 opacity-60 cursor-not-allowed"
        >
          <div className="flex items-center justify-between w-full mb-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-800 text-zinc-500">
              <Repeat className="h-4 w-4" />
            </div>
            <span className="text-[10px] font-bold text-zinc-500 bg-zinc-800 px-2 py-0.5 rounded">
              PHASE 2
            </span>
          </div>
          <h3 className="text-base font-bold text-zinc-300 mb-1">Repurpose</h3>
          <p className="text-xs text-zinc-500 leading-relaxed">
            I already have long-form video, podcasts, or articles.
          </p>
        </button>
      </div>

      {/* Error Alert */}
      {errorMsg && (
        <div className="mb-8 flex items-center gap-3 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-200">
          <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* RENDERING STATE MODAL */}
      {isSubmitting && (
return <div>Music selector configured</div>;}