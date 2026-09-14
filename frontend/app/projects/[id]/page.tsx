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
  History,
  Copy,
  Loader2,
  Check,
  X,
  ChevronRight,
  Info,
  Upload,
  Image as ImageIcon,
  ShieldCheck,
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

interface ProjectVersionItem {
  version_number: number;
  created_at: string;
  label: string;
  title: string;
  hook: string;
  duration_seconds: number;
  voice: string;
  music?: string;
  style: string;
  scenes_count?: number;
  scenes?: any[];
}

interface HookAlternative {
  id: string;
  strategy: string;
  label: string;
  hook: string;
  caption: string;
}

interface VisualAlternativeItem {
  filename: string;
  url: string;
  label: string;
  type: string;
  domain?: string;
}

interface ProjectDetail {
  id: string;
  title: string;
  created_at: string;
  status: string;
  lifecycle_state?: string;
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
  qualitative_feedback?: string[];
  quality_gate?: any;
  quality_warnings?: string[];
  versions?: ProjectVersionItem[];
  metrics?: any;
}

const CREATOR_COMMAND_CHIPS = [
  { label: "🪝 Stronger Hook", cmd: "Make the hook stronger" },
  { label: "🔥 Provocative", cmd: "Make this more provocative" },
  { label: "⏱️ 20s Reel", cmd: "Make this 20 seconds" },
  { label: "✂️ Shorter", cmd: "Make this shorter" },
  { label: "💻 Technical", cmd: "Make this more technical" },
  { label: "💬 Conversational", cmd: "Make it sound more conversational" },
  { label: "🔤 Simpler Language", cmd: "Use simpler language" },
  { label: "🎯 Stronger Ending", cmd: "Give me a stronger ending" },
  { label: "🧹 Deduplicate", cmd: "Remove unnecessary repetition" },
];

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

  // Version History Modal state
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [versions, setVersions] = useState<ProjectVersionItem[]>([]);
  const [isLoadingVersions, setIsLoadingVersions] = useState(false);
  const [isRestoringVersion, setIsRestoringVersion] = useState<number | null>(null);

  // Hook Alternatives Modal state
  const [showHookModal, setShowHookModal] = useState(false);
  const [hookAlternatives, setHookAlternatives] = useState<HookAlternative[]>([]);
  const [isLoadingHooks, setIsLoadingHooks] = useState(false);
  const [isApplyingHook, setIsApplyingHook] = useState(false);

  // Duplication state
  const [isDuplicating, setIsDuplicating] = useState(false);

  // Visual Alternatives & Custom B-Roll state (Phase 7)
  const [showVisualAlternativesModal, setShowVisualAlternativesModal] = useState(false);
  const [visualAlternativesSceneOrder, setVisualAlternativesSceneOrder] = useState<number | null>(null);
  const [visualAlternatives, setVisualAlternatives] = useState<VisualAlternativeItem[]>([]);
  const [isLoadingAlternatives, setIsLoadingAlternatives] = useState(false);
  const [isUploadingBroll, setIsUploadingBroll] = useState<number | null>(null);
  const fileInputRefs = useRef<{ [order: number]: HTMLInputElement | null }>({});

  // HTML5 Video ref to seek when selecting scenes in completed reels
  const videoPlayerRef = useRef<HTMLVideoElement | null>(null);

  const handleUploadBrollClick = (sceneOrder: number) => {
    fileInputRefs.current[sceneOrder]?.click();
  };

  const handleBrollFileChange = async (sceneOrder: number, e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !project) return;

    setIsUploadingBroll(sceneOrder);
    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`/api/projects/${project.id}/scenes/${sceneOrder}/upload-asset`, {
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        setProject(data.project);
        setAssistantFeedback(`✨ Custom B-Roll uploaded for Scene #${sceneOrder}!`);
        setTimeout(() => setAssistantFeedback(null), 3500);
      } else {
        const err = await res.json();
        alert(err.detail || "Failed to upload asset.");
      }
    } catch (err) {
      console.error("Upload error", err);
    } finally {
      setIsUploadingBroll(null);
      if (e.target) e.target.value = "";
    }
  };

  const handleOpenVisualAlternatives = async (sceneOrder: number) => {
    if (!project) return;
    setVisualAlternativesSceneOrder(sceneOrder);
    setShowVisualAlternativesModal(true);
    setIsLoadingAlternatives(true);
    try {
      const res = await fetch(`/api/projects/${project.id}/scenes/${sceneOrder}/visual-alternatives`);
      if (res.ok) {
        const data = await res.json();
        setVisualAlternatives(data.alternatives || []);
      }
    } catch (e) {
      console.error("Failed loading visual alternatives", e);
    } finally {
      setIsLoadingAlternatives(false);
    }
  };

  const handleSelectVisualAlternative = async (alt: VisualAlternativeItem) => {
    if (!project || visualAlternativesSceneOrder === null) return;
    try {
      const res = await fetch(`/api/projects/${project.id}/scenes/${visualAlternativesSceneOrder}/select-visual`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          visual_filename: alt.filename,
          visual_url: alt.url,
          visual_type: alt.type,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setProject(data.project);
        setShowVisualAlternativesModal(false);
        setAssistantFeedback(`Visual for Scene #${visualAlternativesSceneOrder} set to '${alt.label}'.`);
        setTimeout(() => setAssistantFeedback(null), 3000);
      }
    } catch (e) {
      console.error("Failed selecting visual alternative", e);
    }
  };

  const handleRemoveCustomVisual = async (sceneOrder: number) => {
    if (!project) return;
    try {
      const res = await fetch(`/api/projects/${project.id}/scenes/${sceneOrder}/visual`, {
        method: "DELETE",
      });
      if (res.ok) {
        const data = await res.json();
        setProject(data.project);
        setAssistantFeedback(`Reverted Scene #${sceneOrder} to stock fallback visual.`);
        setTimeout(() => setAssistantFeedback(null), 3000);
      }
    } catch (e) {
      console.error("Failed removing visual", e);
    }
  };

  const loadProject = async () => {
    if (!projectId) return;
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

  useEffect(() => {
    loadProject();
  }, [projectId]);

  // Sync selected scene with video playback time if video is present
  const handleSelectScene = (index: number) => {
    setSelectedSceneIndex(index);
    if (project?.video_url && videoPlayerRef.current && project.scenes) {
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
    field: "narration" | "caption" | "visual_direction" | "motion" | "transition" | "visual_prompt",
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
        setAssistantFeedback(`Scene #${sceneOrder} regenerated.`);
        setTimeout(() => setAssistantFeedback(null), 3000);
      }
    } catch (e) {
      console.error("Regenerate scene error", e);
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
        setAssistantFeedback(`Visual for Scene #${sceneOrder} regenerated.`);
        setTimeout(() => setAssistantFeedback(null), 3000);
      }
    } catch (e) {
      console.error("Regenerate visual error", e);
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
            motion: s.motion,
            transition: s.transition,
            duration_seconds: s.duration_seconds,
            visual_source: s.visual_source,
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

  // Ask VidSnap Handler
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
        if (data.success) {
          setAssistantFeedback(`✨ ${data.action} (Snapshot saved to history)`);
        } else {
          setAssistantFeedback(`ℹ️ ${data.action}`);
        }
        setAssistantPrompt("");
      }
    } catch (err) {
      console.error("Ask VidSnap error", err);
    } finally {
      setIsAssistantWorking(false);
    }
  };

  // Phase 6: Version History Handlers
  const fetchVersions = async () => {
    if (!projectId) return;
    setIsLoadingVersions(true);
    try {
      const res = await fetch(`/api/projects/${projectId}/versions`);
      if (res.ok) {
        const data = await res.json();
        setVersions(data);
      }
    } catch (e) {
      console.error("Failed to load versions", e);
    } finally {
      setIsLoadingVersions(false);
    }
  };

  const handleOpenHistory = () => {
    setShowHistoryModal(true);
    fetchVersions();
  };

  const handleRestoreVersion = async (versionNum: number) => {
    if (!project) return;
    setIsRestoringVersion(versionNum);
    try {
      const res = await fetch(`/api/projects/${project.id}/versions/${versionNum}/restore`, {
        method: "POST",
      });
      if (res.ok) {
        const data = await res.json();
        setProject(data.project);
        setShowHistoryModal(false);
        setAssistantFeedback(`Restored project state from Version ${versionNum}!`);
        setTimeout(() => setAssistantFeedback(null), 4000);
      }
    } catch (e) {
      console.error("Failed to restore version", e);
    } finally {
      setIsRestoringVersion(null);
    }
  };

  // Phase 6: Project Duplication Handler
  const handleDuplicateProject = async () => {
    if (!project) return;
    setIsDuplicating(true);
    try {
      const res = await fetch(`/api/projects/${project.id}/duplicate`, {
        method: "POST",
      });
      if (res.ok) {
        const newProj = await res.json();
        router.push(`/projects/${newProj.id}`);
      }
    } catch (e) {
      console.error("Failed to duplicate project", e);
      setIsDuplicating(false);
    }
  };

  // Phase 6: Hook Alternatives Handlers
  const handleOpenHookModal = async () => {
    if (!project) return;
    setShowHookModal(true);
    setIsLoadingHooks(true);
    try {
      const res = await fetch(`/api/projects/${project.id}/alternatives/hook`);
      if (res.ok) {
        const data = await res.json();
        setHookAlternatives(data.alternatives || []);
      }
    } catch (e) {
      console.error("Failed to fetch hook alternatives", e);
    } finally {
      setIsLoadingHooks(false);
    }
  };

  const handleApplyHook = async (hookText: string, captionText?: string) => {
    if (!project) return;
    setIsApplyingHook(true);
    try {
      const res = await fetch(`/api/projects/${project.id}/apply-hook`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ hook: hookText, caption: captionText }),
      });
      if (res.ok) {
        const data = await res.json();
        setProject(data.project);
        setShowHookModal(false);
        setAssistantFeedback("Applied alternative hook and saved snapshot!");
        setTimeout(() => setAssistantFeedback(null), 4000);
      }
    } catch (e) {
      console.error("Failed to apply hook", e);
    } finally {
      setIsApplyingHook(false);
    }
  };

  const getLifecycleBadge = (lifecycle?: string, status?: string) => {
    const state = (lifecycle || status || "draft").toLowerCase();
    if (state === "ready" || state === "completed") {
      return { label: "Ready", color: "bg-emerald-950/80 text-emerald-400 border-emerald-500/30", icon: CheckCircle2 };
    }
    if (state === "rendering" || state === "processing") {
      return { label: "Rendering...", color: "bg-amber-950/80 text-amber-300 border-amber-500/30 animate-pulse", icon: Loader2 };
    }
    if (state === "story_ready" || state === "planned") {
      return { label: "Story Ready", color: "bg-indigo-950/80 text-indigo-300 border-indigo-500/30", icon: Sparkles };
    }
    if (state === "failed") {
      return { label: "Failed", color: "bg-rose-950/80 text-rose-400 border-rose-500/30", icon: AlertCircle };
    }
    return { label: "Draft", color: "bg-zinc-900/80 text-zinc-300 border-zinc-700/40", icon: Film };
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
          <div className="flex justify-center gap-3">
            <Link
              href="/projects"
              className="rounded-xl border border-white/[0.1] bg-white/[0.05] px-4 py-2.5 text-xs font-semibold text-white hover:bg-white/[0.1]"
            >
              Go to Projects
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

  const badge = getLifecycleBadge(project.lifecycle_state, project.status);
  const BadgeIcon = badge.icon;

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
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <h1 className="text-lg sm:text-xl font-bold text-white truncate max-w-xs sm:max-w-md">
                {project.title}
              </h1>
              {/* Lifecycle State Badge */}
              <span className={`inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase border ${badge.color}`}>
                <BadgeIcon className="h-3 w-3 shrink-0" />
                <span>{badge.label}</span>
              </span>
            </div>
            <p className="text-xs text-zinc-400">
              Story Editor • ~{Math.round(project.duration_seconds)}s • {project.scenes.length} Scenes • Voice: {project.voice}
            </p>
          </div>
        </div>

        {/* Primary Action Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Version History Trigger */}
          <button
            onClick={handleOpenHistory}
            className="flex items-center gap-1.5 rounded-xl border border-white/[0.1] bg-white/[0.03] hover:bg-white/[0.07] px-3 py-2 text-xs font-semibold text-zinc-300 hover:text-white transition-all"
            title="View immutable version history and restore points"
          >
            <History className="h-3.5 w-3.5 text-cyan-400" />
            <span>History ({project.versions?.length || 1})</span>
          </button>

          {/* Duplicate Project Trigger */}
          <button
            onClick={handleDuplicateProject}
            disabled={isDuplicating}
            className="flex items-center gap-1.5 rounded-xl border border-white/[0.1] bg-white/[0.03] hover:bg-white/[0.07] px-3 py-2 text-xs font-semibold text-zinc-300 hover:text-white transition-all disabled:opacity-50"
            title="Duplicate as an independent project variant"
          >
            {isDuplicating ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin text-purple-400" />
            ) : (
              <Copy className="h-3.5 w-3.5 text-purple-400" />
            )}
            <span>Duplicate</span>
          </button>

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
            <span>{renderStep}</span>
          </div>
        </div>
      )}

      {/* Qualitative Feedback Card (Honest, explainable review bullets) */}
      {project.qualitative_feedback && project.qualitative_feedback.length > 0 && (
        <div className="mb-6 p-4 rounded-2xl border border-white/[0.08] bg-white/[0.02] flex flex-col gap-2">
          <div className="flex items-center gap-2 text-xs font-bold text-zinc-300">
            <Info className="h-3.5 w-3.5 text-cyan-400" />
            <span>Story Pacing & Structure Insights</span>
          </div>
          <div className="flex flex-wrap gap-2 pt-1">
            {project.qualitative_feedback.map((bullet, bIdx) => (
              <span
                key={bIdx}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs bg-cyan-950/40 border border-cyan-500/25 text-cyan-200"
              >
                <Check className="h-3 w-3 text-cyan-400 shrink-0" />
                <span>{bullet}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Mobile Tab Switcher */}
      <div className="flex lg:hidden items-center justify-center p-1 bg-white/[0.03] border border-white/[0.08] rounded-xl mb-6">
        <button
          onClick={() => setMobileTab("storyboard")}
          className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${
            mobileTab === "storyboard"
              ? "bg-cyan-500 text-black shadow-md"
              : "text-zinc-400 hover:text-white"
          }`}
        >
          Storyboard ({project.scenes.length})
        </button>
        <button
          onClick={() => setMobileTab("preview")}
          className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${
            mobileTab === "preview"
              ? "bg-cyan-500 text-black shadow-md"
              : "text-zinc-400 hover:text-white"
          }`}
        >
          Video Preview
        </button>
      </div>

      {/* 2-Column Responsive Layout: Left Storyboard, Right Sticky Preview */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Storyboard Scenes (VidSnap edits the story!) */}
        <div className={`lg:col-span-7 flex flex-col gap-6 ${mobileTab === "preview" ? "hidden lg:flex" : "flex"}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Layers className="h-4 w-4 text-cyan-400" />
              <h2 className="text-sm font-bold uppercase tracking-wider text-white">
                Story Scenes ({project.scenes.length})
              </h2>
            </div>

            <button
              onClick={handleRegenerateStory}
              disabled={isRegeneratingStory}
              className="flex items-center gap-1 text-xs font-semibold text-purple-400 hover:text-purple-300 transition-colors"
            >
              <RotateCcw className={`h-3.5 w-3.5 ${isRegeneratingStory ? "animate-spin" : ""}`} />
              <span>Regenerate Angle</span>
            </button>
          </div>

          {/* Scene Cards List */}
          <div className="flex flex-col gap-4">
            {project.scenes.map((scene, idx) => {
              const isSelected = selectedSceneIndex === idx;

              return (
                <div
                  key={scene.id}
                  onClick={() => handleSelectScene(idx)}
                  className={`glass-card rounded-2xl p-4 transition-all cursor-pointer border ${
                    isSelected
                      ? "border-cyan-500 shadow-lg shadow-cyan-500/10 bg-cyan-950/20"
                      : "border-white/[0.08] hover:border-white/[0.18]"
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

                      {/* Try Another Hook Button on Scene 1 */}
                      {scene.order === 1 && (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleOpenHookModal();
                          }}
                          className="flex items-center gap-1 px-2.5 py-0.5 rounded-md text-[10px] font-bold text-amber-300 bg-amber-500/15 border border-amber-500/30 hover:bg-amber-500/25 transition-all shadow-sm"
                          title="Try 2 distinct strategic hook alternatives"
                        >
                          <Sparkles className="h-3 w-3 text-amber-400" />
                          <span>Try Another Hook</span>
                        </button>
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
                  <div className="flex flex-col sm:flex-row items-start gap-4 pt-3">
                    {/* Visual Thumbnail & Direct Creative Controls */}
                    <div className="flex flex-col gap-1.5 w-full sm:w-36 flex-shrink-0" onClick={(e) => e.stopPropagation()}>
                      <div className="relative aspect-square w-full rounded-xl overflow-hidden bg-zinc-900 border border-white/[0.1] group">
                        <img
                          src={scene.visual_url}
                          alt={`Scene ${scene.order}`}
                          className="w-full h-full object-cover"
                        />
                        <div className="absolute top-1.5 right-1.5 flex items-center gap-1">
                          {scene.visual_source === "custom" && (
                            <span className="bg-emerald-600/90 backdrop-blur-md px-1.5 py-0.5 rounded text-[9px] font-bold text-white">
                              CUSTOM
                            </span>
                          )}
                          {scene.visual_source === "ai" && (
                            <span className="bg-purple-900/90 backdrop-blur-md px-1.5 py-0.5 rounded text-[9px] font-bold text-purple-200">
                              AI
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Hidden file input for custom B-roll upload */}
                      <input
                        type="file"
                        accept="image/*,video/*"
                        ref={(el) => { fileInputRefs.current[scene.order] = el; }}
                        onChange={(e) => handleBrollFileChange(scene.order, e)}
                        className="hidden"
                      />

                      {/* Action buttons: Upload B-Roll & Choose Alternatives */}
                      <div className="grid grid-cols-2 gap-1 w-full">
                        <button
                          type="button"
                          disabled={isUploadingBroll === scene.order}
                          onClick={() => handleUploadBrollClick(scene.order)}
                          className="flex items-center justify-center gap-1 py-1 px-1.5 rounded-lg text-[10px] font-semibold text-emerald-300 bg-emerald-500/10 border border-emerald-500/25 hover:bg-emerald-500/20 transition-all disabled:opacity-40"
                          title="Upload custom B-roll image or video"
                        >
                          <Upload className="h-3 w-3" />
                          <span>{isUploadingBroll === scene.order ? "..." : "Upload"}</span>
                        </button>

                        <button
                          type="button"
                          onClick={() => handleOpenVisualAlternatives(scene.order)}
                          className="flex items-center justify-center gap-1 py-1 px-1.5 rounded-lg text-[10px] font-semibold text-cyan-300 bg-cyan-500/10 border border-cyan-500/25 hover:bg-cyan-500/20 transition-all"
                          title="Select from stock or project visual alternatives"
                        >
                          <ImageIcon className="h-3 w-3" />
                          <span>Alts</span>
                        </button>
                      </div>

                      {/* Row 2: Regenerate AI Visual & Reset */}
                      <div className="flex items-center gap-1 w-full">
                        <button
                          type="button"
                          disabled={regeneratingVisualSceneId === scene.id}
                          onClick={() => handleRegenerateVisual(scene.order, scene.id)}
                          className="flex-1 flex items-center justify-center gap-1 py-1 px-2 rounded-lg text-[10px] font-semibold text-purple-300 bg-purple-500/10 border border-purple-500/20 hover:bg-purple-500/25 transition-all disabled:opacity-40"
                        >
                          <Sparkles className={`h-3 w-3 ${regeneratingVisualSceneId === scene.id ? "animate-spin" : ""}`} />
                          <span>{regeneratingVisualSceneId === scene.id ? "..." : "Regen AI"}</span>
                        </button>

                        {scene.visual_source === "custom" && (
                          <button
                            type="button"
                            onClick={() => handleRemoveCustomVisual(scene.order)}
                            className="p-1 rounded-lg text-zinc-400 hover:text-red-400 hover:bg-red-500/10 border border-white/[0.08] transition-all"
                            title="Revert to stock fallback"
                          >
                            <RotateCcw className="h-3 w-3" />
                          </button>
                        )}
                      </div>
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

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        <div>
                          <label className="block text-[10px] font-semibold uppercase tracking-wider text-zinc-500 mb-1">
                            Screen Caption
                          </label>
                          <input
                            type="text"
                            value={scene.caption}
                            onChange={(e) => handleSceneChange(scene.id, "caption", e.target.value)}
                            className="w-full rounded-xl border border-white/[0.1] bg-white/[0.02] px-2.5 py-1.5 text-xs font-bold text-cyan-300 placeholder-zinc-500 focus:border-cyan-400 focus:outline-none"
                          />
                        </div>

                        <div>
                          <label className="block text-[10px] font-semibold uppercase tracking-wider text-zinc-500 mb-1">
                            Visual Prompt Direction
                          </label>
                          <input
                            type="text"
                            value={scene.visual_direction || ""}
                            onChange={(e) => handleSceneChange(scene.id, "visual_direction", e.target.value)}
                            placeholder="Visual scene direction..."
                            className="w-full rounded-xl border border-white/[0.1] bg-white/[0.02] px-2.5 py-1.5 text-xs text-zinc-300 placeholder-zinc-600 focus:border-cyan-400 focus:outline-none"
                          />
                        </div>
                      </div>

                      {/* Camera Motion & Transition Controls */}
                      <div className="grid grid-cols-2 gap-2 pt-1 border-t border-white/[0.04]">
                        <div>
                          <label className="block text-[10px] font-semibold uppercase tracking-wider text-zinc-500 mb-1">
                            Camera Motion
                          </label>
                          <select
                            value={scene.motion || scene.visual_plan?.motion || "slow_zoom_in"}
                            onChange={(e) => handleSceneChange(scene.id, "motion", e.target.value)}
                            className="w-full rounded-xl border border-white/[0.1] bg-zinc-900 px-2.5 py-1.5 text-xs text-zinc-300 focus:border-cyan-400 focus:outline-none capitalize"
                          >
                            <option value="slow_zoom_in">Slow Zoom In</option>
                            <option value="slow_zoom_out">Slow Zoom Out</option>
                            <option value="pan_left">Pan Left</option>
                            <option value="pan_right">Pan Right</option>
                            <option value="tilt_up">Tilt Up</option>
                          </select>
                        </div>

                        <div>
                          <label className="block text-[10px] font-semibold uppercase tracking-wider text-zinc-500 mb-1">
                            Transition
                          </label>
                          <select
                            value={scene.transition || scene.visual_plan?.transition || "crossfade"}
                            onChange={(e) => handleSceneChange(scene.id, "transition", e.target.value)}
                            className="w-full rounded-xl border border-white/[0.1] bg-zinc-900 px-2.5 py-1.5 text-xs text-zinc-300 focus:border-cyan-400 focus:outline-none capitalize"
                          >
                            <option value="crossfade">Crossfade (0.3s)</option>
                            <option value="short_fade">Short Fade</option>
                            <option value="cut">Direct Cut</option>
                          </select>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Ask VidSnap: Compact Creative Control Layer */}
          <div className="glass-card rounded-2xl p-4 border border-cyan-500/30 bg-gradient-to-br from-cyan-950/20 via-zinc-900/40 to-purple-950/20 shadow-xl">
            <div className="flex items-center gap-2 mb-2">
              <Bot className="h-4 w-4 text-cyan-400" />
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                Ask VidSnap AI
              </h3>
              <span className="text-[10px] text-zinc-400">
                • 1-Click Creative Commands & Snapshot Protection
              </span>
            </div>

            {/* Quick Command Chips */}
            <div className="flex flex-wrap gap-1.5 mb-3">
              {CREATOR_COMMAND_CHIPS.map((chip) => (
                <button
                  key={chip.label}
                  type="button"
                  disabled={isAssistantWorking}
                  onClick={() => handleAskAssistant(chip.cmd)}
                  className="rounded-lg border border-white/[0.08] bg-white/[0.03] px-2.5 py-1 text-[11px] text-zinc-300 hover:text-white hover:border-cyan-500/40 transition-all active:scale-98 disabled:opacity-50"
                >
                  {chip.label}
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
                placeholder="Type a creative intent (e.g. 'Make this 20 seconds', 'Replace scene 2')..."
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
              <div className="mt-3 p-2.5 rounded-xl bg-white/[0.04] border border-cyan-500/30 text-xs text-cyan-200 animate-fadeIn flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-cyan-400 shrink-0 mt-0.5" />
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

                {/* Bottom Kinetic Caption Overlay (Matching ASS 1080x1920 layout) */}
                <div className="phone-caption-overlay">
                  <p className="phone-caption-text">
                    {currentScene.caption.split(" ").map((word, idx) => {
                      const isFirst = idx === 0;
                      const isEmphasis = word.length > 6 || word.toUpperCase() === word;
                      return (
                        <span
                          key={idx}
                          className={
                            isFirst
                              ? "phone-caption-active-word mr-1"
                              : isEmphasis
                              ? "phone-caption-emphasis-word mr-1"
                              : "mr-1"
                          }
                        >
                          {word}
                        </span>
                      );
                    })}
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

          {/* Quality Gate Diagnostic (Phase 7: Real Reliability Gate) */}
          <div className="mt-3 w-full max-w-[320px] glass-card rounded-2xl p-4 border border-white/[0.1] bg-[#0c0f18]/90 shadow-xl flex flex-col gap-2.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <ShieldCheck className="h-4 w-4 text-emerald-400" />
                <span className="text-xs font-bold text-white uppercase tracking-wider">
                  Quality Gate
                </span>
              </div>
              {project.video_url ? (
                project.quality_gate?.passed ? (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                    ✨ Ready to Post
                  </span>
                ) : project.quality_gate?.blocking_issues?.length > 0 ? (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40">
                    ❌ Action Required
                  </span>
                ) : (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">
                    ⚠️ Review Warnings
                  </span>
                )
              ) : (
                <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-zinc-800 text-zinc-400 border border-white/5">
                  Pre-render Plan
                </span>
              )}
            </div>

            {/* Check Matrix */}
            <div className="grid grid-cols-2 gap-1.5 text-[11px] pt-1 border-t border-white/[0.04]">
              <div className="flex items-center gap-1 text-zinc-300">
                <Check className="h-3 w-3 text-emerald-400 shrink-0" />
                <span>1080×1920 (9:16)</span>
              </div>
              <div className="flex items-center gap-1 text-zinc-300">
                <Check className="h-3 w-3 text-emerald-400 shrink-0" />
                <span>Audio Sync</span>
              </div>
              <div className="flex items-center gap-1 text-zinc-300">
                <Check className="h-3 w-3 text-emerald-400 shrink-0" />
                <span>Safe Caption Zone</span>
              </div>
              <div className="flex items-center gap-1 text-zinc-300">
                <Check className="h-3 w-3 text-emerald-400 shrink-0" />
                <span>Best-Effort Continuity</span>
              </div>
            </div>

            {/* Quality Warnings (if any) */}
            {((project.quality_gate?.warnings && project.quality_gate.warnings.length > 0) ||
              (project.quality_warnings && project.quality_warnings.length > 0)) && (
              <div className="mt-1 p-2 rounded-xl bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-200 flex flex-col gap-1">
                {(project.quality_gate?.warnings || project.quality_warnings || []).map((w: string, i: number) => (
                  <div key={i} className="flex items-start gap-1.5">
                    <AlertCircle className="h-3 w-3 text-amber-400 shrink-0 mt-0.5" />
                    <span>{w}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modal 1: Version History Drawer / Modal */}
      {showHistoryModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-fadeIn">
          <div className="glass-card rounded-3xl p-6 max-w-xl w-full border border-white/[0.12] bg-[#0c0f18] shadow-2xl max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between pb-4 border-b border-white/[0.08]">
              <div className="flex items-center gap-2">
                <History className="h-5 w-5 text-cyan-400" />
                <div>
                  <h3 className="text-base font-bold text-white">
                    Version History
                  </h3>
                  <p className="text-[11px] text-zinc-400">
                    Immutable snapshots of past story states. Restoring never overwrites history.
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowHistoryModal(false)}
                className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.06]"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto py-4 flex flex-col gap-3">
              {isLoadingVersions ? (
                <div className="py-12 text-center text-zinc-400 flex flex-col items-center gap-2">
                  <Loader2 className="h-6 w-6 animate-spin text-cyan-400" />
                  <span className="text-xs">Loading immutable snapshots...</span>
                </div>
              ) : versions.length === 0 ? (
                <div className="py-12 text-center text-zinc-500 text-xs">
                  No previous snapshots found for this project.
                </div>
              ) : (
                [...versions].reverse().map((v) => {
                  const vDate = new Date(v.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                  return (
                    <div
                      key={v.version_number}
                      className="p-3.5 rounded-2xl border border-white/[0.06] bg-white/[0.02] hover:border-white/[0.15] transition-all flex flex-col gap-2"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded-md text-[11px] font-mono font-bold bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
                            v{v.version_number}
                          </span>
                          <span className="text-xs font-semibold text-white">
                            {v.label}
                          </span>
                        </div>
                        <span className="text-[11px] font-mono text-zinc-500">
                          {vDate}
                        </span>
                      </div>

                      <p className="text-xs text-zinc-300 italic line-clamp-1">
                        "{v.hook}"
                      </p>

                      <div className="flex items-center justify-between pt-1 border-t border-white/[0.04]">
                        <span className="text-[10px] text-zinc-400">
                          {v.scenes?.length || 0} scenes • ~{Math.round(v.duration_seconds)}s • Voice: {v.voice}
                        </span>
                        <button
                          onClick={() => handleRestoreVersion(v.version_number)}
                          disabled={isRestoringVersion === v.version_number}
                          className="px-3 py-1 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 text-xs font-bold transition-all disabled:opacity-50 flex items-center gap-1"
                        >
                          {isRestoringVersion === v.version_number ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : (
                            <RotateCcw className="h-3 w-3" />
                          )}
                          <span>Restore</span>
                        </button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modal 2: Hook Alternatives Modal */}
      {showHookModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-fadeIn">
          <div className="glass-card rounded-3xl p-6 max-w-lg w-full border border-amber-500/30 bg-[#0c0f18] shadow-2xl flex flex-col">
            <div className="flex items-center justify-between pb-4 border-b border-white/[0.08]">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-amber-400" />
                <div>
                  <h3 className="text-base font-bold text-white">
                    Try Another Hook
                  </h3>
                  <p className="text-[11px] text-zinc-400">
                    2 distinct strategic angles faithful to your topic and domain.
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowHookModal(false)}
                className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.06]"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="py-4 flex flex-col gap-4">
              {isLoadingHooks ? (
                <div className="py-12 text-center text-zinc-400 flex flex-col items-center gap-2">
                  <Loader2 className="h-6 w-6 animate-spin text-amber-400" />
                  <span className="text-xs">Formulating strategic alternative hooks...</span>
                </div>
              ) : hookAlternatives.length === 0 ? (
                <div className="py-8 text-center text-zinc-500 text-xs">
                  No hook alternatives available.
                </div>
              ) : (
                hookAlternatives.map((alt) => (
                  <div
                    key={alt.id}
                    className="p-4 rounded-2xl border border-white/[0.08] bg-white/[0.02] hover:border-amber-500/40 transition-all flex flex-col gap-2.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="px-2.5 py-0.5 rounded-md text-[10px] uppercase font-bold tracking-wider bg-amber-500/15 text-amber-300 border border-amber-500/30">
                        {alt.label}
                      </span>
                      <span className="text-[10px] font-mono text-zinc-500 uppercase">
                        Strategy: {alt.strategy}
                      </span>
                    </div>

                    <p className="text-xs font-medium text-white leading-relaxed">
                      "{alt.hook}"
                    </p>

                    <div className="flex items-center justify-between pt-2 border-t border-white/[0.06]">
                      <span className="text-[10px] font-bold text-cyan-400 uppercase">
                        Caption: {alt.caption}
                      </span>
                      <button
                        onClick={() => handleApplyHook(alt.hook, alt.caption)}
                        disabled={isApplyingHook}
                        className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-black font-bold text-xs shadow-md shadow-amber-500/20 transition-all disabled:opacity-50 flex items-center gap-1 active:scale-98"
                      >
                        {isApplyingHook ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin text-black" />
                        ) : (
                          <Check className="h-3.5 w-3.5 text-black" />
                        )}
                        <span>Use This Hook</span>
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modal 3: Visual Alternatives & Asset Selector Modal (Phase 7) */}
      {showVisualAlternativesModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-fadeIn">
          <div className="glass-card rounded-3xl p-6 max-w-2xl w-full border border-cyan-500/30 bg-[#0c0f18] shadow-2xl max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between pb-4 border-b border-white/[0.08]">
              <div className="flex items-center gap-2">
                <ImageIcon className="h-5 w-5 text-cyan-400" />
                <div>
                  <h3 className="text-base font-bold text-white">
                    Select Visual for Scene #{visualAlternativesSceneOrder}
                  </h3>
                  <p className="text-[11px] text-zinc-400">
                    Choose from stock library, project assets, or revert to default.
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowVisualAlternativesModal(false)}
                className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.06]"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto py-4">
              {isLoadingAlternatives ? (
                <div className="py-12 text-center text-zinc-400 flex flex-col items-center gap-2">
                  <Loader2 className="h-6 w-6 animate-spin text-cyan-400" />
                  <span className="text-xs">Loading visual candidates...</span>
                </div>
              ) : visualAlternatives.length === 0 ? (
                <div className="py-8 text-center text-zinc-500 text-xs">
                  No visual alternatives found.
                </div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {visualAlternatives.map((alt) => (
                    <div
                      key={alt.filename}
                      className="group relative rounded-2xl overflow-hidden border border-white/[0.08] hover:border-cyan-400/50 bg-white/[0.02] flex flex-col transition-all cursor-pointer"
                      onClick={() => handleSelectVisualAlternative(alt)}
                    >
                      <div className="aspect-[9/16] w-full bg-black/50 overflow-hidden relative">
                        {alt.filename.endsWith(".mp4") ? (
                          <video
                            src={alt.url}
                            muted
                            playsInline
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                          />
                        ) : (
                          <img
                            src={alt.url}
                            alt={alt.label}
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                          />
                        )}
                        <span className="absolute top-2 left-2 px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider bg-black/75 text-cyan-300 border border-white/10">
                          {alt.domain || alt.type}
                        </span>
                      </div>
                      <div className="p-2.5 flex items-center justify-between gap-1">
                        <span className="text-xs font-semibold text-zinc-200 truncate">
                          {alt.label}
                        </span>
                        <button
                          type="button"
                          className="shrink-0 px-2 py-1 rounded-lg bg-cyan-500/20 text-cyan-300 group-hover:bg-cyan-500 group-hover:text-black text-[10px] font-bold transition-all"
                        >
                          Use
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="pt-3 border-t border-white/[0.08] flex items-center justify-between">
              <button
                type="button"
                onClick={() => {
                  if (visualAlternativesSceneOrder !== null) {
                    handleRemoveCustomVisual(visualAlternativesSceneOrder);
                    setShowVisualAlternativesModal(false);
                  }
                }}
                className="text-xs text-rose-400 hover:text-rose-300 flex items-center gap-1.5 transition-colors"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                <span>Revert to Stock Fallback</span>
              </button>
              <button
                type="button"
                onClick={() => setShowVisualAlternativesModal(false)}
                className="px-4 py-1.5 rounded-xl bg-white/[0.05] hover:bg-white/[0.1] text-zinc-300 text-xs font-semibold transition-all"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
