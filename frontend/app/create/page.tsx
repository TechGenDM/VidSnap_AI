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
return <div>Upload configured</div>;}