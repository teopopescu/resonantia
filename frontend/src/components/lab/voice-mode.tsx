"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, X } from "lucide-react";
import { useAudioRecorder } from "@/lib/hooks/use-audio-recorder";
import { useAudioPlayer } from "@/lib/hooks/use-audio-player";
import { useLabStore } from "@/stores/lab-store";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type VoiceStatus = "listening" | "silence_detected" | "transcribing" | "thinking" | "speaking" | "error";

interface VoiceModeProps {
  onExit: () => void;
}

export default function VoiceMode({ onExit }: VoiceModeProps) {
  const { addMessage } = useLabStore();
  const recorder = useAudioRecorder();
  const player = useAudioPlayer();
  const [status, setStatus] = useState<VoiceStatus>("listening");
  const [errorMsg, setErrorMsg] = useState("");
  const activeRef = useRef(true);

  // Start listening on mount
  useEffect(() => {
    activeRef.current = true;
    recorder.start();
    return () => {
      activeRef.current = false;
      recorder.reset();
      player.stop();
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Update status from recorder state
  useEffect(() => {
    if (recorder.state === "listening") setStatus("listening");
    if (recorder.state === "silence_detected") setStatus("silence_detected");
    if (recorder.error) {
      setStatus("error");
      setErrorMsg(recorder.error);
    }
  }, [recorder.state, recorder.error]);

  // When audioBlob is ready, send to backend
  useEffect(() => {
    if (!recorder.audioBlob || !activeRef.current) return;

    const processVoice = async () => {
      const blob = recorder.audioBlob!;
      recorder.reset();

      // Add placeholder user message
      addMessage("user", "Transcribing...");
      setStatus("transcribing");

      try {
        const formData = new FormData();
        formData.append("audio", blob, "recording.webm");
        formData.append("conversation_id", "voice-session");

        setStatus("thinking");

        const res = await fetch(`${API_URL}/api/v1/voice/chat`, {
          method: "POST",
          body: formData,
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error((err as { detail?: string }).detail || "Voice processing failed");
        }

        const data = await res.json();

        if (data.error === "no_speech_detected") {
          // Resume listening
          setStatus("listening");
          if (activeRef.current) recorder.start();
          return;
        }

        // Add the real transcription and response
        addMessage("user", data.transcription);
        addMessage("assistant", data.response);

        // Play TTS audio
        if (data.audio_url && activeRef.current) {
          setStatus("speaking");
          const audioUrl = `${API_URL}${data.audio_url}`;
          console.log("[Voice] Playing TTS audio:", audioUrl);
          try {
            await player.play(audioUrl);
            console.log("[Voice] TTS playback finished");
          } catch (playErr) {
            console.warn("[Voice] TTS playback error:", playErr);
          }
        } else {
          console.log("[Voice] No audio_url in response or voice mode deactivated");
        }

        // Resume listening if still active
        if (activeRef.current) {
          setStatus("listening");
          recorder.start();
        }
      } catch (err: unknown) {
        const e = err as { message?: string };
        setStatus("error");
        setErrorMsg(e.message || "Voice processing failed");
        addMessage("assistant", `Voice error: ${e.message}`);
        // Resume listening after error
        setTimeout(() => {
          if (activeRef.current) {
            setStatus("listening");
            recorder.start();
          }
        }, 2000);
      }
    };

    processVoice();
  }, [recorder.audioBlob]); // eslint-disable-line react-hooks/exhaustive-deps

  // Keyboard: Escape to exit
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onExit();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onExit]);

  const statusLabels: Record<VoiceStatus, string> = {
    listening: "Listening...",
    silence_detected: `Sending in ${Math.ceil(recorder.silenceCountdown / 1000)}s...`,
    transcribing: "Transcribing...",
    thinking: "Thinking...",
    speaking: "Speaking...",
    error: errorMsg || "Error",
  };

  const isActive = status === "listening" || status === "silence_detected";

  // Generate bar heights from audio level
  const bars = 7;
  const barHeights = Array.from({ length: bars }, (_, i) => {
    const center = Math.abs(i - 3) / 3;
    return Math.max(4, recorder.audioLevel * (1 - center * 0.5) * 48);
  });

  return (
    <div className="flex flex-col items-center justify-center py-8 px-6 relative">
      {/* Exit button */}
      <button
        onClick={onExit}
        className="absolute top-4 right-4 p-2 rounded-lg text-muted hover:text-charcoal hover:bg-cream transition-colors z-10"
      >
        <X size={18} />
      </button>

      {/* Mic circle with pulsing rings */}
      <div className="relative mb-6">
        {/* Pulse rings */}
        <AnimatePresence>
          {isActive && (
            <>
              {[1, 2, 3].map((ring) => (
                <motion.div
                  key={ring}
                  initial={{ scale: 1, opacity: 0.3 }}
                  animate={{ scale: 1 + ring * 0.3, opacity: 0 }}
                  transition={{ duration: 2, repeat: Infinity, delay: ring * 0.4 }}
                  className="absolute inset-0 rounded-full border-2 border-amber/30"
                />
              ))}
            </>
          )}
        </AnimatePresence>

        {/* Main mic button */}
        <button
          onClick={() => {
            if (isActive) {
              recorder.stop();
            }
          }}
          className={`relative w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300 ${
            isActive
              ? "bg-amber text-charcoal shadow-lg shadow-amber/20"
              : status === "speaking"
              ? "bg-amber/80 text-charcoal"
              : status === "error"
              ? "bg-red-100 text-red-600"
              : "bg-cream-dark text-muted"
          }`}
        >
          {isActive ? (
            <Mic size={32} className="animate-pulse" />
          ) : status === "speaking" ? (
            <motion.div
              animate={{ scale: [1, 1.1, 1] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            >
              <Mic size={32} />
            </motion.div>
          ) : status === "error" ? (
            <X size={32} />
          ) : (
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              className="w-6 h-6 border-2 border-muted border-t-amber rounded-full"
            />
          )}
        </button>

        {/* Silence countdown ring */}
        {status === "silence_detected" && (
          <svg className="absolute inset-0 w-24 h-24 -rotate-90" viewBox="0 0 96 96">
            <circle
              cx="48" cy="48" r="46"
              fill="none"
              stroke="#D4A843"
              strokeWidth="3"
              strokeDasharray={`${((1500 - recorder.silenceCountdown) / 1500) * 289} 289`}
              strokeLinecap="round"
            />
          </svg>
        )}
      </div>

      {/* Audio level bars */}
      <div className="flex items-end gap-1 h-12 mb-4">
        {barHeights.map((h, i) => (
          <motion.div
            key={i}
            animate={{ height: isActive ? h : 4 }}
            transition={{ duration: 0.1 }}
            className="w-1.5 rounded-full bg-amber/60"
            style={{ minHeight: 4 }}
          />
        ))}
      </div>

      {/* Status label */}
      <motion.p
        key={status}
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        className={`text-sm font-medium ${
          status === "error" ? "text-red-500" : "text-muted"
        }`}
      >
        {statusLabels[status]}
      </motion.p>

      {/* Help text */}
      <p className="text-xs text-muted/50 mt-3">
        {isActive ? "Tap the mic to send manually \u00b7 Esc to exit" : ""}
      </p>
    </div>
  );
}
