"use client";

import { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Sparkles,
  Play,
  Download,
  CheckCircle2,
  Clock,
  Layers,
  Bot,
  Send,
  Wand2,
  Mic,
  Music,
  Save,
  Trash2,
  Sliders,
  AlertCircle,
  RefreshCw,
  ArrowUp,
  ArrowDown,
  RotateCcw,
  Eye,
  Flame,
  Film,
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

interface SceneItem {
  id: string;
  order: number;
  visual_filename: string;
  visual_url: string;
  visual_direction?: string;
  narration: string;
  caption: string;
  duration_seconds: number;
  scene_role?: string;
  match_quality?: string;
  visual_plan?: VisualPlanData;
  motion?: string;
  transition?: string;
  visual_source?: string;
  alignment_source?: string;
  caption_segments?: any[];
}

interface ProjectDetail {
  id: string;
  title: string;
  created_at: string;
  status: string;
  duration_seconds: number;
  video_url?: string;
  thumbnail_url?: string;
  voice: string;
  music?: string;
  style: string;
  script: string;
  mode: string;
  source_type?: string;
  original_prompt?: string;
  audience?: string;
  tone?: string;
  target_length?: string;
  scenes: SceneItem[];
}

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params?.id as string;

  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isRendering, setIsRendering] = useState(false);
  const [renderStep, setRenderStep] = useState("");
  
  // Selected scene for storyboard <-> video synchronization
  const [selectedSceneIndex, setSelectedSceneIndex] = useState<number>(0);

  // Mobile tab switcher: "storyboard" vs "preview"
  const [mobileTab, setMobileTab] = useState<"storyboard" | "preview">("storyboard");

  // Ask VidSnap compact command bar
  const [assistantPrompt, setAssistantPrompt] = useState("");
  const [assistantFeedback, setAssistantFeedback] = useState<string | null>(null);
  const [isAssistantWorking, setIsAssistantWorking] = useState(false);

  // Scene regeneration flags
  const [regeneratingSceneId, setRegeneratingSceneId] = useState<string | null>(null);
  const [regeneratingVisualSceneId, setRegeneratingVisualSceneId] = useState<string | null>(null);
  const [isRegeneratingStory, setIsRegeneratingStory] = useState(false);

  // HTML5 Video ref to seek when selecting scenes in completed reels
  const videoPlayerRef = useRef<HTMLVideoElement | null>(null);

  useEffect(() => {
    if (!projectId) return;

    const loadProject = async () => {
      try {
        const res = await fetch(`/api/projects/${projectId}`);
        if (res.ok) {
          const data = await res.json();
          setProject(data);
        } else {
          setNotFound(true);
        }
      } catch (err) {
        console.error("Failed to load project", err);
        setNotFound(true);
      } finally {
        setIsLoading(false);
      }
    };

    loadProject();
  }, [projectId]);

  // Sync selected scene with video playback time if video is present
  const handleSelectScene = (index: number) => {
    setSelectedSceneIndex(index);
    if (project?.video_url && videoPlayerRef.current && project.scenes) {
      // Calculate scene start timestamp
      let startSecs = 0;
      for (let i = 0; i < index; i++) {
        startSecs += project.scenes[i]?.duration_seconds || 4;
      }
      try {
        videoPlayerRef.current.currentTime = startSecs;
        videoPlayerRef.current.play().catch(() => {});
      } catch (e) {
        console.error("Failed to seek video", e);
      }
    }
  };

  const handleSceneChange = (
    sceneId: string,
    field: "narration" | "caption" | "visual_direction",
    value: string
  ) => {
    if (!project) return;
    setProject({
      ...project,
      scenes: project.scenes.map((s) => (s.id === sceneId ? { ...s, [field]: value } : s)),
    });
  };

  const handleRegenerateScene = async (sceneOrder: number, sceneId: string) => {
    if (!project) return;
    setRegeneratingSceneId(sceneId);
    try {
      const res = await fetch(`/api/projects/${project.id}/scenes/${sceneOrder}/regenerate`, {
        method: "POST",
      });
      if (res.ok) {
        const data = await res.json();
        setProject((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            scenes: prev.scenes.map((s) => (s.order === sceneOrder ? { ...s, ...data.scene } : s)),
          };
        });
        setAssistantFeedback(`✨ Scene #${sceneOrder} regenerated!`);
        setTimeout(() => setAssistantFeedback(null), 3000);
      }
    } catch (e) {
      console.error("Regenerate scene failed", e);
    } finally {
      setRegeneratingSceneId(null);
    }
  };

  const handleRegenerateVisual = async (sceneOrder: number, sceneId: string) => {
    if (!project) return;
    setRegeneratingVisualSceneId(sceneId);
    try {
      const res = await fetch(`/api/projects/${project.id}/scenes/${sceneOrder}/regenerate-visual`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to regenerate visual.");
      }
      const data = await res.json();
      setProject(data.project);
      setAssistantFeedback(`✨ Visual for Scene #${sceneOrder} regenerated!`);
      setTimeout(() => setAssistantFeedback(null), 3000);
    } catch (e: any) {
      alert("Could not regenerate visual: " + e.message);
    } finally {
      setRegeneratingVisualSceneId(null);
    }
  };

  const handleDeleteScene = async (sceneOrder: number) => {
    if (!project) return;
    if (project.scenes.length <= 1) {
      alert("A Reel must have at least one scene.");
      return;
    }
    if (!confirm(`Delete Scene #${sceneOrder}?`)) return;
    try {
      const res = await fetch(`/api/projects/${project.id}/scenes/${sceneOrder}`, {
        method: "DELETE",
      });
      if (res.ok) {
        const data = await res.json();
        setProject(data.project);
        setSelectedSceneIndex(0);
        setAssistantFeedback(`Deleted Scene #${sceneOrder}.`);
        setTimeout(() => setAssistantFeedback(null), 3000);
      }
    } catch (e) {
      console.error("Failed to delete scene", e);
    }
  };

  const moveScene = (index: number, direction: "up" | "down") => {
    if (!project) return;
    const newScenes = [...project.scenes];
    const targetIndex = direction === "up" ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= newScenes.length) return;

    const temp = newScenes[index];
    newScenes[index] = newScenes[targetIndex];
    newScenes[targetIndex] = temp;

    newScenes.forEach((s, idx) => {
      s.order = idx + 1;
    });

    setProject({ ...project, scenes: newScenes });
    setSelectedSceneIndex(targetIndex);
  };

  const handleRegenerateStory = async () => {
    if (!project) return;
    setIsRegeneratingStory(true);
    try {
      const res = await fetch(`/api/projects/${project.id}/regenerate-story`, {
        method: "POST",
      });
      if (res.ok) {
        const data = await res.json();
        setProject(data.project);
        setSelectedSceneIndex(0);
        setAssistantFeedback("✨ Story regenerated with a new hook & angle!");
        setTimeout(() => setAssistantFeedback(null), 4000);
      }
    } catch (e) {
      console.error("Regenerate story error", e);
    } finally {
      setIsRegeneratingStory(false);
    }
  };

  const saveScenes = async (): Promise<boolean> => {
    if (!project) return false;
    setIsSaving(true);
    try {
      const res = await fetch(`/api/projects/${project.id}/scenes`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scenes: project.scenes.map((s) => ({
            id: s.id,
            narration: s.narration,
            caption: s.caption,
            visual_direction: s.visual_direction,
          })),
        }),
      });
      if (res.ok) {
        const updated = await res.json();
        setProject(updated);
        setAssistantFeedback("Story changes saved successfully!");
        setTimeout(() => setAssistantFeedback(null), 3000);
        return true;
      }
      return false;
    } catch (e) {
      console.error("Failed to save scenes", e);
      return false;
    } finally {
      setIsSaving(false);
    }
  };

  const handleReRender = async () => {
    if (!project) return;
    setIsRendering(true);
    setRenderStep("Saving story changes & enqueuing render...");
    try {
      await saveScenes();
      const res = await fetch(`/api/projects/${project.id}/render`, {
        method: "POST",
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to start render.");
      }
      const data = await res.json();
      const jobId = data.job_id;

      const interval = setInterval(async () => {
        try {
          const pollRes = await fetch(`/api/jobs/${jobId}`);
          if (pollRes.ok) {
            const jobData = await pollRes.json();
            setRenderStep(jobData.step);
            if (jobData.status === "completed") {
              clearInterval(interval);
              setIsRendering(false);
              const projRes = await fetch(`/api/projects/${project.id}`);
              if (projRes.ok) {
                setProject(await projRes.json());
              }
              setAssistantFeedback("Reel rendered successfully! 🎉");
              setTimeout(() => setAssistantFeedback(null), 4000);
            } else if (jobData.status === "failed") {
              clearInterval(interval);
              setIsRendering(false);
              setAssistantFeedback(`Render failed: ${jobData.error_message || "Unknown error"}`);
            }
          }
        } catch (e) {
          console.error("Poll error", e);
        }
      }, 1000);
    } catch (err: any) {
      setIsRendering(false);
      setAssistantFeedback(err.message || "Failed to trigger render.");
    }
  };

  const handleDeleteProject = async () => {
    if (!project) return;
    if (!confirm(`Are you sure you want to delete "${project.title}"?`)) return;
    try {
      const res = await fetch(`/api/projects/${project.id}`, { method: "DELETE" });
      if (res.ok) {
        router.push("/projects");
      }
    } catch (e) {
      console.error("Failed to delete project", e);
    }
  };

  const handleAskAssistant = async (commandOverride?: string) => {
    const cmd = commandOverride || assistantPrompt;
    if (!cmd.trim() || !project) return;

    setIsAssistantWorking(true);
    setAssistantFeedback(null);

    try {
      const res = await fetch(`/api/projects/${project.id}/assistant`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: cmd }),
      });

      if (res.ok) {
        const data = await res.json();
        setProject(data.project);
        setAssistantFeedback(data.action || "Story updated by Ask VidSnap.");
        setAssistantPrompt("");
      }
    } catch (err) {
      console.error("Ask VidSnap error", err);
    } finally {
      setIsAssistantWorking(false);
    }
  };

  if (notFound) {
    return (
      <div className="mx-auto max-w-lg px-4 py-24 text-center">
        <div className="glass-card rounded-3xl p-8 border-red-500/30 bg-zinc-900/60 shadow-2xl">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-red-500/10 text-red-400 mx-auto mb-4 border border-red-500/20">
            <AlertCircle className="h-6 w-6" />
          </div>
          <h2 className="text-xl font-bold text-white mb-2">Project Not Found</h2>
          <p className="text-sm text-zinc-400 mb-6 leading-relaxed">
            We couldn't locate a story project with ID: <br />
            <code className="text-zinc-300 bg-white/[0.05] px-2 py-0.5 rounded text-xs mt-1 inline-block font-mono">
              {projectId}
            </code>
          </p>
          <div className="flex items-center justify-center gap-3">
            <Link
              href="/projects"
              className="rounded-xl bg-white/[0.05] hover:bg-white/[0.1] px-5 py-2.5 text-xs font-semibold text-white transition-all"
            >
              ← Return to Projects
            </Link>
            <Link
              href="/create"
              className="rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 px-5 py-2.5 text-xs font-semibold text-white shadow-lg shadow-cyan-500/20"
            >
              Create New Reel
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (isLoading || !project) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-20 text-center">
        <div className="h-8 w-8 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin mx-auto mb-4" />
        <p className="text-sm text-zinc-400">Opening VidSnap Studio Editor...</p>
      </div>
    );
  }

  const currentScene: SceneItem | null =
    project.scenes && project.scenes.length > 0
      ? project.scenes[selectedSceneIndex] || project.scenes[0]
      : null;

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8 w-full">
      {/* Top Header & Breadcrumbs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 mb-6 border-b border-white/[0.08]">
        <div className="flex items-center gap-3.5">
          <Link
            href="/projects"
            aria-label="Back to Projects"
            className="p-2.5 rounded-xl border border-white/[0.08] bg-white/[0.02] text-zinc-400 hover:text-white hover:bg-white/[0.06] transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h1 className="text-lg sm:text-xl font-bold text-white truncate max-w-xs sm:max-w-md">
                {project.title}
              </h1>
              <span className="text-[10px] font-bold text-cyan-400 bg-cyan-500/10 border border-cyan-500/25 px-2 py-0.5 rounded-full uppercase">
                {project.mode} Reel
              </span>
            </div>
            <p className="text-xs text-zinc-400">
              Story Editor • Total duration: ~{Math.round(project.duration_seconds)}s • {project.scenes.length} Scenes
            </p>
          </div>
        </div>

        {/* Primary Action Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={saveScenes}
            disabled={isSaving || isRendering}
            className="flex items-center gap-1.5 rounded-xl border border-white/[0.1] bg-white/[0.03] hover:bg-white/[0.07] px-3.5 py-2 text-xs font-semibold text-white transition-all disabled:opacity-50"
          >
            <Save className="h-3.5 w-3.5 text-cyan-400" />
            <span>{isSaving ? "Saving..." : "Save Story"}</span>
          </button>

          <button
            onClick={handleReRender}
            disabled={isRendering || isSaving}
            className="flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-cyan-500 via-indigo-600 to-purple-600 hover:from-cyan-400 hover:to-indigo-500 px-4 py-2 text-xs font-bold text-white shadow-md shadow-cyan-500/20 transition-all disabled:opacity-50 active:scale-98"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isRendering ? "animate-spin" : ""}`} />
            <span>{isRendering ? "Rendering..." : project.video_url ? "Re-Render Reel" : "Render Reel"}</span>
          </button>

          {project.video_url && (
            <a
              href={project.video_url}
              download={`${project.title}.mp4`}
              className="flex items-center gap-1.5 rounded-xl border border-white/[0.1] bg-white/[0.03] hover:bg-white/[0.07] px-3 py-2 text-xs font-semibold text-zinc-200 transition-all"
            >
              <Download className="h-3.5 w-3.5" />
              <span>MP4</span>
            </a>
          )}

          <button
            onClick={handleDeleteProject}
            disabled={isRendering}
            className="p-2 rounded-xl border border-white/[0.1] bg-white/[0.02] text-zinc-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
            title="Delete Project"
            aria-label="Delete Project"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Rendering Banner */}
      {isRendering && (
        <div className="mb-6 flex items-center gap-3 rounded-2xl border border-cyan-500/30 bg-cyan-500/10 p-4 text-xs text-cyan-200 animate-pulse">
          <RefreshCw className="h-4 w-4 animate-spin text-cyan-400 flex-shrink-0" />
          <div>
            <span className="font-semibold block text-white mb-0.5">VidSnap is rendering your story into video</span>
            <span>{renderStep || "Processing speech synchronization and 1080×1920 video canvas..."}</span>
          </div>
        </div>
      )}

      {/* Mobile Tab Switcher */}
      <div className="lg:hidden flex items-center gap-1.5 p-1 mb-6 rounded-xl bg-white/[0.04] border border-white/[0.08]">
        <button
          type="button"
          onClick={() => setMobileTab("storyboard")}
          className={`flex-1 py-2 rounded-lg text-xs font-bold transition-all ${
            mobileTab === "storyboard"
              ? "bg-white/[0.1] text-white border border-white/[0.15]"
              : "text-zinc-400 hover:text-white"
          }`}
        >
          Storyboard ({project.scenes.length})
        </button>
        <button
          type="button"
          onClick={() => setMobileTab("preview")}
          className={`flex-1 py-2 rounded-lg text-xs font-bold transition-all ${
            mobileTab === "preview"
              ? "bg-white/[0.1] text-white border border-white/[0.15]"
              : "text-zinc-400 hover:text-white"
          }`}
        >
          Video Preview
        </button>
      </div>

      {/* Desktop 2-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Storyboard Scene Cards */}
        <div className={`lg:col-span-7 flex flex-col gap-6 ${mobileTab === "preview" ? "hidden lg:flex" : "flex"}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Layers className="h-4 w-4 text-cyan-400" />
              <h2 className="text-base font-bold text-white">Storyboard Scenes</h2>
            </div>
            <span className="text-xs text-zinc-500">
              Click any scene to focus companion preview
            </span>
          </div>

          {/* Scene Cards List */}
          <div className="space-y-4">
            {project.scenes.map((scene, idx) => {
              const isSelected = selectedSceneIndex === idx;
              return (
                <div
                  key={scene.id}
                  onClick={() => handleSelectScene(idx)}
                  className={`glass-card rounded-2xl p-5 transition-all cursor-pointer flex flex-col gap-4 ${
                    isSelected
                      ? "glass-card-active"
                      : "border-white/[0.08] hover:border-white/[0.15]"
                  }`}
                >
                  {/* Top Header of Scene Card */}
                  <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span
                        className={`px-2 py-0.5 rounded-md text-[11px] font-mono font-bold ${
                          isSelected
                            ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                            : "bg-zinc-800 text-zinc-300 border border-zinc-700"
                        }`}
                      >
                        Scene #{scene.order}
                      </span>
                      {scene.scene_role && (
                        <span className="px-2 py-0.5 rounded-md text-[10px] uppercase font-bold tracking-wider bg-purple-500/10 text-purple-300 border border-purple-500/20">
                          {scene.scene_role}
                        </span>
                      )}
                      {(scene.visual_plan?.motion || scene.motion) && (
                        <span className="px-2 py-0.5 rounded-md text-[10px] font-medium tracking-wide bg-blue-500/10 text-blue-300 border border-blue-500/20 capitalize">
                          {(scene.visual_plan?.motion || scene.motion || "").replace(/_/g, " ")}
                        </span>
                      )}
                      {scene.duration_seconds > 0 && (
                        <span className="text-[11px] text-zinc-400 font-mono">
                          ~{scene.duration_seconds.toFixed(1)}s
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                      {/* Move Up */}
                      <button
                        type="button"
                        disabled={idx === 0}
                        onClick={() => moveScene(idx, "up")}
                        className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.05] disabled:opacity-30 transition-all"
                        aria-label={`Move scene ${scene.order} up`}
                      >
                        <ArrowUp className="h-3.5 w-3.5" />
                      </button>

                      {/* Move Down */}
                      <button
                        type="button"
                        disabled={idx === project.scenes.length - 1}
                        onClick={() => moveScene(idx, "down")}
                        className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.05] disabled:opacity-30 transition-all"
                        aria-label={`Move scene ${scene.order} down`}
                      >
                        <ArrowDown className="h-3.5 w-3.5" />
                      </button>

                      {/* Regenerate Scene */}
                      <button
                        type="button"
                        disabled={regeneratingSceneId === scene.id}
                        onClick={() => handleRegenerateScene(scene.order, scene.id)}
                        className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-semibold text-purple-300 bg-purple-500/10 border border-purple-500/30 hover:bg-purple-500/20 transition-all disabled:opacity-40 ml-1"
                        title="Regenerate this scene narration & caption"
                      >
                        <RotateCcw className={`h-3 w-3 ${regeneratingSceneId === scene.id ? "animate-spin" : ""}`} />
                        <span>Regen</span>
                      </button>

                      {/* Delete Scene */}
                      {project.scenes.length > 1 && (
                        <button
                          type="button"
                          onClick={() => handleDeleteScene(scene.order)}
                          className="p-1.5 rounded-lg text-zinc-500 hover:text-red-400 hover:bg-red-500/10 transition-all ml-1"
                          title="Delete Scene"
                          aria-label={`Delete scene ${scene.order}`}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Scene Body: Thumbnail + Script Fields */}
                  <div className="flex flex-col sm:flex-row items-start gap-4">
                    {/* Visual Thumbnail */}
                    <div className="flex flex-col gap-2 w-full sm:w-32 flex-shrink-0" onClick={(e) => e.stopPropagation()}>
                      <div className="relative aspect-square w-full rounded-xl overflow-hidden bg-zinc-900 border border-white/[0.1]">
                        <img
                          src={scene.visual_url}
                          alt={`Scene ${scene.order}`}
                          className="w-full h-full object-cover"
                        />
                        {scene.visual_source === "ai" && (
                          <div className="absolute top-1.5 right-1.5 bg-purple-900/90 backdrop-blur-md px-1.5 py-0.5 rounded text-[9px] font-bold text-purple-200">
                            AI
                          </div>
                        )}
                      </div>

                      {/* Regenerate Visual Button */}
                      <button
                        type="button"
                        disabled={regeneratingVisualSceneId === scene.id}
                        onClick={() => handleRegenerateVisual(scene.order, scene.id)}
                        className="w-full flex items-center justify-center gap-1 py-1 px-2 rounded-lg text-[10px] font-semibold text-purple-300 bg-purple-500/10 border border-purple-500/20 hover:bg-purple-500/25 transition-all disabled:opacity-40"
                      >
                        <Sparkles className={`h-3 w-3 ${regeneratingVisualSceneId === scene.id ? "animate-spin" : ""}`} />
                        <span>{regeneratingVisualSceneId === scene.id ? "Generating..." : "Regen Visual"}</span>
                      </button>
                    </div>

                    {/* Script Fields */}
                    <div className="flex-1 w-full flex flex-col gap-3" onClick={(e) => e.stopPropagation()}>
                      <div>
                        <label className="block text-[11px] font-semibold text-zinc-400 mb-1">
                          Narration Script
                        </label>
                        <textarea
                          rows={2}
                          value={scene.narration || scene.caption}
                          onChange={(e) => handleSceneChange(scene.id, "narration", e.target.value)}
                          className="w-full rounded-xl border border-white/[0.1] bg-white/[0.02] p-2.5 text-xs text-white placeholder-zinc-500 focus:border-cyan-400 focus:outline-none resize-none leading-relaxed"
                        />
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <div>
                          <label className="block text-[11px] font-semibold text-zinc-400 mb-1">
                            Screen Caption
                          </label>
                          <input
                            type="text"
                            value={scene.caption}
                            onChange={(e) => handleSceneChange(scene.id, "caption", e.target.value)}
                            className="w-full rounded-xl border border-white/[0.1] bg-white/[0.02] px-3 py-1.5 text-xs font-semibold text-white focus:border-cyan-400 focus:outline-none"
                          />
                        </div>

                        <div>
                          <label className="block text-[11px] font-semibold text-zinc-400 mb-1">
                            Visual Direction
                          </label>
                          <input
                            type="text"
                            value={scene.visual_direction || ""}
                            onChange={(e) => handleSceneChange(scene.id, "visual_direction", e.target.value)}
                            className="w-full rounded-xl border border-white/[0.1] bg-white/[0.02] px-3 py-1.5 text-xs text-zinc-300 focus:border-cyan-400 focus:outline-none"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Ask VidSnap: Compact AI Command Interface */}
          <div className="glass-card rounded-2xl p-5 border-cyan-500/20 bg-[#0c0e17]">
            <div className="flex items-center gap-2 mb-2">
              <Bot className="h-4 w-4 text-cyan-400" />
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">Ask VidSnap (AI Director)</h3>
            </div>
            <p className="text-xs text-zinc-400 mb-3">
              Direct and reshape the story with natural language commands:
            </p>

            {/* Quick Action Chips */}
            <div className="flex flex-wrap gap-1.5 mb-3">
              {[
                "Make the hook stronger",
                "Make this shorter",
                "Make this more technical",
                "Change the voice to Rachel",
                "Make the tone punchy",
                "Regenerate full story",
              ].map((chip) => (
                <button
                  key={chip}
                  type="button"
                  onClick={() => handleAskAssistant(chip)}
                  className="rounded-lg border border-white/[0.08] bg-white/[0.03] px-2.5 py-1 text-[11px] text-zinc-300 hover:text-white hover:border-cyan-500/40 transition-all"
                >
                  {chip}
                </button>
              ))}
            </div>

            {/* Input Bar */}
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={assistantPrompt}
                onChange={(e) => setAssistantPrompt(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAskAssistant()}
                placeholder="Ask VidSnap to adjust tone, pacing, or scene details..."
                aria-label="Ask VidSnap command input"
                className="flex-1 rounded-xl border border-white/[0.1] bg-white/[0.02] px-3 py-2 text-xs text-white placeholder-zinc-500 focus:border-cyan-400 focus:outline-none"
              />
              <button
                type="button"
                onClick={() => handleAskAssistant()}
                disabled={isAssistantWorking || !assistantPrompt.trim()}
                className="rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black px-3.5 py-2 text-xs font-bold disabled:opacity-40 transition-all flex items-center gap-1.5"
              >
                {isAssistantWorking ? (
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Send className="h-3.5 w-3.5" />
                )}
                <span>Run</span>
              </button>
            </div>

            {assistantFeedback && (
              <div className="mt-3 flex items-center gap-2 text-xs text-emerald-400 animate-fadeIn">
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>{assistantFeedback}</span>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Sticky Video Preview (STORY ↔ VIDEO) */}
        <div className={`lg:col-span-5 flex flex-col items-center sticky top-24 ${mobileTab === "storyboard" ? "hidden lg:flex" : "flex"}`}>
          <div className="phone-mockup relative">
            <div className="phone-notch" />

            {/* Case 1: Video is Rendered -> HTML5 Player synced to scenes */}
            {project.video_url ? (
              <div className="relative w-full h-full bg-zinc-950 flex flex-col justify-between">
                <video
                  ref={videoPlayerRef}
                  src={project.video_url}
                  controls
                  playsInline
                  className="w-full h-full object-cover"
                />
                <div className="absolute top-12 left-4 right-4 flex items-center justify-between z-30 pointer-events-none">
                  <span className="bg-black/75 backdrop-blur-md px-2 py-0.5 rounded text-[11px] font-mono font-bold text-white border border-white/10">
                    Scene #{selectedSceneIndex + 1}
                  </span>
                  <span className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 backdrop-blur-md px-2 py-0.5 rounded text-[10px] font-bold">
                    RENDERED MP4
                  </span>
                </div>
              </div>
            ) : currentScene ? (
              /* Case 2: Storyboard Preview (Unrendered Project) */
              <div className="relative w-full h-full bg-zinc-950 flex flex-col justify-between overflow-hidden">
                <img
                  src={currentScene.visual_url}
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
                    <span>STORYBOARD PREVIEW</span>
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
                    Screen Caption
                  </span>
                  <p className="text-xs font-bold text-white leading-snug drop-shadow-md">
                    {currentScene.caption}
                  </p>
                </div>
              </div>
            ) : (
              <div className="w-full h-full flex flex-col items-center justify-center p-6 text-center text-zinc-500 bg-zinc-950">
                <Film className="h-10 w-10 text-zinc-600 mb-3" />
                <span className="text-xs font-semibold text-zinc-300 mb-1">
                  Storyboard Preview
                </span>
              </div>
            )}
          </div>

          {/* Quick Details Below Mockup */}
          <div className="mt-4 w-full max-w-[320px] glass-card rounded-xl p-3.5 text-xs text-zinc-400 flex flex-col gap-1.5 border-white/[0.08]">
            <div className="flex justify-between">
              <span>Voice:</span>
              <span className="text-zinc-200 font-semibold capitalize">{project.voice}</span>
            </div>
            <div className="flex justify-between">
              <span>Music:</span>
              <span className="text-zinc-200 font-semibold capitalize">
                {project.music?.replace("_", " ") || "None"}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Canvas:</span>
              <span className="text-zinc-200 font-semibold">1080×1920 (9:16)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
