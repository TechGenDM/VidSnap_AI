"use client";

import { useState, useEffect } from "react";
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
} from "lucide-react";

interface SceneItem {
  id: string;
  order: number;
  visual_filename: string;
  visual_url: string;
  narration: string;
  caption: string;
  duration_seconds: number;
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
  const [assistantPrompt, setAssistantPrompt] = useState("");
  const [assistantFeedback, setAssistantFeedback] = useState<string | null>(null);
  const [isAssistantWorking, setIsAssistantWorking] = useState(false);

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

  const handleSceneChange = (
    sceneId: string,
    field: "narration" | "caption",
    value: string
  ) => {
    if (!project) return;
    setProject({
      ...project,
      scenes: project.scenes.map((s) => (s.id === sceneId ? { ...s, [field]: value } : s)),
    });
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
              setAssistantFeedback("Reel re-rendered successfully! 🎉");
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
      setAssistantFeedback(err.message || "Failed to trigger re-render.");
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
        <div className="glass-card rounded-2xl p-8 border-red-500/30 bg-zinc-900/60 shadow-xl">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-red-500/10 text-red-400 mx-auto mb-4 border border-red-500/20">
            <AlertCircle className="h-6 w-6" />
          </div>
          <h2 className="text-xl font-bold text-white mb-2">Project Not Found</h2>
          <p className="text-sm text-zinc-400 mb-6 leading-relaxed">
            We couldn't locate a story project with ID: <br />
            <code className="text-zinc-300 bg-zinc-800/80 px-2 py-0.5 rounded text-xs mt-1 inline-block font-mono">
              {projectId}
            </code>
            <br />
            The project may have been deleted or the link is incorrect.
          </p>
          <div className="flex items-center justify-center gap-3">
            <Link
              href="/projects"
              className="rounded-xl bg-zinc-800 hover:bg-zinc-700 px-5 py-2.5 text-xs font-semibold text-white transition-all"
            >
              ← Return to Projects
            </Link>
            <Link
              href="/create"
              className="rounded-xl bg-indigo-600 hover:bg-indigo-500 px-5 py-2.5 text-xs font-semibold text-white transition-all shadow-lg shadow-indigo-500/20"
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
        <div className="h-8 w-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin mx-auto mb-4" />
        <p className="text-sm text-zinc-400">Loading your story...</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8 w-full">
      {/* Top Header & Breadcrumbs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 mb-8 border-b border-zinc-800/80">
        <div className="flex items-center gap-4">
          <Link
            href="/projects"
            className="p-2 rounded-xl border border-zinc-800 bg-zinc-900 text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h1 className="text-xl font-bold text-white truncate max-w-sm sm:max-w-md">
                {project.title}
              </h1>
              <span className="text-[10px] font-bold text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-2 py-0.5 rounded-full uppercase">
                {project.mode} Reel
              </span>
            </div>
            <p className="text-xs text-zinc-400">
              Story-driven scene editor • Total duration: ~{project.duration_seconds}s
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={saveScenes}
            disabled={isSaving || isRendering}
            className="flex items-center gap-1.5 rounded-xl border border-zinc-750 bg-zinc-850 hover:bg-zinc-800 px-3.5 py-2 text-xs font-semibold text-white transition-all disabled:opacity-50"
          >
            <Save className="h-3.5 w-3.5" />
            <span>{isSaving ? "Saving..." : "Save Story"}</span>
          </button>

          <button
            onClick={handleReRender}
            disabled={isRendering || isSaving}
            className="flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 px-4 py-2 text-xs font-semibold text-white shadow-md shadow-indigo-500/20 transition-all disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isRendering ? "animate-spin" : ""}`} />
            <span>{isRendering ? "Rendering..." : "Render Reel"}</span>
          </button>

          {project.video_url && (
            <a
              href={project.video_url}
              download={`${project.title}.mp4`}
              className="flex items-center gap-1.5 rounded-xl border border-zinc-800 bg-zinc-900 hover:bg-zinc-800 px-3.5 py-2 text-xs font-semibold text-zinc-200 transition-all"
            >
              <Download className="h-3.5 w-3.5" />
              <span>MP4</span>
            </a>
          )}

          <button
            onClick={handleDeleteProject}
            disabled={isRendering}
            className="p-2 rounded-xl border border-zinc-800 bg-zinc-900 text-zinc-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
            title="Delete Project"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Re-rendering banner */}
      {isRendering && (
        <div className="mb-8 flex items-center gap-3 rounded-xl border border-indigo-500/30 bg-indigo-500/10 p-4 text-xs text-indigo-200 animate-pulse">
          <RefreshCw className="h-4 w-4 animate-spin text-indigo-400 flex-shrink-0" />
          <div>
            <span className="font-semibold block text-white mb-0.5">VidSnap is re-rendering your story</span>
            <span>{renderStep || "Processing speech synchronization and 1080x1920 video canvas..."}</span>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Scene/Story Cards ("VidSnap edits the story, not the timeline") */}
        <div className="lg:col-span-7 flex flex-col gap-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Layers className="h-4 w-4 text-indigo-400" />
              <h2 className="text-base font-bold text-white">Story Scenes</h2>
            </div>
            <span className="text-xs text-zinc-500">
              Edit text or captions directly. Durations re-sync automatically.
            </span>
          </div>

          {/* Scene Cards */}
          <div className="space-y-4">
            {project.scenes.map((scene, idx) => (
              <div
                key={scene.id}
                className="glass-card rounded-2xl p-5 border-zinc-800 hover:border-zinc-700 transition-all flex flex-col sm:flex-row items-start gap-4"
              >
                {/* Visual Thumbnail */}
                <div className="relative w-full sm:w-28 aspect-[9/16] sm:aspect-square flex-shrink-0 rounded-xl overflow-hidden bg-zinc-900 border border-zinc-800">
                  <img
                    src={scene.visual_url}
                    alt={`Scene ${scene.order}`}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute top-1.5 left-1.5 bg-black/70 backdrop-blur-md px-1.5 py-0.5 rounded text-[10px] font-mono font-bold text-white">
                    #{scene.order}
                  </div>
                  {scene.duration_seconds > 0 && (
                    <div className="absolute bottom-1.5 right-1.5 bg-black/70 backdrop-blur-md px-1.5 py-0.5 rounded text-[10px] font-mono text-zinc-300">
                      {scene.duration_seconds}s
                    </div>
                  )}
                </div>

                {/* Text Fields */}
                <div className="flex-1 w-full flex flex-col gap-3">
                  <div>
                    <label className="block text-[11px] font-semibold text-zinc-400 mb-1">
                      Narration
                    </label>
                    <textarea
                      rows={2}
                      value={scene.narration || scene.caption}
                      onChange={(e) =>
                        handleSceneChange(scene.id, "narration", e.target.value)
                      }
                      placeholder="Scene narration text..."
                      className="w-full rounded-lg border border-zinc-800 bg-zinc-900/60 p-2.5 text-xs text-white placeholder-zinc-500 focus:border-indigo-500 focus:outline-none resize-none"
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] font-semibold text-zinc-400 mb-1">
                      Screen Caption Overlay
                    </label>
                    <input
                      type="text"
                      value={scene.caption}
                      onChange={(e) =>
                        handleSceneChange(scene.id, "caption", e.target.value)
                      }
                      placeholder="Caption text displayed in video..."
                      className="w-full rounded-lg border border-zinc-800 bg-zinc-900/60 px-2.5 py-1.5 text-xs text-white placeholder-zinc-500 focus:border-indigo-500 focus:outline-none"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Ask VidSnap AI Assistant Box */}
          <div className="glass-card rounded-2xl p-6 border-indigo-500/30 bg-zinc-950/60">
            <div className="flex items-center gap-2 mb-3">
              <Bot className="h-4 w-4 text-purple-400" />
              <h3 className="text-sm font-bold text-white">Ask VidSnap (AI Assistant)</h3>
            </div>
            <p className="text-xs text-zinc-400 mb-4">
              Give instructions in natural language to refine your story, tone, or hook.
            </p>

            {/* Quick Prompt Chips */}
            <div className="flex flex-wrap gap-2 mb-4">
              {[
                "Make the intro more attention-grabbing",
                "Make the tone more energetic",
                "Change the voice to Rachel",
              ].map((chip) => (
                <button
                  key={chip}
                  type="button"
                  onClick={() => handleAskAssistant(chip)}
                  className="rounded-lg border border-zinc-800 bg-zinc-900 px-2.5 py-1 text-[11px] text-zinc-300 hover:text-white hover:border-purple-500/50 transition-all"
                >
                  {chip}
                </button>
              ))}
            </div>

            {/* Assistant Input Bar */}
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={assistantPrompt}
                onChange={(e) => setAssistantPrompt(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAskAssistant()}
                placeholder="e.g. “Make the second scene shorter and more emotional”"
                className="flex-1 rounded-xl border border-zinc-800 bg-zinc-900 px-3.5 py-2 text-xs text-white placeholder-zinc-500 focus:border-purple-500 focus:outline-none"
              />
              <button
                type="button"
                onClick={() => handleAskAssistant()}
                disabled={isAssistantWorking || !assistantPrompt.trim()}
                className="p-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white disabled:opacity-40 transition-colors"
              >
                <Send className="h-3.5 w-3.5" />
              </button>
            </div>

            {assistantFeedback && (
              <div className="mt-3 flex items-center gap-2 text-xs text-emerald-400">
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>{assistantFeedback}</span>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Phone Preview Simulator */}
        <div className="lg:col-span-5 flex flex-col items-center sticky top-24">
          <div className="phone-mockup relative">
            <div className="phone-notch" />
            {project.video_url ? (
              <video
                src={project.video_url}
                controls
                playsInline
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex flex-col items-center justify-center p-6 text-center text-zinc-500 bg-zinc-900">
                <Wand2 className="h-10 w-10 text-indigo-400 mb-3 animate-pulse" />
                <span className="text-xs font-semibold text-zinc-300 mb-1">
                  Video Not Yet Rendered
                </span>
                <span className="text-[11px] text-zinc-500">
                  Save story changes to trigger high-resolution 1080×1920 compilation.
                </span>
              </div>
            )}
          </div>

          {/* Quick Settings Info */}
          <div className="mt-6 w-[310px] glass-card rounded-xl p-4 text-xs text-zinc-400 flex flex-col gap-2">
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
              <span>Format:</span>
              <span className="text-zinc-200 font-semibold">1080×1920 (9:16)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
