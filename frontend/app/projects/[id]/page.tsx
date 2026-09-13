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
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
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
          router.push("/projects");
        }
      } catch (err) {
        console.error("Failed to load project", err);
      } finally {
        setIsLoading(false);
      }
    };

    loadProject();
  }, [projectId, router]);

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

  const saveScenes = async () => {
    if (!project) return;
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
      }
    } catch (e) {
      console.error("Failed to save scenes", e);
    } finally {
      setIsSaving(false);
</div></div>);}