import { Settings as SettingsIcon, Key, Sliders, Shield } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-10 w-full">
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold tracking-tight text-white mb-1">
          Settings
        </h1>
        <p className="text-sm text-zinc-400">
          Manage your AI integrations, audio profiles, and preferences.
        </p>
      </div>

      <div className="space-y-6">
        {/* ElevenLabs API Card */}
        <div className="glass-card rounded-2xl p-6 border-zinc-800">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-500/20 text-indigo-400">
              <Key className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">ElevenLabs Voice API</h3>
              <p className="text-xs text-zinc-400">
                Connected via local environment variable (<code className="text-indigo-300">.env</code>).
              </p>
            </div>
          </div>
          <p className="text-xs text-zinc-500 leading-relaxed">
            VidSnap automatically detects and validates your configured <code className="text-zinc-300">ELEVENLABS_API_KEY</code> on the backend. When unavailable, it automatically transitions to the high-quality local speech engine.
          </p>
        </div>

        {/* Video Engine Config Card */}
        <div className="glass-card rounded-2xl p-6 border-zinc-800">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-purple-500/20 text-purple-400">
              <Sliders className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">FFmpeg 8.0 Video Renderer</h3>
              <p className="text-xs text-zinc-400">
                Resolution: 1080×1920 (9:16 Vertical) • 30 FPS • H.264 High Profile
              </p>
            </div>
          </div>
          <p className="text-xs text-zinc-500 leading-relaxed">
            Framing uses dynamic blurred background padding and speech-duration slide synchronization.
          </p>
        </div>
      </div>
    </div>
  );
}
