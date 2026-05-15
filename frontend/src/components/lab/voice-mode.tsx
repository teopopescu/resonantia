"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, X } from "lucide-react";
import { useAudioRecorder } from "@/lib/hooks/use-audio-recorder";
import { useLabStore } from "@/stores/lab-store";
import { getActiveOrgId } from "@/lib/api";
import { MicPermission } from "./mic-permission";
import { VoiceSseClient } from "./voice-sse-client";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const ACK_CLIPS = [
  "/audio/ack-working-on-that.mp3",
  "/audio/ack-looking-that-up.mp3",
  "/audio/ack-checking-the-run.mp3",
  "/audio/ack-one-moment.mp3",
  "/audio/ack-running-the-tool.mp3",
  "/audio/ack-on-it.mp3",
  "/audio/ack-let-me-check.mp3",
  "/audio/ack-got-it.mp3",
];

type VoiceStatus = "listening" | "silence_detected" | "processing" | "transcribing" | "thinking" | "speaking" | "error";

interface VoiceModeProps {
  onExit: () => void;
}

export default function VoiceMode({ onExit }: VoiceModeProps) {
  const { addMessage, activeConversationId } = useLabStore();
  const recorder = useAudioRecorder();
  const [status, setStatus] = useState<VoiceStatus>("listening");
  const [errorMsg, setErrorMsg] = useState("");
  const [turnId, setTurnId] = useState<string | null>(null);
  const activeRef = useRef(true);

  // Start listening on mount
  useEffect(() => {
    activeRef.current = true;
    recorder.start();
    return () => {
      activeRef.current = false;
      recorder.reset();
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  function playAckClip() {
    const clip = ACK_CLIPS[Math.floor(Math.random() * ACK_CLIPS.length)];
    const audio = new Audio(clip);
    audio.volume = 0.55;
    void audio.play().catch(() => undefined);
  }

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

      setTurnId(null);
      setStatus("processing");
      playAckClip();

      try {
        const formData = new FormData();
        formData.append("audio", blob, "recording.webm");
        if (activeConversationId) formData.append("conversation_id", activeConversationId);

        const res = await fetch(`${API_URL}/api/v1/voice/turn`, {
          method: "POST",
          body: formData,
          headers: { "X-Org-Id": getActiveOrgId() },
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error((err as { detail?: string }).detail || "Voice processing failed");
        }

        const data = (await res.json()) as { turn_id?: string; turnId?: string };
        setTurnId(data.turn_id || data.turnId || null);
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
    processing: "Processing...",
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
        className="absolute top-4 right-4 p-2 rounded-[3px] text-ink-muted hover:text-ink hover:bg-bg-sunk transition-colors z-10"
      >
        <X size={18} />
      </button>

      {/* Mic circle with pulsing rings */}
      <div className="relative mb-6">
        <AnimatePresence>
          {isActive && (
            <>
              {[1, 2, 3].map((ring) => (
                <motion.div
                  key={ring}
                  initial={{ scale: 1, opacity: 0.3 }}
                  animate={{ scale: 1 + ring * 0.3, opacity: 0 }}
                  transition={{ duration: 2, repeat: Infinity, delay: ring * 0.4 }}
                  className="absolute inset-0 rounded-full border-2 border-brand/30"
                />
              ))}
            </>
          )}
        </AnimatePresence>

        <button
          onClick={() => {
            if (isActive) {
              recorder.stop();
            }
          }}
          className={`relative w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300 ${
            isActive
              ? "bg-brand text-white"
              : status === "speaking"
              ? "bg-brand/80 text-white"
              : status === "error"
              ? "bg-mch-soft text-mch"
              : "bg-bg-sunk text-ink-muted"
          }`}
          style={
            isActive ? { boxShadow: "0 8px 24px -8px rgba(31,77,58,0.25), inset 0 0 0 1px rgba(0,0,0,0.06)" } : undefined
          }
        >
          {isActive ? (
            <Mic size={30} className="animate-pulse" />
          ) : status === "speaking" ? (
            <motion.div
              animate={{ scale: [1, 1.1, 1] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            >
              <Mic size={30} />
            </motion.div>
          ) : status === "error" ? (
            <X size={30} />
          ) : (
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              className="w-6 h-6 border-2 border-ink-subtle border-t-brand rounded-full"
            />
          )}
        </button>

        {status === "silence_detected" && (
          <svg className="absolute inset-0 w-24 h-24 -rotate-90" viewBox="0 0 96 96">
            <circle
              cx="48" cy="48" r="46"
              fill="none"
              stroke="#1F4D3A"
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
            className="w-1.5 rounded-full bg-brand/60"
            style={{ minHeight: 4 }}
          />
        ))}
      </div>

      {/* Status label */}
      <motion.p
        key={status}
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        className={`font-mono text-[12px] uppercase tracking-[0.04em] font-medium ${
          status === "error" ? "text-mch" : "text-ink-muted"
        }`}
      >
        {statusLabels[status].toLowerCase()}
      </motion.p>

      {/* Help text */}
      <p className="font-mono text-[10.5px] uppercase tracking-[0.04em] text-ink-subtle mt-3">
        {isActive ? "tap mic to send \u00b7 esc to exit" : ""}
      </p>
      <MicPermission />
      <VoiceSseClient
        turnId={turnId}
        onStatus={(next) => {
          if (next === "processing") setStatus("processing");
          if (next === "speaking") setStatus("speaking");
          if (next === "error") setStatus("error");
        }}
        onDone={() => {
          if (activeRef.current) {
            setStatus("listening");
            void recorder.start();
          }
        }}
      />
    </div>
  );
}
