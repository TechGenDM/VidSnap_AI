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
  RefreshCw,
  Edit3,
  Flame,
  Check,
  ChevronRight,
  Layers,
} from "lucide-react";

interface VisualPlanData {
  visual_type?: string;
  subject?: string;
  environment?: string;
  composition?: string;
  mood?: string;
  motion?: string;
  transition?: string;
  emphasis?: string;
}

interface StorySceneItem {
  order: number;
  narration: string;
  caption: string;
  visual_direction: string;
  estimated_duration: number;
  scene_role?: string;
  visual_plan?: VisualPlanData;
  motion?: string;
  transition?: string;
}

interface PlannedStory {
  title: string;
  hook: string;
  scenes: StorySceneItem[];
  cta: string;
  estimated_duration: number;
}

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

const TEMPLATE_PRESETS: Record<string, { script: string; style: string; voice: string; music: string }> = {
  tech_breakdown: {
    script: "Artificial Intelligence is transforming how developers build software in 2026. Autonomous agents can now explore repositories, diagnose bottlenecks, and write verified production code in seconds. The future of engineering is orchestration.",
    style: "cinematic",
    voice: "adam",
    music: "ambient_chill",
  },
  product_showcase: {
    script: "Meet the creator workflow built for modern reels. Clean visuals, instant rendering, and speech-synchronized pacing directly on your phone. Experience video creation redefined.",
    style: "dynamic",
    voice: "rachel",
    music: "upbeat_pulse",
  },
  founder_story: {
    script: "When we set out to build VidSnap, our core rule was simple: edit the story, never the timeline. Creators shouldn't spend hours tweaking keyframes when an idea is ready to share.",
    style: "minimal",
    voice: "antoni",
    music: "lofi_beat",
  },
};

function CreatePageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialMode = searchParams.get("mode") === "ai" ? "ai" : "quick";
  const templateKey = searchParams.get("template");

  const [activeMode, setActiveMode] = useState<"quick" | "ai" | "repurpose">(initialMode);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isLoadingSamples, setIsLoadingSamples] = useState(false);

  // Quick Reel State
  const defaultTemplate = templateKey && TEMPLATE_PRESETS[templateKey] ? TEMPLATE_PRESETS[templateKey] : null;
  const [uploadedImages, setUploadedImages] = useState<UploadedFileItem[]>([]);
  const [script, setScript] = useState(
    defaultTemplate?.script ||
    "Welcome to VidSnap AI. Creating high-retention vertical reels has never been faster. Drop in your photos, write your message, and watch the story come to life."
  );
  const [voice, setVoice] = useState(defaultTemplate?.voice || "adam");
  const [music, setMusic] = useState(defaultTemplate?.music || "ambient_chill");
  const [style, setStyle] = useState(defaultTemplate?.style || "cinematic");

  // AI Reel State
  const [aiPrompt, setAiPrompt] = useState(
    "Explain why AI agents are changing software development."
  );
  const [aiAudience, setAiAudience] = useState("Tech Creators");
  const [aiTone, setAiTone] = useState("Educational");
  const [aiLength, setAiLength] = useState("30s");
  const [aiStyle, setAiStyle] = useState("Minimal Tech");
  const [aiVoice, setAiVoice] = useState("adam");
  const [aiMusic, setAiMusic] = useState("ambient_chill");
  const [aiVisualSource, setAiVisualSource] = useState("auto"); // "auto" | "ai" | "local"

  const [isPlanning, setIsPlanning] = useState(false);
  const [plannedStory, setPlannedStory] = useState<PlannedStory | null>(null);
  const [isRegeneratingStory, setIsRegeneratingStory] = useState(false);
  const [reviewFeedback, setReviewFeedback] = useState<string | null>(null);

  // Rendering & Job State
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string | null>(null);
  const [jobStep, setJobStep] = useState<string>("Initializing render...");
  const [jobProgress, setJobProgress] = useState<number>(0);
  const [renderedVideoUrl, setRenderedVideoUrl] = useState<string | null>(null);

  // Restore active job from sessionStorage on refresh/mount
  useEffect(() => {
    if (typeof window === "undefined") return;
    const savedJobId = sessionStorage.getItem("vidsnap_active_job_id");
    const savedProjectId = sessionStorage.getItem("vidsnap_active_project_id");
    if (savedJobId) {
      setActiveJobId(savedJobId);
      if (savedProjectId) setActiveProjectId(savedProjectId);
      setIsSubmitting(true);
      setJobStep("Resuming render progress...");
    }
  }, []);

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

  // Instant Sample Images Loader
  const handleLoadSampleImages = async () => {
    setIsLoadingSamples(true);
    setErrorMsg(null);
    try {
      const samples = [
        { name: "visual_01.jpg", url: "/media/templates/1.jpg" },
        { name: "visual_02.jpg", url: "/media/templates/2.jpg" },
        { name: "visual_03.jpg", url: "/media/templates/3.jpg" },
      ];
      const items: UploadedFileItem[] = [];
      for (let i = 0; i < samples.length; i++) {
        const item = samples[i];
        const res = await fetch(item.url);
        const blob = await res.blob();
        const file = new File([blob], item.name, { type: "image/jpeg" });
        items.push({
          id: `sample_${Date.now()}_${i}`,
          file,
          previewUrl: URL.createObjectURL(file),
        });
      }
      setUploadedImages((prev) => [...prev, ...items]);
    } catch (e: any) {
      setErrorMsg("Failed to load sample visuals: " + e.message);
    } finally {
      setIsLoadingSamples(false);
    }
  };

  // Drag and drop handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    handleFileSelect(e.dataTransfer.files);
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
      if (typeof window !== "undefined") {
        sessionStorage.setItem("vidsnap_active_job_id", data.job_id);
        sessionStorage.setItem("vidsnap_active_project_id", data.project_id);
      }
      setJobStatus("queued");
      setJobProgress(5);
    } catch (err: any) {
      setErrorMsg(err.message || "An error occurred while creating reel.");
      setIsSubmitting(false);
    }
  };

  // Submit AI Reel Idea -> Generates Story for Review
  const handleAiReelSubmit = async () => {
    if (!aiPrompt.trim()) {
      setErrorMsg("Please describe what you want to create.");
      return;
    }

    setIsPlanning(true);
    setErrorMsg(null);
    setReviewFeedback(null);

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
          music: aiMusic,
          visual_source: aiVisualSource,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to generate AI story.");
      }

      const data = await res.json();
      setPlannedStory(data.story);
      setActiveProjectId(data.project_id);
    } catch (err: any) {
      setErrorMsg(err.message || "Could not plan AI Reel.");
    } finally {
      setIsPlanning(false);
    }
  };

  // Regenerate Entire Story
  const handleRegenerateStory = async () => {
    if (!activeProjectId) return;
    setIsRegeneratingStory(true);
    setErrorMsg(null);
    setReviewFeedback(null);
    try {
      const res = await fetch(`/api/projects/${activeProjectId}/regenerate-story`, {
        method: "POST",
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to regenerate story.");
      }
      const data = await res.json();
      setPlannedStory(data.story);
      setReviewFeedback("✨ Story regenerated with a fresh angle & hook!");
      setTimeout(() => setReviewFeedback(null), 3500);
    } catch (err: any) {
      setErrorMsg(err.message || "Could not regenerate story.");
    } finally {
      setIsRegeneratingStory(false);
    }
  };

  // Handle inline scene edits during Story Review
  const handlePlannedSceneChange = (
    order: number,
    field: "narration" | "caption" | "visual_direction",
    val: string
  ) => {
    if (!plannedStory) return;
    setPlannedStory({
      ...plannedStory,
      scenes: plannedStory.scenes.map((s) =>
        s.order === order ? { ...s, [field]: val } : s
      ),
    });
  };

  // Approve Story & Trigger Video Rendering
  const handleApproveAndRender = async () => {
    if (!activeProjectId || !plannedStory) return;
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      // First persist any inline edits to backend scenes
      await fetch(`/api/projects/${activeProjectId}/scenes`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scenes: plannedStory.scenes.map((s) => ({
            id: `scene_${s.order}`,
            narration: s.narration,
            caption: s.caption,
            visual_direction: s.visual_direction,
          })),
        }),
      });

      // Launch render pipeline
      const res = await fetch(`/api/projects/${activeProjectId}/render`, {
        method: "POST",
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to enqueue video render.");
      }
      const data = await res.json();
      setActiveJobId(data.job_id);
      if (typeof window !== "undefined") {
        sessionStorage.setItem("vidsnap_active_job_id", data.job_id);
        sessionStorage.setItem("vidsnap_active_project_id", activeProjectId);
      }
      setJobStatus("queued");
      setJobProgress(5);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to start render.");
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
          if (typeof window !== "undefined") {
            sessionStorage.removeItem("vidsnap_active_job_id");
          }
          clearInterval(interval);
        } else if (data.status === "failed") {
          setErrorMsg(data.error_message || "Video rendering encountered an error.");
          setIsSubmitting(false);
          if (typeof window !== "undefined") {
            sessionStorage.removeItem("vidsnap_active_job_id");
          }
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
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-4">
          <div className="glass-card rounded-2xl max-w-lg w-full p-8 border-indigo-500/40 shadow-2xl relative overflow-hidden">
            <div className="flex items-center gap-3 mb-6">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/20 text-indigo-400 animate-pulse">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">YOUR REEL</h3>
                <p className="text-xs text-zinc-400">{jobStep}</p>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-zinc-800 h-2 rounded-full mb-6 overflow-hidden">
              <div
                className="bg-gradient-to-r from-indigo-500 to-purple-500 h-full rounded-full transition-all duration-300"
                style={{ width: `${jobProgress}%` }}
              />
            </div>

            {/* Step-by-Step Checklist */}
            <div className="space-y-3.5 mb-8">
              {RENDER_STEPS.map((step, idx) => {
                const status = getStepStatus(idx);
                return (
                  <div key={step.key} className="flex items-center gap-3 text-sm">
                    {status === "completed" ? (
                      <CheckCircle2 className="h-5 w-5 text-emerald-400 flex-shrink-0" />
                    ) : status === "active" ? (
                      <div className="h-5 w-5 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin flex-shrink-0" />
                    ) : (
                      <Circle className="h-5 w-5 text-zinc-700 flex-shrink-0" />
                    )}
                    <span
                      className={
                        status === "completed"
                          ? "text-zinc-300 line-through decoration-zinc-600"
                          : status === "active"
                          ? "text-white font-semibold"
                          : "text-zinc-500"
                      }
                    >
                      {step.label}
                    </span>
                  </div>
                );
              })}
            </div>

            <p className="text-xs text-center text-zinc-500">
              VidSnap is rendering 1080×1920 MP4 with speech-driven slide synchronization...
            </p>
          </div>
        </div>
      )}

      {/* RESULT EXPERIENCE (When Reel is Completed) */}
      {jobStatus === "completed" && renderedVideoUrl && (
        <div className="mb-12 glass-card rounded-2xl p-8 border-emerald-500/40 bg-zinc-950/80">
          <div className="flex flex-col lg:flex-row items-center gap-10">
            {/* Phone Player Preview */}
            <div className="phone-mockup flex-shrink-0">
              <div className="phone-notch" />
              <video
                src={renderedVideoUrl}
                controls
                autoPlay
                loop
                playsInline
                className="w-full h-full object-cover"
              />
            </div>

            {/* Result Info & Actions */}
            <div className="flex-1 flex flex-col items-start">
              <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3.5 py-1 text-xs font-semibold text-emerald-400 mb-4">
                <CheckCircle2 className="h-4 w-4" />
                <span>1080×1920 HD Ready</span>
              </div>

              <h2 className="text-3xl font-extrabold text-white mb-3">
                Your Reel is ready 🎉
              </h2>

              <p className="text-sm text-zinc-300 mb-6 max-w-lg leading-relaxed">
                Your vertical Reel was rendered with blurred background padding, dynamic narration sync, and background music ducking.
              </p>

              <div className="grid grid-cols-2 gap-3 w-full max-w-md mb-8">
                <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-3.5 text-left">
                  <span className="text-[11px] text-zinc-400 block mb-1">Duration</span>
                  <span className="text-base font-bold text-white">{estimatedDurationSecs}s</span>
                </div>
                <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-3.5 text-left">
                  <span className="text-[11px] text-zinc-400 block mb-1">Scenes / Slides</span>
                  <span className="text-base font-bold text-white">{uploadedImages.length}</span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center gap-3 w-full max-w-md">
                <a
                  href={renderedVideoUrl}
                  download="vidsnap_reel.mp4"
                  className="flex-1 flex items-center justify-center gap-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 px-5 py-3 text-sm font-semibold text-white shadow-lg transition-all"
                >
                  <Download className="h-4 w-4" />
                  <span>Download MP4</span>
                </a>

                {activeProjectId && (
                  <Link
                    href={`/projects/${activeProjectId}`}
                    className="flex-1 flex items-center justify-center gap-2 rounded-xl border border-zinc-700 bg-zinc-800 hover:bg-zinc-750 px-5 py-3 text-sm font-semibold text-white transition-all"
                  >
                    <Sliders className="h-4 w-4" />
                    <span>Edit Story</span>
                  </Link>
                )}

                <button
                  onClick={() => {
                    setJobStatus(null);
                    setRenderedVideoUrl(null);
                    setUploadedImages([]);
                    if (typeof window !== "undefined") {
                      sessionStorage.removeItem("vidsnap_active_job_id");
                      sessionStorage.removeItem("vidsnap_active_project_id");
                    }
                  }}
                  className="w-full flex items-center justify-center gap-2 rounded-xl border border-zinc-850 hover:border-zinc-750 py-2.5 text-xs text-zinc-400 hover:text-white transition-colors"
                >
                  <RotateCcw className="h-3.5 w-3.5" />
                  <span>Create Another Reel</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* QUICK REEL INTERFACE */}
      {activeMode === "quick" && jobStatus !== "completed" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: Upload Your Visuals */}
          <div className="lg:col-span-6 flex flex-col gap-6">
            <div className="glass-card rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2.5">
                  <ImageIcon className="h-5 w-5 text-indigo-400" />
                  <h2 className="text-lg font-bold text-white">Upload your visuals</h2>
                </div>
                <span className="text-xs font-semibold text-zinc-400 bg-zinc-800 px-2.5 py-1 rounded-full">
                  {uploadedImages.length} {uploadedImages.length === 1 ? "image" : "images"}
                </span>
              </div>

              {/* Drag and Drop Zone */}
              <label
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`relative flex flex-col items-center justify-center w-full min-h-[160px] rounded-xl border-2 border-dashed transition-all p-6 text-center group cursor-pointer ${
                  isDragging
                    ? "border-indigo-400 bg-indigo-500/15 scale-[1.01]"
                    : "border-zinc-800 hover:border-indigo-500/50 bg-zinc-900/40 hover:bg-zinc-900/80"
                }`}
              >
                <UploadCloud
                  className={`h-10 w-10 transition-colors mb-3 ${
                    isDragging ? "text-indigo-400 animate-bounce" : "text-zinc-500 group-hover:text-indigo-400"
                  }`}
                />
                <span className="text-sm font-semibold text-zinc-200 mb-1">
                  {isDragging ? "Drop images to upload" : "Drop your photos here, or browse"}
                </span>
                <span className="text-xs text-zinc-500">
                  Supports JPG, PNG, WebP up to 25MB each
                </span>
                <input
                  type="file"
                  multiple
                  accept="image/jpeg,image/png,image/webp"
                  className="hidden"
                  onChange={(e) => handleFileSelect(e.target.files)}
                />
              </label>

              {/* Sample Images Quick Button */}
              <div className="mt-3 flex items-center justify-between">
                <span className="text-xs text-zinc-500">Need sample images to test?</span>
                <button
                  type="button"
                  onClick={handleLoadSampleImages}
                  disabled={isLoadingSamples}
                  className="flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 font-medium px-2.5 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/20 hover:bg-indigo-500/20 transition-all disabled:opacity-50"
                >
                  <Sparkles className="h-3 w-3" />
                  <span>{isLoadingSamples ? "Loading..." : "Load Sample Photos"}</span>
                </button>
              </div>

              {/* Uploaded Thumbnails List with Reordering */}
              {uploadedImages.length > 0 && (
                <div className="mt-6 flex flex-col gap-2.5">
                  <div className="flex items-center justify-between text-xs text-zinc-400 px-1">
                    <span>Scene Order</span>
                    <span>Use arrows to reorder slides</span>
                  </div>

                  <div className="grid grid-cols-1 gap-2.5 max-h-[340px] overflow-y-auto pr-1">
                    {uploadedImages.map((item, idx) => (
                      <div
                        key={item.id}
                        className="flex items-center justify-between p-2.5 rounded-xl border border-zinc-800 bg-zinc-900/70 hover:border-zinc-700 transition-all"
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-xs font-mono font-bold text-zinc-500 w-5 text-center">
                            #{idx + 1}
                          </span>
                          <img
                            src={item.previewUrl}
                            alt="Preview"
                            className="h-12 w-12 rounded-lg object-cover border border-zinc-700"
                          />
                          <div className="flex flex-col">
                            <span className="text-xs font-medium text-white truncate max-w-[160px] sm:max-w-[220px]">
                              {item.file.name}
                            </span>
                            <span className="text-[10px] text-zinc-500">
                              {(item.file.size / 1024).toFixed(0)} KB
                            </span>
                          </div>
                        </div>

                        {/* Reorder & Delete Buttons */}
                        <div className="flex items-center gap-1">
                          <button
                            type="button"
                            disabled={idx === 0}
                            onClick={() => moveImage(idx, "up")}
                            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 disabled:opacity-30"
                          >
                            <ArrowUp className="h-4 w-4" />
                          </button>
                          <button
                            type="button"
                            disabled={idx === uploadedImages.length - 1}
                            onClick={() => moveImage(idx, "down")}
                            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 disabled:opacity-30"
                          >
                            <ArrowDown className="h-4 w-4" />
                          </button>
                          <button
                            type="button"
                            onClick={() => removeImage(idx)}
                            className="p-1.5 rounded-lg text-red-400 hover:bg-red-500/10 ml-1"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Tell the Story */}
          <div className="lg:col-span-6 flex flex-col gap-6">
            <div className="glass-card rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2.5">
                  <Mic className="h-5 w-5 text-indigo-400" />
                  <h2 className="text-lg font-bold text-white">Tell the story</h2>
                </div>
                <div className="flex items-center gap-2 text-xs text-zinc-400">
                  <Clock className="h-3.5 w-3.5" />
                  <span>Est. ~{estimatedDurationSecs}s duration</span>
                </div>
              </div>

              {/* Script Textarea */}
              <div className="relative mb-6">
                <textarea
                  rows={5}
                  value={script}
                  onChange={(e) => setScript(e.target.value)}
                  placeholder="Enter your voiceover narration script here..."
                  className="w-full rounded-xl border border-zinc-800 bg-zinc-900/60 p-4 text-sm text-zinc-100 placeholder-zinc-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 resize-none transition-all"
                />
                <div className="flex justify-between text-[11px] text-zinc-500 px-1 mt-1">
                  <span>{wordCount} words</span>
                  <span>Audio duration auto-syncs to slide count</span>
                </div>
              </div>

              {/* Voice, Music, Style Selectors */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
                {/* Voice */}
                <div>
                  <label className="block text-xs font-semibold text-zinc-300 mb-1.5">
                    Narration Voice
                  </label>
                  <select
                    value={voice}
                    onChange={(e) => setVoice(e.target.value)}
                    className="w-full rounded-xl border border-zinc-800 bg-zinc-900 px-3.5 py-2.5 text-xs text-white focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="adam">Adam (Deep & Narrative)</option>
                    <option value="rachel">Rachel (Warm & Engaging)</option>
                    <option value="josh">Josh (Young & Energetic)</option>
                    <option value="antoni">Antoni (Crisp & Thoughtful)</option>
                  </select>
                </div>

                {/* Music */}
                <div>
                  <label className="block text-xs font-semibold text-zinc-300 mb-1.5">
                    Background Music
                  </label>
                  <select
                    value={music}
                    onChange={(e) => setMusic(e.target.value)}
                    className="w-full rounded-xl border border-zinc-800 bg-zinc-900 px-3.5 py-2.5 text-xs text-white focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="ambient_chill">Ambient Chill (Ducked)</option>
                    <option value="upbeat_pulse">Upbeat Pulse (Ducked)</option>
                    <option value="lofi_beat">Lo-Fi Dream (Ducked)</option>
                    <option value="none">None (Voice Only)</option>
                  </select>
                </div>
              </div>

              {/* Style Selector */}
              <div className="mb-8">
                <label className="block text-xs font-semibold text-zinc-300 mb-1.5">
                  Visual Presentation Style
                </label>
                <div className="grid grid-cols-3 gap-2.5">
                  {[
                    { id: "cinematic", label: "Cinematic" },
                    { id: "dynamic", label: "Dynamic Pop" },
                    { id: "minimal", label: "Clean Minimal" },
                  ].map((s) => (
                    <button
                      key={s.id}
                      type="button"
                      onClick={() => setStyle(s.id)}
                      className={`py-2 px-3 rounded-lg text-xs font-medium border text-center transition-all ${
                        style === s.id
                          ? "bg-indigo-600 text-white border-indigo-500 shadow-sm"
                          : "border-zinc-800 bg-zinc-900 text-zinc-400 hover:text-white"
                      }`}
                    >
                      {s.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Primary CTA */}
              <button
                type="button"
                onClick={handleQuickReelSubmit}
                disabled={uploadedImages.length === 0 || !script.trim()}
                className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 py-3.5 text-sm font-bold text-white shadow-xl shadow-indigo-500/25 hover:from-indigo-600 hover:to-purple-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all active:scale-98"
              >
                <Sparkles className="h-4 w-4" />
                <span>Generate Reel →</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* AI REEL INTERFACE */}
      {activeMode === "ai" && jobStatus !== "completed" && (
        <div className="max-w-4xl mx-auto">
          {!plannedStory ? (
            /* STEP 1 — IDEA INPUT */
            <div className="glass-card rounded-2xl p-6 sm:p-8 border-purple-500/20 shadow-2xl">
              <div className="flex items-center gap-3.5 mb-6">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-purple-500/20 to-indigo-500/20 text-purple-400 border border-purple-500/30">
                  <Bot className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white tracking-tight">What do you want to create?</h2>
                  <p className="text-xs text-zinc-400">
                    VidSnap structures your idea into a high-retention hook, scenes, captions, and visual plan.
                  </p>
                </div>
              </div>

              {/* Idea Prompt Input */}
              <div className="mb-6">
                <label className="block text-xs font-semibold text-zinc-300 mb-2">
                  Your Idea / Topic
                </label>
                <textarea
                  rows={4}
                  value={aiPrompt}
                  onChange={(e) => setAiPrompt(e.target.value)}
                  placeholder="e.g. “Explain why AI agents are changing software development.”"
                  className="w-full rounded-xl border border-zinc-800 bg-zinc-900/70 p-4 text-sm text-zinc-100 placeholder-zinc-500 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500 resize-none transition-all"
                />
              </div>

              {/* Optional Controls Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
                <div>
                  <label className="block text-xs font-semibold text-zinc-300 mb-1.5">
                    Target Audience
                  </label>
                  <select
                    value={aiAudience}
                    onChange={(e) => setAiAudience(e.target.value)}
                    className="w-full rounded-xl border border-zinc-800 bg-zinc-900 px-3.5 py-2.5 text-xs text-white focus:border-purple-500 focus:outline-none"
                  >
                    <option value="Tech Creators">Tech Creators</option>
                    <option value="General Audience">General Audience</option>
                    <option value="Startup Founders">Startup Founders</option>
                    <option value="Students & Beginners">Students & Beginners</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-zinc-300 mb-1.5">
                    Narrative Tone
                  </label>
                  <select
                    value={aiTone}
                    onChange={(e) => setAiTone(e.target.value)}
                    className="w-full rounded-xl border border-zinc-800 bg-zinc-900 px-3.5 py-2.5 text-xs text-white focus:border-purple-500 focus:outline-none"
                  >
                    <option value="Educational">Educational & Calm</option>
                    <option value="High Energy">High Energy (Punchy)</option>
                    <option value="Thought-Provoking">Thought-Provoking</option>
                    <option value="Documentary Story">Documentary Story</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-zinc-300 mb-1.5">
                    Target Length
                  </label>
                  <select
                    value={aiLength}
                    onChange={(e) => setAiLength(e.target.value)}
                    className="w-full rounded-xl border border-zinc-800 bg-zinc-900 px-3.5 py-2.5 text-xs text-white focus:border-purple-500 focus:outline-none"
                  >
                    <option value="15s">15 seconds (Viral Hook)</option>
                    <option value="30s">30 seconds (Standard Reel)</option>
                    <option value="60s">60 seconds (Deep Dive)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-zinc-300 mb-1.5">
                    Visual Style
                  </label>
                  <select
                    value={aiStyle}
                    onChange={(e) => setAiStyle(e.target.value)}
                    className="w-full rounded-xl border border-zinc-800 bg-zinc-900 px-3.5 py-2.5 text-xs text-white focus:border-purple-500 focus:outline-none"
                  >
                    <option value="Minimal Tech">Minimal Tech</option>
                    <option value="Cinematic Photography">Cinematic Photography</option>
                    <option value="Vibrant Modern">Vibrant Modern</option>
                    <option value="Documentary">Documentary</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-zinc-300 mb-1.5">
                    Narrator Voice
                  </label>
                  <select
                    value={aiVoice}
                    onChange={(e) => setAiVoice(e.target.value)}
                    className="w-full rounded-xl border border-zinc-800 bg-zinc-900 px-3.5 py-2.5 text-xs text-white focus:border-purple-500 focus:outline-none"
                  >
                    <option value="adam">Adam (Deep & Narrative)</option>
                    <option value="rachel">Rachel (Warm & Engaging)</option>
                    <option value="josh">Josh (Young & Energetic)</option>
                    <option value="antoni">Antoni (Crisp & Thoughtful)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-zinc-300 mb-1.5">
                    Background Music
                  </label>
                  <select
                    value={aiMusic}
                    onChange={(e) => setAiMusic(e.target.value)}
                    className="w-full rounded-xl border border-zinc-800 bg-zinc-900 px-3.5 py-2.5 text-xs text-white focus:border-purple-500 focus:outline-none"
                  >
                    <option value="ambient_chill">Ambient Chill (Ducked)</option>
                    <option value="upbeat_pulse">Upbeat Pulse (Ducked)</option>
                    <option value="lofi_beat">Lo-Fi Dream (Ducked)</option>
                    <option value="none">None (Voice Only)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-zinc-300 mb-1.5 flex items-center justify-between">
                    <span>Visual Source</span>
                    <span className="text-[10px] text-purple-400 font-mono">Real AI</span>
                  </label>
                  <select
                    value={aiVisualSource}
                    onChange={(e) => setAiVisualSource(e.target.value)}
                    className="w-full rounded-xl border border-zinc-800 bg-zinc-900 px-3.5 py-2.5 text-xs text-white focus:border-purple-500 focus:outline-none"
                  >
                    <option value="auto">Smart (Balanced & Fast)</option>
                    <option value="ai">AI Generated (Full AI Visuals)</option>
                    <option value="local">Stock (Local Templates)</option>
                  </select>
                </div>
              </div>

              {/* Primary CTA */}
              <button
                type="button"
                onClick={handleAiReelSubmit}
                disabled={!aiPrompt.trim() || isPlanning}
                className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 py-4 text-sm font-bold text-white shadow-xl shadow-purple-500/25 hover:from-purple-500 hover:to-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all active:scale-98"
              >
                {isPlanning ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin text-purple-200" />
                    <span>Structuring Your Story...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    <span>Build My Reel →</span>
                  </>
                )}
              </button>
            </div>
          ) : (
            /* STEP 2 — SCRIPT REVIEW STEP (HUMAN APPROVAL POINT) */
            <div className="space-y-6">
              {/* Review Header Banner */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 glass-card rounded-2xl border-purple-500/30 bg-gradient-to-r from-purple-950/20 via-zinc-900/60 to-indigo-950/20 shadow-xl">
                <div>
                  <div className="flex items-center gap-2.5 mb-1.5">
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider bg-purple-500/20 text-purple-300 border border-purple-500/30">
                      <Sparkles className="h-3 w-3" />
                      Human Review Step
                    </span>
                    <span className="text-xs text-zinc-400 font-mono">
                      ~{plannedStory.estimated_duration}s est. • {plannedStory.scenes.length} scenes
                    </span>
                  </div>
                  <h1 className="text-2xl font-extrabold text-white tracking-tight">
                    Your Story
                  </h1>
                  <p className="text-xs text-zinc-400 mt-0.5">
                    Review and fine-tune your hook, narration, and scene captions before generating video.
                  </p>
                </div>

                <div className="flex items-center gap-2.5">
                  <button
                    type="button"
                    onClick={() => setPlannedStory(null)}
                    className="px-3 py-2 rounded-xl text-xs font-semibold text-zinc-400 hover:text-white bg-zinc-900 border border-zinc-800 hover:border-zinc-700 transition-all"
                  >
                    ← Edit Idea
                  </button>

                  <button
                    type="button"
                    onClick={handleRegenerateStory}
                    disabled={isRegeneratingStory}
                    className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold text-purple-300 hover:text-white bg-purple-500/10 border border-purple-500/30 hover:bg-purple-500/20 transition-all disabled:opacity-50"
                  >
                    <RefreshCw className={`h-3.5 w-3.5 ${isRegeneratingStory ? "animate-spin" : ""}`} />
                    <span>{isRegeneratingStory ? "Regenerating..." : "Regenerate Story"}</span>
                  </button>
                </div>
              </div>

              {/* Feedback toast banner if present */}
              {reviewFeedback && (
                <div className="flex items-center gap-2 p-3.5 rounded-xl border border-emerald-500/30 bg-emerald-500/10 text-xs font-medium text-emerald-300 animate-fadeIn">
                  <Check className="h-4 w-4 text-emerald-400" />
                  <span>{reviewFeedback}</span>
                </div>
              )}

              {/* Story Title & Hook Section */}
              <div className="glass-card rounded-2xl p-6 border-zinc-800 space-y-4">
                <div>
                  <label className="block text-[11px] font-semibold uppercase tracking-wider text-zinc-500 mb-1">
                    Reel Title
                  </label>
                  <input
                    type="text"
                    value={plannedStory.title}
                    onChange={(e) => setPlannedStory({ ...plannedStory, title: e.target.value })}
                    className="w-full text-base font-bold text-white bg-zinc-900/60 border border-zinc-800 rounded-xl px-3.5 py-2 focus:border-purple-500 focus:outline-none"
                  />
                </div>

                <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/25">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-purple-300 mb-1.5">
                    <Flame className="h-3.5 w-3.5 text-amber-400" />
                    <span>Opening Hook (First 2 Seconds)</span>
                  </div>
                  <p className="text-sm font-medium text-purple-100 leading-relaxed">
                    “{plannedStory.hook}”
                  </p>
                </div>
              </div>

              {/* Story Scenes Flow */}
              <div className="space-y-4">
                <div className="flex items-center justify-between px-1">
                  <div className="flex items-center gap-2">
                    <Layers className="h-4 w-4 text-purple-400" />
                    <h3 className="text-sm font-bold text-white">Scene Flow</h3>
                  </div>
                  <span className="text-xs text-zinc-500">
                    Durations dynamically re-sync to spoken audio length
                  </span>
                </div>

                {plannedStory.scenes.map((s) => (
                  <div
                    key={s.order}
                    className="glass-card rounded-2xl p-5 border-zinc-800 hover:border-zinc-700 transition-all space-y-3"
                  >
                    <div className="flex items-center justify-between flex-wrap gap-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="px-2 py-0.5 rounded-md text-[11px] font-mono font-bold bg-zinc-800 text-zinc-200 border border-zinc-700">
                          Scene #{s.order}
                        </span>
                        {s.scene_role && (
                          <span className="px-2 py-0.5 rounded-md text-[10px] uppercase font-bold tracking-wider bg-purple-500/10 text-purple-300 border border-purple-500/20">
                            {s.scene_role}
                          </span>
                        )}
                        {(s.visual_plan?.motion || s.motion) && (
                          <span className="px-2 py-0.5 rounded-md text-[10px] font-medium tracking-wide bg-blue-500/10 text-blue-300 border border-blue-500/20 capitalize">
                            {(s.visual_plan?.motion || s.motion || "").replace(/_/g, " ")}
                          </span>
                        )}
                        {(s.visual_plan?.transition || s.transition) && (
                          <span className="px-2 py-0.5 rounded-md text-[10px] font-medium tracking-wide bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 capitalize">
                            {(s.visual_plan?.transition || s.transition || "").replace(/_/g, " ")}
                          </span>
                        )}
                        {s.visual_plan?.mood && (
                          <span className="px-2 py-0.5 rounded-md text-[10px] font-medium tracking-wide bg-amber-500/10 text-amber-300 border border-amber-500/20 capitalize">
                            {s.visual_plan.mood}
                          </span>
                        )}
                        <span className="text-[11px] text-zinc-400 font-mono">
                          Est. ~{s.estimated_duration}s
                        </span>
                      </div>
                      <span className="text-[11px] text-purple-400/90 font-medium">
                        {aiVisualSource === "ai"
                          ? "✨ AI Generated Visual"
                          : aiVisualSource === "local"
                          ? "📷 Stock Library Asset"
                          : "⚡ Smart Visual Engine"}
                      </span>
                    </div>

                    {/* Narration Field */}
                    <div>
                      <label className="block text-[11px] font-semibold text-zinc-400 mb-1">
                        Narration Script
                      </label>
                      <textarea
                        rows={2}
                        value={s.narration}
                        onChange={(e) => handlePlannedSceneChange(s.order, "narration", e.target.value)}
                        className="w-full rounded-xl border border-zinc-800 bg-zinc-900/70 p-3 text-xs text-white placeholder-zinc-500 focus:border-purple-500 focus:outline-none resize-none leading-relaxed"
                      />
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {/* Caption Overlay */}
                      <div>
                        <label className="block text-[11px] font-semibold text-zinc-400 mb-1">
                          Screen Caption
                        </label>
                        <input
                          type="text"
                          value={s.caption}
                          onChange={(e) => handlePlannedSceneChange(s.order, "caption", e.target.value)}
                          className="w-full rounded-xl border border-zinc-800 bg-zinc-900/70 px-3 py-2 text-xs font-semibold text-white focus:border-purple-500 focus:outline-none"
                        />
                      </div>

                      {/* Visual Direction */}
                      <div>
                        <label className="block text-[11px] font-semibold text-zinc-400 mb-1">
                          Visual Direction
                        </label>
                        <input
                          type="text"
                          value={s.visual_direction}
                          onChange={(e) => handlePlannedSceneChange(s.order, "visual_direction", e.target.value)}
                          className="w-full rounded-xl border border-zinc-800 bg-zinc-900/70 px-3 py-2 text-xs text-zinc-300 focus:border-purple-500 focus:outline-none"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Call to Action Card */}
              <div className="glass-card rounded-2xl p-5 border-zinc-800 flex items-start gap-3">
                <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                  <ArrowRight className="h-4 w-4" />
                </div>
                <div className="flex-1">
                  <span className="block text-[11px] font-semibold uppercase tracking-wider text-zinc-500 mb-0.5">
                    Ending Call To Action (CTA)
                  </span>
                  <input
                    type="text"
                    value={plannedStory.cta}
                    onChange={(e) => setPlannedStory({ ...plannedStory, cta: e.target.value })}
                    className="w-full text-xs font-semibold text-white bg-zinc-900/60 border border-zinc-800 rounded-lg px-3 py-1.5 focus:border-purple-500 focus:outline-none"
                  />
                </div>
              </div>

              {/* Bottom Sticky Action Bar */}
              <div className="glass-card rounded-2xl p-4 border-zinc-800 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-2xl">
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={handleRegenerateStory}
                    disabled={isRegeneratingStory}
                    className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-xs font-semibold text-zinc-300 hover:text-white bg-zinc-900 border border-zinc-800 hover:border-zinc-700 transition-all disabled:opacity-50"
                  >
                    <RefreshCw className={`h-3.5 w-3.5 ${isRegeneratingStory ? "animate-spin" : ""}`} />
                    <span>Regenerate Story</span>
                  </button>

                  {activeProjectId && (
                    <button
                      type="button"
                      onClick={() => router.push(`/projects/${activeProjectId}`)}
                      className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-xs font-semibold text-zinc-300 hover:text-white bg-zinc-900 border border-zinc-800 hover:border-zinc-700 transition-all"
                    >
                      <Edit3 className="h-3.5 w-3.5" />
                      <span>Edit in Project Editor</span>
                    </button>
                  )}
                </div>

                {/* Primary CTA: Generate Reel */}
                <button
                  type="button"
                  onClick={handleApproveAndRender}
                  className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-purple-600 via-indigo-600 to-purple-600 hover:from-purple-500 hover:to-indigo-500 text-sm font-bold text-white shadow-xl shadow-purple-500/25 transition-all active:scale-98"
                >
                  <Sparkles className="h-4 w-4" />
                  <span>Generate Reel →</span>
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function CreatePage() {
  return (
    <Suspense fallback={
      <div className="mx-auto max-w-7xl px-4 py-20 text-center">
        <div className="h-8 w-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin mx-auto mb-4" />
        <p className="text-sm text-zinc-400">Loading creator...</p>
      </div>
    }>
      <CreatePageContent />
    </Suspense>
  );
}
