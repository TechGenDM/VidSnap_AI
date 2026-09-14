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
  Wand2,
  Film,
  Sparkle,
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
  visual_url?: string;
  visual_filename?: string;
  visual_plan?: VisualPlanData;
  motion?: string;
  transition?: string;
  visual_source?: string;
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

// 4-Step Navigational flow for AI Reel
type StudioStep = 1 | 2 | 3 | 4;

const RENDER_STEPS = [
  { key: "understanding", label: "Structuring narrative & story flow" },
  { key: "voice", label: "Synthesizing voice narration" },
  { key: "captions", label: "Aligning speech-synchronized captions" },
  { key: "visuals", label: "Composing visuals, transitions & motion" },
  { key: "rendering", label: "Rendering 1080×1920 vertical video" },
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

// Quick inspiration prompts for Step 1
const IDEA_CHIPS = [
  "Explain why AI agents are changing software development.",
  "3 counter-intuitive habits that doubled my productivity.",
  "How next-generation battery tech is unlocking electric flight.",
  "The biggest mistake early founders make when pitching.",
];

function CreatePageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialMode = searchParams.get("mode") === "ai" ? "ai" : "quick";
  const templateKey = searchParams.get("template");

  // Mode Selection
  const [activeMode, setActiveMode] = useState<"quick" | "ai" | "repurpose">(initialMode);
  
  // Navigational 4-Step Studio Flow (Idea -> Story -> Style -> Generate)
  const [currentStep, setCurrentStep] = useState<StudioStep>(1);

  // General Status & Errors
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [errorAction, setErrorAction] = useState<"retry_story" | "retry_render" | "fallback_stock" | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isLoadingSamples, setIsLoadingSamples] = useState(false);

  // Selected Scene for the companion phone preview (Story <-> Video connection)
  const [selectedSceneIndex, setSelectedSceneIndex] = useState<number>(0);

  // Mobile View Switcher between Storyboard & Preview on small screens
  const [mobileActiveTab, setMobileActiveTab] = useState<"storyboard" | "preview">("storyboard");

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

  // AI Reel State (Step 1: Idea)
  const [aiPrompt, setAiPrompt] = useState(
    "Explain why AI agents are changing software development."
  );
  const [aiAudience, setAiAudience] = useState("Tech Creators");
  const [aiTone, setAiTone] = useState("Educational");
  const [aiLength, setAiLength] = useState("30s");
  const [aiVisualSource, setAiVisualSource] = useState("auto"); // "auto" | "ai" | "local"

  // AI Reel State (Step 2: Story)
  const [isPlanning, setIsPlanning] = useState(false);
  const [plannedStory, setPlannedStory] = useState<PlannedStory | null>(null);
  const [isRegeneratingStory, setIsRegeneratingStory] = useState(false);
  const [reviewFeedback, setReviewFeedback] = useState<string | null>(null);

  // AI Reel State (Step 3: Style - Human Concepts)
  const [humanVisualStyle, setHumanVisualStyle] = useState<"Cinematic" | "Clean" | "Vibrant" | "Documentary">("Cinematic");
  const [humanMotion, setHumanMotion] = useState<"Subtle" | "Dynamic" | "Cinematic">("Subtle");
  const [humanCaptions, setHumanCaptions] = useState<"Kinetic" | "Highlight" | "Minimal">("Kinetic");
  const [humanMusic, setHumanMusic] = useState<"Ambient" | "Upbeat" | "Lo-Fi" | "None">("Ambient");
  const [aiVoice, setAiVoice] = useState("adam");

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

  // Word count & duration calculation for Quick Reel
  const quickWordCount = script.trim() ? script.trim().split(/\s+/).length : 0;
  const quickEstimatedSecs = Math.max(3, Math.round((quickWordCount / 140) * 60));

  // Translate Human Style to Backend Parameters
  const getBackendStyleParams = () => {
    const styleMap: Record<string, string> = {
      Cinematic: "cinematic",
      Clean: "minimal",
      Vibrant: "dynamic",
      Documentary: "documentary",
    };
    const musicMap: Record<string, string> = {
      Ambient: "ambient_chill",
      Upbeat: "upbeat_pulse",
      "Lo-Fi": "lofi_beat",
      None: "none",
    };
    return {
      style: styleMap[humanVisualStyle] || "cinematic",
      music: musicMap[humanMusic] || "ambient_chill",
      motion: humanMotion.toLowerCase(),
      captions: humanCaptions.toLowerCase(),
    };
  };

  // Multi-Image Upload for Quick Reel
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

  const moveImage = (index: number, direction: "up" | "down") => {
    const targetIndex = direction === "up" ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= uploadedImages.length) return;

    setUploadedImages((prev) => {
      const copy = [...prev];
      const [moved] = copy.splice(index, 1);
      copy.splice(targetIndex, 0, moved);
      return copy;
    });
    if (selectedSceneIndex === index) {
      setSelectedSceneIndex(targetIndex);
    }
  };

  const removeImage = (index: number) => {
    setUploadedImages((prev) => {
      const copy = [...prev];
      URL.revokeObjectURL(copy[index].previewUrl);
      copy.splice(index, 1);
      return copy;
    });
    if (selectedSceneIndex >= uploadedImages.length - 1) {
      setSelectedSceneIndex(Math.max(0, uploadedImages.length - 2));
    }
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
      setErrorAction("retry_render");
      setIsSubmitting(false);
    }
  };

  // Step 1 -> Step 2: Generate AI Story (Idea -> Storyboard)
  const handleAiStoryGenerate = async () => {
    if (!aiPrompt.trim()) {
      setErrorMsg("Please describe what you want to create.");
      return;
    }

    setIsPlanning(true);
    setErrorMsg(null);
    setErrorAction(null);
    setReviewFeedback(null);

    try {
      const backendParams = getBackendStyleParams();
      const res = await fetch("/api/reels/ai", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: aiPrompt,
          audience: aiAudience,
          tone: aiTone,
          length: aiLength,
          visual_style: backendParams.style,
          voice: aiVoice,
          music: backendParams.music,
          visual_source: aiVisualSource,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to generate AI story.");
      }

      const data = await res.json();
      // Enrich story scenes with visual URLs if returned in data.scenes
      const enrichedScenes: StorySceneItem[] = data.story.scenes.map((s: any, idx: number) => {
        const matched = data.scenes && data.scenes[idx] ? data.scenes[idx] : {};
        return {
          ...s,
          visual_url: matched.visual_url || `/media/templates/${((idx % 5) + 1)}.jpg`,
          visual_filename: matched.visual_filename || `scene_${idx + 1}.jpg`,
          visual_source: matched.visual_source || "stock",
          visual_plan: matched.visual_plan || s.visual_plan,
          motion: matched.motion || "slow_zoom_in",
          transition: matched.transition || "crossfade",
        };
      });

      setPlannedStory({
        ...data.story,
        scenes: enrichedScenes,
      });
      setActiveProjectId(data.project_id);
      setSelectedSceneIndex(0);
      // Advance to Step 2 (Story)
      setCurrentStep(2);
    } catch (err: any) {
      setErrorMsg(err.message || "Could not plan AI Reel.");
      setErrorAction("retry_story");
    } finally {
      setIsPlanning(false);
    }
  };

  // Regenerate Entire Story (keeps same topic, creates new hook & scenes)
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
      const enrichedScenes: StorySceneItem[] = data.story.scenes.map((s: any, idx: number) => {
        const matched = data.scenes && data.scenes[idx] ? data.scenes[idx] : {};
        return {
          ...s,
          visual_url: matched.visual_url || `/media/templates/${((idx % 5) + 1)}.jpg`,
          visual_filename: matched.visual_filename || `scene_${idx + 1}.jpg`,
          visual_source: matched.visual_source || "stock",
          visual_plan: matched.visual_plan || s.visual_plan,
        };
      });
      setPlannedStory({
        ...data.story,
        scenes: enrichedScenes,
      });
      setSelectedSceneIndex(0);
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

  // Approve Story & Trigger Video Rendering (Step 4)
  const handleApproveAndRender = async () => {
    if (!activeProjectId || !plannedStory) return;
    setIsSubmitting(true);
    setErrorMsg(null);
    setErrorAction(null);
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
      setErrorAction("retry_render");
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
          setErrorAction("retry_render");
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
        ? 5
        : jobProgress >= 80
        ? 4
        : jobProgress >= 60
        ? 3
        : jobProgress >= 40
        ? 2
        : jobProgress >= 20
        ? 1
        : 0;

    if (stepIndex < activeIndex) return "completed";
    if (stepIndex === activeIndex) return "active";
    return "pending";
  };

  // Current active scene in Storyboard for preview
  const currentScene: StorySceneItem | null =
    plannedStory && plannedStory.scenes.length > 0
      ? plannedStory.scenes[selectedSceneIndex] || plannedStory.scenes[0]
      : null;

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8 w-full">
      {/* 1. STUDIO HEADER */}
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold uppercase tracking-wider text-cyan-400 font-mono">
              VidSnap Studio
            </span>
            <span className="text-zinc-600">•</span>
            <span className="text-xs text-zinc-400">Story-First Vertical Video</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
            What are we creating today?
          </h1>
        </div>

        {/* Mode Selector Tabs */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-white/[0.04] border border-white/[0.08] self-start sm:self-auto">
          <button
            onClick={() => {
              setActiveMode("quick");
              setErrorMsg(null);
            }}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeMode === "quick"
                ? "bg-white/[0.1] text-white shadow-sm border border-white/[0.15]"
                : "text-zinc-400 hover:text-white"
            }`}
          >
            <Zap className="h-3.5 w-3.5 text-cyan-400" />
            <span>Quick Reel</span>
          </button>

          <button
            onClick={() => {
              setActiveMode("ai");
              setErrorMsg(null);
            }}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeMode === "ai"
                ? "bg-white/[0.1] text-white shadow-sm border border-white/[0.15]"
                : "text-zinc-400 hover:text-white"
            }`}
          >
            <Bot className="h-3.5 w-3.5 text-purple-400" />
            <span>AI Reel</span>
          </button>

          <button
            disabled
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-zinc-600 cursor-not-allowed"
          >
            <Repeat className="h-3 w-3" />
            <span>Repurpose</span>
          </button>
        </div>
      </div>

      {/* 2. NON-LINEAR 4-STEP BREADCRUMB NAVIGATION (For AI Reel) */}
      {activeMode === "ai" && jobStatus !== "completed" && (
        <nav aria-label="Creation Steps" className="mb-8 p-1.5 rounded-2xl glass-card flex items-center justify-between overflow-x-auto">
          {[
            { step: 1, label: "1. Idea", icon: Sparkles, unlocked: true },
            { step: 2, label: "2. Story", icon: Layers, unlocked: !!plannedStory },
            { step: 3, label: "3. Style", icon: Sliders, unlocked: !!plannedStory },
            { step: 4, label: "4. Generate", icon: Wand2, unlocked: !!plannedStory },
          ].map((item) => {
            const Icon = item.icon;
            const isCurrent = currentStep === item.step;
            return (
              <button
                key={item.step}
                type="button"
                onClick={() => {
                  if (item.unlocked) {
                    setCurrentStep(item.step as StudioStep);
                    setErrorMsg(null);
                  }
                }}
                disabled={!item.unlocked}
                className={`flex-1 min-w-[120px] flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl text-xs font-bold transition-all ${
                  isCurrent
                    ? "bg-gradient-to-r from-cyan-500/20 via-indigo-500/20 to-purple-500/20 text-white border border-cyan-500/40 shadow-sm"
                    : item.unlocked
                    ? "text-zinc-400 hover:text-white hover:bg-white/[0.04]"
                    : "text-zinc-650 opacity-40 cursor-not-allowed"
                }`}
              >
                <Icon className={`h-3.5 w-3.5 ${isCurrent ? "text-cyan-400" : "text-zinc-500"}`} />
                <span>{item.label}</span>
                {item.unlocked && item.step < (plannedStory ? 4 : 2) && (
                  <Check className="h-3 w-3 text-emerald-400/80 ml-0.5" />
                )}
              </button>
            );
          })}
        </nav>
      )}

      {/* ERROR BANNER WITH RECOVERY ACTIONS */}
      {errorMsg && (
        <div className="mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-2xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-200 animate-fadeIn">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
          <div className="flex items-center gap-2 self-end sm:self-auto">
            {errorAction === "retry_story" && (
              <button
                type="button"
                onClick={handleAiStoryGenerate}
                className="px-3 py-1.5 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-xs font-semibold text-red-100 transition-colors"
              >
                Try Again
              </button>
            )}
            {errorAction === "retry_render" && (
              <button
                type="button"
                onClick={activeMode === "quick" ? handleQuickReelSubmit : handleApproveAndRender}
                className="px-3 py-1.5 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-xs font-semibold text-red-100 transition-colors"
              >
                Retry Render
              </button>
            )}
            <button
              type="button"
              onClick={() => setErrorMsg(null)}
              className="p-1.5 rounded-lg text-red-400 hover:text-red-200"
              aria-label="Dismiss Error"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* LIVE RENDERING MODAL */}
      {isSubmitting && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-4">
          <div className="glass-card rounded-2xl max-w-lg w-full p-8 border-cyan-500/40 shadow-2xl relative overflow-hidden">
            <div className="flex items-center gap-3 mb-6">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-500/20 text-cyan-400 animate-pulse">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Rendering Reel</h3>
                <p className="text-xs text-zinc-400">{jobStep}</p>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-zinc-800 h-2 rounded-full mb-6 overflow-hidden">
              <div
                className="bg-gradient-to-r from-cyan-400 via-indigo-500 to-purple-500 h-full rounded-full transition-all duration-300"
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
                      <div className="h-5 w-5 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin flex-shrink-0" />
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
              VidSnap is generating 1080×1920 MP4 with blurred background padding and audio ducking...
            </p>
          </div>
        </div>
      )}

      {/* 3. RESULT EXPERIENCE (PAYOFF SCREEN) */}
      {jobStatus === "completed" && renderedVideoUrl && (
        <div className="mb-12 glass-card rounded-3xl p-6 sm:p-10 border-emerald-500/40 bg-zinc-950/90 shadow-2xl animate-fadeIn">
          <div className="flex flex-col lg:flex-row items-center gap-10">
            {/* Large Phone Player Preview */}
            <div className="phone-mockup flex-shrink-0 shadow-2xl">
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

            {/* Payoff Info & Actions */}
            <div className="flex-1 flex flex-col items-start">
              <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3.5 py-1 text-xs font-semibold text-emerald-400 mb-4">
                <CheckCircle2 className="h-4 w-4" />
                <span>1080×1920 HD Ready</span>
              </div>

              <h2 className="text-3xl sm:text-4xl font-extrabold text-white mb-3 tracking-tight">
                Your Reel is ready.
              </h2>

              <p className="text-sm text-zinc-300 mb-6 max-w-lg leading-relaxed">
                Rendered with kinetic speech-synchronized captions, cinematic motion, and background music ducking.
              </p>

              {/* Reel Metrics */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 w-full max-w-lg mb-8">
                <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-3 text-left">
                  <span className="text-[11px] text-zinc-400 block mb-1">Duration</span>
                  <span className="text-base font-bold text-white">
                    {plannedStory ? `~${plannedStory.estimated_duration}s` : `~${quickEstimatedSecs}s`}
                  </span>
                </div>
                <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-3 text-left">
                  <span className="text-[11px] text-zinc-400 block mb-1">Scenes</span>
                  <span className="text-base font-bold text-white">
                    {plannedStory ? plannedStory.scenes.length : uploadedImages.length}
                  </span>
                </div>
                <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-3 text-left">
                  <span className="text-[11px] text-zinc-400 block mb-1">Resolution</span>
                  <span className="text-base font-bold text-white">1080×1920</span>
                </div>
                <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-3 text-left">
                  <span className="text-[11px] text-zinc-400 block mb-1">Voice</span>
                  <span className="text-base font-bold text-white capitalize">
                    {activeMode === "ai" ? aiVoice : voice}
                  </span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 w-full max-w-lg">
                <a
                  href={renderedVideoUrl}
                  download="vidsnap_reel.mp4"
                  className="flex-1 flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 px-6 py-3.5 text-sm font-bold text-white shadow-xl shadow-cyan-500/25 transition-all active:scale-98"
                >
                  <Download className="h-4 w-4" />
                  <span>Download MP4</span>
                </a>

                {activeProjectId && (
                  <Link
                    href={`/projects/${activeProjectId}`}
                    className="flex-1 flex items-center justify-center gap-2 rounded-xl border border-white/[0.15] bg-white/[0.05] hover:bg-white/[0.1] px-5 py-3.5 text-sm font-semibold text-white transition-all"
                  >
                    <Sliders className="h-4 w-4" />
                    <span>Edit Story</span>
                  </Link>
                )}
              </div>

              <button
                type="button"
                onClick={() => {
                  setJobStatus(null);
                  setRenderedVideoUrl(null);
                  setUploadedImages([]);
                  setPlannedStory(null);
                  setCurrentStep(1);
                  if (typeof window !== "undefined") {
                    sessionStorage.removeItem("vidsnap_active_job_id");
                    sessionStorage.removeItem("vidsnap_active_project_id");
                  }
                }}
                className="mt-4 flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                <span>Create Another Reel</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 4. QUICK REEL MODE */}
      {activeMode === "quick" && jobStatus !== "completed" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: Upload & Script */}
          <div className="lg:col-span-7 flex flex-col gap-6">
            {/* Upload Box */}
            <div className="glass-card rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2.5">
                  <ImageIcon className="h-5 w-5 text-cyan-400" />
                  <h2 className="text-base font-bold text-white">Visual Assets</h2>
                </div>
                <span className="text-xs font-semibold text-zinc-400 bg-white/[0.05] px-2.5 py-1 rounded-full border border-white/[0.08]">
                  {uploadedImages.length} {uploadedImages.length === 1 ? "image" : "images"}
                </span>
              </div>

              <label
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`relative flex flex-col items-center justify-center w-full min-h-[140px] rounded-xl border-2 border-dashed transition-all p-6 text-center group cursor-pointer ${
                  isDragging
                    ? "border-cyan-400 bg-cyan-500/10 scale-[1.01]"
                    : "border-white/[0.1] hover:border-cyan-500/50 bg-white/[0.02] hover:bg-white/[0.04]"
                }`}
              >
                <UploadCloud
                  className={`h-9 w-9 transition-colors mb-2.5 ${
                    isDragging ? "text-cyan-400 animate-bounce" : "text-zinc-500 group-hover:text-cyan-400"
                  }`}
                />
                <span className="text-sm font-semibold text-zinc-200 mb-1">
                  {isDragging ? "Drop images here" : "Drop photos or click to browse"}
                </span>
                <span className="text-xs text-zinc-500">
                  JPG, PNG, WebP up to 25MB each
                </span>
                <input
                  type="file"
                  multiple
                  accept="image/jpeg,image/png,image/webp"
                  className="hidden"
                  onChange={(e) => handleFileSelect(e.target.files)}
                />
              </label>

              <div className="mt-3 flex items-center justify-between">
                <span className="text-xs text-zinc-500">Need test visuals?</span>
                <button
                  type="button"
                  onClick={handleLoadSampleImages}
                  disabled={isLoadingSamples}
                  className="flex items-center gap-1.5 text-xs text-cyan-400 hover:text-cyan-300 font-medium px-2.5 py-1 rounded-lg bg-cyan-500/10 border border-cyan-500/20 hover:bg-cyan-500/20 transition-all disabled:opacity-50"
                >
                  <Sparkles className="h-3 w-3" />
                  <span>{isLoadingSamples ? "Loading..." : "Load Sample Photos"}</span>
                </button>
              </div>

              {/* Uploaded Thumbnails List */}
              {uploadedImages.length > 0 && (
                <div className="mt-5 flex flex-col gap-2">
                  <span className="text-xs text-zinc-400 px-1">
                    Click a scene to focus companion preview:
                  </span>
                  <div className="grid grid-cols-1 gap-2 max-h-[280px] overflow-y-auto pr-1">
                    {uploadedImages.map((item, idx) => (
                      <div
                        key={item.id}
                        onClick={() => setSelectedSceneIndex(idx)}
                        className={`flex items-center justify-between p-2.5 rounded-xl border transition-all cursor-pointer ${
                          selectedSceneIndex === idx
                            ? "border-cyan-400/80 bg-cyan-500/10 shadow-sm"
                            : "border-white/[0.08] bg-white/[0.02] hover:border-white/[0.15]"
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-xs font-mono font-bold text-zinc-400 w-5 text-center">
                            #{idx + 1}
                          </span>
                          <img
                            src={item.previewUrl}
                            alt="Preview"
                            className="h-10 w-10 rounded-lg object-cover border border-white/[0.1]"
                          />
                          <span className="text-xs font-medium text-white truncate max-w-[180px]">
                            {item.file.name}
                          </span>
                        </div>

                        <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                          <button
                            type="button"
                            disabled={idx === 0}
                            onClick={() => moveImage(idx, "up")}
                            className="p-1 rounded-lg text-zinc-400 hover:text-white disabled:opacity-30"
                            aria-label={`Move image ${idx + 1} up`}
                          >
                            <ArrowUp className="h-3.5 w-3.5" />
                          </button>
                          <button
                            type="button"
                            disabled={idx === uploadedImages.length - 1}
                            onClick={() => moveImage(idx, "down")}
                            className="p-1 rounded-lg text-zinc-400 hover:text-white disabled:opacity-30"
                            aria-label={`Move image ${idx + 1} down`}
                          >
                            <ArrowDown className="h-3.5 w-3.5" />
                          </button>
                          <button
                            type="button"
                            onClick={() => removeImage(idx)}
                            className="p-1 rounded-lg text-red-400 hover:bg-red-500/10 ml-1"
                            aria-label={`Delete image ${idx + 1}`}
                          >
                            <X className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Script Box */}
            <div className="glass-card rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2.5">
                  <Mic className="h-5 w-5 text-cyan-400" />
                  <h2 className="text-base font-bold text-white">Narration Script</h2>
                </div>
                <span className="text-xs text-zinc-400 font-mono">
                  ~{quickEstimatedSecs}s est. duration
                </span>
              </div>

              <textarea
                rows={4}
                value={script}
                onChange={(e) => setScript(e.target.value)}
                placeholder="Enter voiceover script here..."
                className="w-full rounded-xl border border-white/[0.1] bg-white/[0.02] p-3.5 text-sm text-zinc-100 placeholder-zinc-500 focus:border-cyan-400 focus:outline-none resize-none leading-relaxed mb-4"
              />

              {/* Controls */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="block text-xs font-semibold text-zinc-300 mb-1.5">
                    Narration Voice
                  </label>
                  <select
                    value={voice}
                    onChange={(e) => setVoice(e.target.value)}
                    className="w-full rounded-xl border border-white/[0.1] bg-zinc-900 px-3.5 py-2 text-xs text-white focus:border-cyan-400 focus:outline-none"
                  >
                    <option value="adam">Adam (Narrative Deep)</option>
                    <option value="rachel">Rachel (Warm & Clear)</option>
                    <option value="josh">Josh (Energetic)</option>
                    <option value="antoni">Antoni (Thoughtful)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-zinc-300 mb-1.5">
                    Background Music
                  </label>
                  <select
                    value={music}
                    onChange={(e) => setMusic(e.target.value)}
                    className="w-full rounded-xl border border-white/[0.1] bg-zinc-900 px-3.5 py-2 text-xs text-white focus:border-cyan-400 focus:outline-none"
                  >
                    <option value="ambient_chill">Ambient Chill (Ducked)</option>
                    <option value="upbeat_pulse">Upbeat Pulse (Ducked)</option>
                    <option value="lofi_beat">Lo-Fi Beat (Ducked)</option>
                    <option value="none">None (Voice Only)</option>
                  </select>
                </div>
              </div>

              <button
                type="button"
                onClick={handleQuickReelSubmit}
                disabled={uploadedImages.length === 0 || !script.trim()}
                className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 via-indigo-600 to-purple-600 py-3.5 text-sm font-bold text-white shadow-xl shadow-cyan-500/20 hover:from-cyan-400 hover:to-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all active:scale-98"
              >
                <Sparkles className="h-4 w-4" />
                <span>Generate Reel (1080×1920) →</span>
              </button>
            </div>
          </div>

          {/* Right Column: Companion Preview */}
          <div className="lg:col-span-5 flex flex-col items-center sticky top-24">
            <div className="phone-mockup relative">
              <div className="phone-notch" />
              {uploadedImages.length > 0 && uploadedImages[selectedSceneIndex] ? (
                <div className="relative w-full h-full bg-zinc-950 flex flex-col justify-between overflow-hidden">
                  <img
                    src={uploadedImages[selectedSceneIndex].previewUrl}
                    alt="Current Scene Visual"
                    className="absolute inset-0 w-full h-full object-cover"
                  />
                  <div className="absolute top-12 left-4 right-4 flex items-center justify-between z-30">
                    <span className="bg-black/75 backdrop-blur-md px-2 py-0.5 rounded text-[11px] font-mono font-bold text-white border border-white/10">
                      Scene #{selectedSceneIndex + 1}
                    </span>
                    <span className="bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 backdrop-blur-md px-2 py-0.5 rounded text-[10px] font-bold uppercase">
                      Storyboard Preview
                    </span>
                  </div>
                  <div className="phone-caption-overlay">
                    <p className="text-xs font-bold text-white leading-snug drop-shadow-md">
                      {script.slice(0, 70)}...
                    </p>
                  </div>
                </div>
              ) : (
                <div className="w-full h-full flex flex-col items-center justify-center p-6 text-center text-zinc-500 bg-zinc-950">
                  <Film className="h-10 w-10 text-zinc-600 mb-3" />
                  <span className="text-xs font-semibold text-zinc-300 mb-1">
                    Storyboard Companion Preview
                  </span>
                  <span className="text-[11px] text-zinc-500">
                    Upload images to see scene slides previewed in real-time.
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 5. AI REEL MODE (4-STEP STUDIO EXPERIENCE) */}
      {activeMode === "ai" && jobStatus !== "completed" && (
        <div className="w-full">
          {/* STEP 1: IDEA INPUT */}
          {currentStep === 1 && (
            <div className="max-w-3xl mx-auto glass-card rounded-3xl p-6 sm:p-10 border-white/[0.1] shadow-2xl animate-fadeIn">
              <div className="flex items-center gap-3.5 mb-6">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-500/20 via-indigo-500/20 to-purple-500/20 text-cyan-300 border border-cyan-500/30">
                  <Bot className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white tracking-tight">Step 1 — Shape Your Idea</h2>
                  <p className="text-xs text-zinc-400">
                    VidSnap transforms raw topics into high-retention hooks, multi-scene storyboards, and visuals.
                  </p>
                </div>
              </div>

              {/* Topic Prompt Textarea */}
              <div className="mb-4">
                <label htmlFor="ai-prompt-input" className="block text-xs font-semibold text-zinc-300 mb-2">
                  What is your Reel about?
                </label>
                <textarea
                  id="ai-prompt-input"
                  rows={4}
                  value={aiPrompt}
                  onChange={(e) => setAiPrompt(e.target.value)}
                  placeholder="e.g. “Explain why AI agents are changing software development.”"
                  className="w-full rounded-2xl border border-white/[0.1] bg-white/[0.02] p-4 text-sm text-zinc-100 placeholder-zinc-500 focus:border-cyan-400 focus:outline-none resize-none leading-relaxed transition-all"
                />
              </div>

              {/* Quick Inspiration Chips */}
              <div className="mb-8">
                <span className="block text-[11px] text-zinc-500 mb-2">Need inspiration? Click a concept:</span>
                <div className="flex flex-wrap gap-2">
                  {IDEA_CHIPS.map((chip) => (
                    <button
                      key={chip}
                      type="button"
                      onClick={() => setAiPrompt(chip)}
                      className="text-left text-[11px] text-zinc-300 hover:text-white bg-white/[0.03] hover:bg-white/[0.08] border border-white/[0.08] hover:border-cyan-500/40 rounded-xl px-3 py-1.5 transition-all"
                    >
                      {chip}
                    </button>
                  ))}
                </div>
              </div>

              {/* Creative Controls Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                <div>
                  <label className="block text-xs font-semibold text-zinc-300 mb-1.5">
                    Target Audience
                  </label>
                  <select
                    value={aiAudience}
                    onChange={(e) => setAiAudience(e.target.value)}
                    className="w-full rounded-xl border border-white/[0.1] bg-zinc-900 px-3 py-2 text-xs text-white focus:border-cyan-400 focus:outline-none"
                  >
                    <option value="Tech Creators">Tech Creators</option>
                    <option value="General Audience">General Audience</option>
                    <option value="Startup Founders">Startup Founders</option>
                    <option value="Students & Learners">Students & Learners</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-zinc-300 mb-1.5">
                    Narrative Tone
                  </label>
                  <select
                    value={aiTone}
                    onChange={(e) => setAiTone(e.target.value)}
                    className="w-full rounded-xl border border-white/[0.1] bg-zinc-900 px-3 py-2 text-xs text-white focus:border-cyan-400 focus:outline-none"
                  >
                    <option value="Educational">Educational & Calm</option>
                    <option value="High Energy">High Energy (Punchy)</option>
                    <option value="Thought-Provoking">Thought-Provoking</option>
                    <option value="Documentary Story">Documentary Story</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-zinc-300 mb-1.5">
                    Target Duration
                  </label>
                  <select
                    value={aiLength}
                    onChange={(e) => setAiLength(e.target.value)}
                    className="w-full rounded-xl border border-white/[0.1] bg-zinc-900 px-3 py-2 text-xs text-white focus:border-cyan-400 focus:outline-none"
                  >
                    <option value="15s">15 seconds (Viral Hook)</option>
                    <option value="30s">30 seconds (Standard Reel)</option>
                    <option value="60s">60 seconds (Deep Dive)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-zinc-300 mb-1.5">
                    Visual Source
                  </label>
                  <select
                    value={aiVisualSource}
                    onChange={(e) => setAiVisualSource(e.target.value)}
                    className="w-full rounded-xl border border-white/[0.1] bg-zinc-900 px-3 py-2 text-xs text-white focus:border-cyan-400 focus:outline-none"
                  >
                    <option value="auto">Smart (Fast & Curated)</option>
                    <option value="ai">Real AI Visuals</option>
                    <option value="local">Stock Library</option>
                  </select>
                </div>
              </div>

              {/* Build Story Button */}
              <button
                type="button"
                onClick={handleAiStoryGenerate}
                disabled={!aiPrompt.trim() || isPlanning}
                className="w-full flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-cyan-500 via-indigo-600 to-purple-600 py-4 text-sm font-bold text-white shadow-xl shadow-cyan-500/25 hover:from-cyan-400 hover:to-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all active:scale-98"
              >
                {isPlanning ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin text-cyan-200" />
                    <span>Structuring Story & Matching Visuals...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    <span>Build Storyboard →</span>
                  </>
                )}
              </button>
            </div>
          )}

          {/* STEP 2: STORYBOARD & STORY <-> VIDEO COMPANION PREVIEW */}
          {currentStep === 2 && plannedStory && (
            <div className="w-full">
              {/* Mobile View Toggle */}
              <div className="lg:hidden flex items-center gap-1.5 p-1 mb-6 rounded-xl bg-white/[0.04] border border-white/[0.08]">
                <button
                  type="button"
                  onClick={() => setMobileActiveTab("storyboard")}
                  className={`flex-1 py-2 rounded-lg text-xs font-bold transition-all ${
                    mobileActiveTab === "storyboard"
                      ? "bg-white/[0.1] text-white border border-white/[0.15]"
                      : "text-zinc-400 hover:text-white"
                  }`}
                >
                  Storyboard Scenes ({plannedStory.scenes.length})
                </button>
                <button
                  type="button"
                  onClick={() => setMobileActiveTab("preview")}
                  className={`flex-1 py-2 rounded-lg text-xs font-bold transition-all ${
                    mobileActiveTab === "preview"
                      ? "bg-white/[0.1] text-white border border-white/[0.15]"
                      : "text-zinc-400 hover:text-white"
                  }`}
                >
                  Phone Preview
                </button>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
                {/* Left Column: Storyboard Scene Cards */}
                <div className={`lg:col-span-7 flex flex-col gap-6 ${mobileActiveTab === "preview" ? "hidden lg:flex" : "flex"}`}>
                  {/* Human Review Banner */}
                  <div className="p-5 glass-card rounded-2xl border-cyan-500/30 bg-gradient-to-r from-cyan-950/20 via-zinc-900/60 to-purple-950/20 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                          <Eye className="h-3 w-3" />
                          Human Review Point
                        </span>
                        <span className="text-xs text-zinc-400 font-mono">
                          ~{plannedStory.estimated_duration}s • {plannedStory.scenes.length} scenes
                        </span>
                      </div>
                      <h2 className="text-lg font-bold text-white tracking-tight">
                        Review & Refine Story
                      </h2>
                      <p className="text-xs text-zinc-400">
                        Selecting any scene immediately updates the vertical preview.
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={handleRegenerateStory}
                        disabled={isRegeneratingStory}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-purple-300 hover:text-white bg-purple-500/10 border border-purple-500/30 hover:bg-purple-500/20 transition-all disabled:opacity-50"
                      >
                        <RefreshCw className={`h-3.5 w-3.5 ${isRegeneratingStory ? "animate-spin" : ""}`} />
                        <span>{isRegeneratingStory ? "Regenerating..." : "Regenerate Story"}</span>
                      </button>
                    </div>
                  </div>

                  {reviewFeedback && (
                    <div className="flex items-center gap-2 p-3 rounded-xl border border-emerald-500/30 bg-emerald-500/10 text-xs font-medium text-emerald-300 animate-fadeIn">
                      <Check className="h-4 w-4 text-emerald-400" />
                      <span>{reviewFeedback}</span>
                    </div>
                  )}

                  {/* Title & Opening Hook Card */}
                  <div className="glass-card rounded-2xl p-5 border-white/[0.08] space-y-3">
                    <div>
                      <label className="block text-[11px] font-semibold uppercase tracking-wider text-zinc-500 mb-1">
                        Reel Title
                      </label>
                      <input
                        type="text"
                        value={plannedStory.title}
                        onChange={(e) => setPlannedStory({ ...plannedStory, title: e.target.value })}
                        className="w-full text-base font-bold text-white bg-white/[0.02] border border-white/[0.1] rounded-xl px-3.5 py-2 focus:border-cyan-400 focus:outline-none"
                      />
                    </div>

                    <div className="p-3.5 rounded-xl bg-purple-500/10 border border-purple-500/25">
                      <div className="flex items-center gap-1.5 text-xs font-bold text-purple-300 mb-1">
                        <Flame className="h-3.5 w-3.5 text-amber-400" />
                        <span>Opening Hook (First 2 Seconds)</span>
                      </div>
                      <p className="text-xs font-medium text-purple-100 leading-relaxed">
                        “{plannedStory.hook}”
                      </p>
                    </div>
                  </div>

                  {/* Scene Flow Cards */}
                  <div className="space-y-3">
                    {plannedStory.scenes.map((s, idx) => {
                      const isSelected = selectedSceneIndex === idx;
                      return (
                        <div
                          key={s.order}
                          onClick={() => setSelectedSceneIndex(idx)}
                          className={`glass-card rounded-2xl p-5 transition-all cursor-pointer ${
                            isSelected
                              ? "glass-card-active"
                              : "border-white/[0.08] hover:border-white/[0.15]"
                          }`}
                        >
                          <div className="flex items-center justify-between flex-wrap gap-2 mb-3">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span
                                className={`px-2 py-0.5 rounded-md text-[11px] font-mono font-bold ${
                                  isSelected
                                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                                    : "bg-zinc-800 text-zinc-300 border border-zinc-700"
                                }`}
                              >
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
                              <span className="text-[11px] text-zinc-400 font-mono">
                                ~{s.estimated_duration}s
                              </span>
                            </div>

                            <span className="text-[11px] text-cyan-400/90 font-medium">
                              {s.visual_source === "ai"
                                ? "✨ AI Generated Visual"
                                : "📷 Matched Visual Asset"}
                            </span>
                          </div>

                          {/* Narration Script */}
                          <div className="mb-3" onClick={(e) => e.stopPropagation()}>
                            <label className="block text-[11px] font-semibold text-zinc-400 mb-1">
                              Narration Script
                            </label>
                            <textarea
                              rows={2}
                              value={s.narration}
                              onChange={(e) => handlePlannedSceneChange(s.order, "narration", e.target.value)}
                              className="w-full rounded-xl border border-white/[0.1] bg-white/[0.02] p-2.5 text-xs text-white placeholder-zinc-500 focus:border-cyan-400 focus:outline-none resize-none leading-relaxed"
                            />
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3" onClick={(e) => e.stopPropagation()}>
                            {/* Caption Overlay */}
                            <div>
                              <label className="block text-[11px] font-semibold text-zinc-400 mb-1">
                                Screen Caption
                              </label>
                              <input
                                type="text"
                                value={s.caption}
                                onChange={(e) => handlePlannedSceneChange(s.order, "caption", e.target.value)}
                                className="w-full rounded-xl border border-white/[0.1] bg-white/[0.02] px-3 py-1.5 text-xs font-semibold text-white focus:border-cyan-400 focus:outline-none"
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
                                className="w-full rounded-xl border border-white/[0.1] bg-white/[0.02] px-3 py-1.5 text-xs text-zinc-300 focus:border-cyan-400 focus:outline-none"
                              />
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Ending CTA */}
                  <div className="glass-card rounded-2xl p-4 border-white/[0.08] flex items-center gap-3">
                    <ArrowRight className="h-4 w-4 text-cyan-400 flex-shrink-0" />
                    <div className="flex-1">
                      <span className="block text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
                        Ending Call to Action (CTA)
                      </span>
                      <input
                        type="text"
                        value={plannedStory.cta}
                        onChange={(e) => setPlannedStory({ ...plannedStory, cta: e.target.value })}
                        className="w-full text-xs font-semibold text-white bg-transparent border-b border-white/[0.15] py-1 focus:border-cyan-400 focus:outline-none"
                      />
                    </div>
                  </div>

                  {/* Navigation Buttons */}
                  <div className="flex items-center justify-between pt-2">
                    <button
                      type="button"
                      onClick={() => setCurrentStep(1)}
                      className="px-4 py-2.5 rounded-xl text-xs font-semibold text-zinc-400 hover:text-white bg-white/[0.04] border border-white/[0.08] hover:bg-white/[0.08] transition-all"
                    >
                      ← Back to Idea
                    </button>

                    <button
                      type="button"
                      onClick={() => setCurrentStep(3)}
                      className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-xs font-bold text-white shadow-lg shadow-cyan-500/20 transition-all active:scale-98"
                    >
                      <span>Continue to Style</span>
                      <ChevronRight className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                {/* Right Column: Companion Phone Storyboard Preview */}
                <div className={`lg:col-span-5 flex flex-col items-center sticky top-24 ${mobileActiveTab === "storyboard" ? "hidden lg:flex" : "flex"}`}>
                  <div className="phone-mockup relative">
                    <div className="phone-notch" />

                    {currentScene ? (
                      <div className="relative w-full h-full bg-zinc-950 flex flex-col justify-between overflow-hidden">
                        {/* Selected Scene Image */}
                        <img
                          src={currentScene.visual_url || `/media/templates/${((selectedSceneIndex % 5) + 1)}.jpg`}
                          alt={`Scene ${currentScene.order}`}
                          className="absolute inset-0 w-full h-full object-cover"
                        />

                        {/* Top Storyboard Preview Badges */}
                        <div className="absolute top-12 left-4 right-4 flex items-center justify-between z-30">
                          <div className="flex items-center gap-1.5">
                            <span className="bg-black/75 backdrop-blur-md px-2 py-0.5 rounded text-[11px] font-mono font-bold text-white border border-white/10">
                              Scene #{currentScene.order}
                            </span>
                            {currentScene.scene_role && (
                              <span className="bg-purple-900/80 backdrop-blur-md px-2 py-0.5 rounded text-[10px] font-bold uppercase text-purple-200 border border-purple-500/20">
                                {currentScene.scene_role}
                              </span>
                            )}
                          </div>

                          <div className="flex items-center gap-1 bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 backdrop-blur-md px-2 py-0.5 rounded text-[10px] font-bold">
                            <Eye className="h-3 w-3" />
                            <span>PREVIEW</span>
                          </div>
                        </div>

                        {/* Middle Motion Indicator */}
                        <div className="absolute top-22 left-4 z-30">
                          <span className="bg-black/70 backdrop-blur-md px-2 py-0.5 rounded text-[10px] font-medium text-zinc-300 border border-white/10 capitalize">
                            🎬 Motion: {(currentScene.visual_plan?.motion || currentScene.motion || "Slow Zoom").replace(/_/g, " ")}
                          </span>
                        </div>

                        {/* Bottom Kinetic Caption Overlay */}
                        <div className="phone-caption-overlay">
                          <span className="text-[10px] uppercase font-bold text-cyan-400 block mb-0.5">
                            Kinetic Caption
                          </span>
                          <p className="text-xs font-bold text-white leading-snug drop-shadow-md">
                            {currentScene.caption || "CAPTION PREVIEW"}
                          </p>
                        </div>
                      </div>
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-zinc-500">
                        No scene selected
                      </div>
                    )}
                  </div>

                  {/* Scene Preview Meta Info */}
                  {currentScene && (
                    <div className="mt-4 w-full max-w-[320px] p-3 rounded-xl bg-white/[0.03] border border-white/[0.08] text-xs text-zinc-400 space-y-1">
                      <div className="flex justify-between">
                        <span>Duration:</span>
                        <span className="text-white font-mono">~{currentScene.estimated_duration}s</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Narration:</span>
                        <span className="text-zinc-300 truncate max-w-[200px]">{currentScene.narration}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Visual Type:</span>
                        <span className="text-zinc-300 capitalize">{currentScene.visual_plan?.visual_type || "cinematic_photo"}</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: CREATIVE STYLE CONTROLS (HUMAN CONCEPTS) */}
          {currentStep === 3 && plannedStory && (
            <div className="max-w-3xl mx-auto glass-card rounded-3xl p-6 sm:p-10 border-white/[0.1] shadow-2xl animate-fadeIn">
              <div className="flex items-center gap-3.5 mb-6">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500/20 via-purple-500/20 to-pink-500/20 text-indigo-300 border border-indigo-500/30">
                  <Sliders className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white tracking-tight">Step 3 — Presentation Style</h2>
                  <p className="text-xs text-zinc-400">
                    Choose high-level creative concepts. VidSnap automatically calibrates render parameters.
                  </p>
                </div>
              </div>

              <div className="space-y-6 mb-8">
                {/* Visual Style Concept */}
                <div>
                  <label className="block text-xs font-semibold text-zinc-300 mb-2">
                    Visual Presentation Style
                  </label>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {(["Cinematic", "Clean", "Vibrant", "Documentary"] as const).map((s) => (
                      <button
                        key={s}
                        type="button"
                        onClick={() => setHumanVisualStyle(s)}
                        className={`p-3 rounded-xl text-xs font-bold border transition-all text-center ${
                          humanVisualStyle === s
                            ? "bg-cyan-500/20 text-white border-cyan-400 shadow-sm shadow-cyan-500/20"
                            : "border-white/[0.08] bg-white/[0.02] text-zinc-400 hover:text-white hover:bg-white/[0.05]"
                        }`}
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Motion Concept */}
                <div>
                  <label className="block text-xs font-semibold text-zinc-300 mb-2">
                    Camera Motion & Pacing
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    {(["Subtle", "Dynamic", "Cinematic"] as const).map((m) => (
                      <button
                        key={m}
                        type="button"
                        onClick={() => setHumanMotion(m)}
                        className={`p-3 rounded-xl text-xs font-bold border transition-all text-center ${
                          humanMotion === m
                            ? "bg-indigo-500/20 text-white border-indigo-400 shadow-sm shadow-indigo-500/20"
                            : "border-white/[0.08] bg-white/[0.02] text-zinc-400 hover:text-white hover:bg-white/[0.05]"
                        }`}
                      >
                        {m}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Captions Concept */}
                <div>
                  <label className="block text-xs font-semibold text-zinc-300 mb-2">
                    Kinetic Captions Design
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    {(["Kinetic", "Highlight", "Minimal"] as const).map((c) => (
                      <button
                        key={c}
                        type="button"
                        onClick={() => setHumanCaptions(c)}
                        className={`p-3 rounded-xl text-xs font-bold border transition-all text-center ${
                          humanCaptions === c
                            ? "bg-purple-500/20 text-white border-purple-400 shadow-sm shadow-purple-500/20"
                            : "border-white/[0.08] bg-white/[0.02] text-zinc-400 hover:text-white hover:bg-white/[0.05]"
                        }`}
                      >
                        {c}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Music Concept */}
                <div>
                  <label className="block text-xs font-semibold text-zinc-300 mb-2">
                    Background Music Track
                  </label>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {(["Ambient", "Upbeat", "Lo-Fi", "None"] as const).map((track) => (
                      <button
                        key={track}
                        type="button"
                        onClick={() => setHumanMusic(track)}
                        className={`p-3 rounded-xl text-xs font-bold border transition-all text-center ${
                          humanMusic === track
                            ? "bg-pink-500/20 text-white border-pink-400 shadow-sm shadow-pink-500/20"
                            : "border-white/[0.08] bg-white/[0.02] text-zinc-400 hover:text-white hover:bg-white/[0.05]"
                        }`}
                      >
                        {track}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Voice Selection */}
                <div>
                  <label className="block text-xs font-semibold text-zinc-300 mb-2">
                    Narration Voice
                  </label>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {[
                      { id: "adam", name: "Adam", desc: "Narrative & Deep" },
                      { id: "rachel", name: "Rachel", desc: "Warm & Clear" },
                      { id: "josh", name: "Josh", desc: "Young & Punchy" },
                      { id: "antoni", name: "Antoni", desc: "Crisp & Thoughtful" },
                    ].map((v) => (
                      <button
                        key={v.id}
                        type="button"
                        onClick={() => setAiVoice(v.id)}
                        className={`p-3 rounded-xl text-left border transition-all ${
                          aiVoice === v.id
                            ? "bg-cyan-500/20 border-cyan-400 text-white shadow-sm"
                            : "border-white/[0.08] bg-white/[0.02] text-zinc-400 hover:text-white"
                        }`}
                      >
                        <span className="block text-xs font-bold text-white mb-0.5">{v.name}</span>
                        <span className="block text-[10px] text-zinc-500">{v.desc}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Navigation */}
              <div className="flex items-center justify-between pt-2">
                <button
                  type="button"
                  onClick={() => setCurrentStep(2)}
                  className="px-4 py-2.5 rounded-xl text-xs font-semibold text-zinc-400 hover:text-white bg-white/[0.04] border border-white/[0.08] hover:bg-white/[0.08] transition-all"
                >
                  ← Back to Storyboard
                </button>

                <button
                  type="button"
                  onClick={() => setCurrentStep(4)}
                  className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-xs font-bold text-white shadow-lg shadow-cyan-500/20 transition-all active:scale-98"
                >
                  <span>Continue to Generate</span>
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}

          {/* STEP 4: APPROVAL CHECKPOINT & LAUNCH GENERATE */}
          {currentStep === 4 && plannedStory && (
            <div className="max-w-3xl mx-auto glass-card rounded-3xl p-6 sm:p-10 border-white/[0.1] shadow-2xl animate-fadeIn">
              <div className="flex items-center gap-3.5 mb-6">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-500/20 via-cyan-500/20 to-indigo-500/20 text-emerald-300 border border-emerald-500/30">
                  <CheckCircle2 className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white tracking-tight">Step 4 — Final Approval Checkpoint</h2>
                  <p className="text-xs text-zinc-400">
                    Never silently render an unreviewed story. Verify your Reel summary before initiating 1080×1920 video compilation.
                  </p>
                </div>
              </div>

              {/* Review Summary Card */}
              <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/[0.08] space-y-4 mb-8">
                <div>
                  <span className="text-[11px] font-semibold text-zinc-500 uppercase tracking-wider block mb-1">
                    Reel Title & Hook
                  </span>
                  <h3 className="text-base font-bold text-white mb-1">{plannedStory.title}</h3>
                  <p className="text-xs text-purple-300 bg-purple-500/10 p-2.5 rounded-xl border border-purple-500/20">
                    “{plannedStory.hook}”
                  </p>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
                  <div className="p-3 rounded-xl bg-zinc-900/80 border border-white/[0.05]">
                    <span className="text-[10px] text-zinc-500 uppercase block mb-0.5">Duration</span>
                    <span className="text-xs font-bold text-white">~{plannedStory.estimated_duration}s</span>
                  </div>
                  <div className="p-3 rounded-xl bg-zinc-900/80 border border-white/[0.05]">
                    <span className="text-[10px] text-zinc-500 uppercase block mb-0.5">Scene Count</span>
                    <span className="text-xs font-bold text-white">{plannedStory.scenes.length} Scenes</span>
                  </div>
                  <div className="p-3 rounded-xl bg-zinc-900/80 border border-white/[0.05]">
                    <span className="text-[10px] text-zinc-500 uppercase block mb-0.5">Style & Motion</span>
                    <span className="text-xs font-bold text-white">{humanVisualStyle} • {humanMotion}</span>
                  </div>
                  <div className="p-3 rounded-xl bg-zinc-900/80 border border-white/[0.05]">
                    <span className="text-[10px] text-zinc-500 uppercase block mb-0.5">Voice & Music</span>
                    <span className="text-xs font-bold text-white capitalize">{aiVoice} • {humanMusic}</span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setCurrentStep(2)}
                  className="px-4 py-3 rounded-xl text-xs font-semibold text-zinc-400 hover:text-white bg-white/[0.04] border border-white/[0.08] hover:bg-white/[0.08] transition-all"
                >
                  ← Edit Story Scenes
                </button>

                <button
                  type="button"
                  onClick={handleApproveAndRender}
                  className="flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-cyan-500 via-indigo-600 to-purple-600 px-8 py-3.5 text-sm font-bold text-white shadow-xl shadow-cyan-500/25 hover:from-cyan-400 hover:to-indigo-500 transition-all active:scale-98"
                >
                  <Sparkles className="h-4 w-4" />
                  <span>Generate Reel (1080×1920) →</span>
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
        <div className="h-8 w-8 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin mx-auto mb-4" />
        <p className="text-sm text-zinc-400">Loading VidSnap Studio...</p>
      </div>
    }>
      <CreatePageContent />
    </Suspense>
  );
}
