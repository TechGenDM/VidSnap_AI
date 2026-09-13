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

return <div>Quick Reel Loading...</div>;}