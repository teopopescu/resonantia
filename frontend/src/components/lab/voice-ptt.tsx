"use client";

/**
 * Push-to-talk voice surface.
 *
 * Differs from VoiceMode (VAD): the user explicitly holds Spacebar
 * (or the on-screen mic button) to record, releases to send. There is
 * no auto-silence detection — better for noisy bench environments and
 * for foot-pedal mappings (most foot pedals key to Spacebar by default).
 *
 * Hands-free wake-word triggering is intentionally not in this component;
 * that lives in a future PR using openWakeWord.
 */

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, X } from "lucide-react";
import { usePttRecorder } from "@/lib/hooks/use-ptt-recorder";
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

type PttStatus =
  | "idle"
  | "recording"
  | "processing"
  | "transcribing"
  | "thinking"
  | "speaking"
  | "error";

interface VoicePttProps {
  onExit: () => void;
}

export default function VoicePtt({ onExit }: VoicePttProps) {
  const { addMessage, activeConversationId } = useLabStore();
  const recorder = usePttRecorder();
  const [status, setStatus] = useState<PttStatus>("idle");
  const [errorMsg, setErrorMsg] = useState("");
  const [turnId, setTurnId] = useState<string | null>(null);
  const activeRef = useRef(true);
  // True only while the mouse is the active input source — set on
  // mouse/touch start, cleared on mouse/touch end. Lets us ignore
  // mouseLeave when the user is holding Space (keyboard hold).
  const mouseHoldingRef = useRef(false);
  // Dedupes the send effect so the same audioBlob isn't shipped twice
  // if React batches state in unexpected order.
  const sendingRef = useRef(false);
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    activeRef.current = true;
    // Focus the panel root so Space presses target our handler instead
    // of leaking to other focused buttons on the page.
    panelRef.current?.focus();
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

  // Mirror recorder.state into our local status for UI.
  useEffect(() => {
    if (recorder.state === "recording") setStatus("recording");
    if (recorder.error) {
      setStatus("error");
      setErrorMsg(recorder.error);
    }
  }, [recorder.state, recorder.error]);

  // Keyboard: Spacebar hold = record, Escape = exit.
  // We ONLY claim Space when the active element is the panel root or
  // an interactive target inside it. That avoids:
  //   - stealing Space from genuine text inputs elsewhere on the page,
  //   - suppressing default Space-activation on focused buttons.
  useEffect(() => {
    const isInteractiveOutside = () => {
      const active = document.activeElement;
      if (!active) return false;
      if (panelRef.current?.contains(active)) return false;
      const tag = active.tagName.toLowerCase();
      // Buttons, links, inputs, selects, contentEditable — let the
      // browser handle Space normally.
      if (
        tag === "input" || tag === "textarea" || tag === "select" ||
        tag === "button" || tag === "a"
      ) return true;
      if (active instanceof HTMLElement && active.isContentEditable) return true;
      return false;
    };

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onExit();
        return;
      }
      if (e.code !== "Space" || e.repeat) return;
      if (isInteractiveOutside()) return;
      if (status === "processing" || status === "thinking" || status === "transcribing" || status === "speaking") return;
      e.preventDefault();
      void recorder.start();
    };
    const onKeyUp = (e: KeyboardEvent) => {
      if (e.code !== "Space") return;
      if (isInteractiveOutside()) return;
      e.preventDefault();
      recorder.stop();
    };

    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("keyup", onKeyUp);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("keyup", onKeyUp);
    };
  }, [recorder, onExit, status]);

  // When a recording finishes, send to backend.
  useEffect(() => {
    if (!recorder.audioBlob || !activeRef.current) return;
    if (sendingRef.current) return; // dedup: a previous send is still in flight
    sendingRef.current = true;

    const send = async () => {
      const blob = recorder.audioBlob!;
      recorder.reset();

      setTurnId(null);
      setStatus("processing");
      playAckClip();

      try {
        const form = new FormData();
        // Match extension to the actual recorded mime so the backend's
        // ffmpeg-based decode picks the right path.
        const ext = blob.type.startsWith("audio/mp4") ? "mp4" : "webm";
        form.append("audio", blob, `ptt.${ext}`);
        if (activeConversationId) form.append("conversation_id", activeConversationId);

        const res = await fetch(`${API_URL}/api/v1/voice/turn`, {
          method: "POST",
          body: form,
          headers: { "X-Org-Id": getActiveOrgId() },
        });
        if (!res.ok) {
          const err = (await res.json().catch(() => ({}))) as { detail?: string };
          throw new Error(err.detail || "Voice processing failed");
        }
        const data = (await res.json()) as { turn_id?: string; turnId?: string };
        setTurnId(data.turn_id || data.turnId || null);
      } catch (err) {
        const msg = err instanceof Error ? err.message : "voice processing failed";
        setStatus("error");
        setErrorMsg(msg);
        addMessage("assistant", `Voice error: ${msg}`);
        setTimeout(() => {
          if (activeRef.current) setStatus("idle");
        }, 1800);
      } finally {
        sendingRef.current = false;
      }
    };

    void send();
  }, [recorder.audioBlob]); // eslint-disable-line react-hooks/exhaustive-deps

  const isRecording = status === "recording";
  const isBusy = status === "processing" || status === "thinking" || status === "transcribing" || status === "speaking";

  const labels: Record<PttStatus, string> = {
    idle: "Hold Space to talk",
    recording: "Listening — release to send",
    processing: "Processing…",
    transcribing: "Transcribing…",
    thinking: "Thinking…",
    speaking: "Speaking…",
    error: errorMsg || "Error",
  };

  // Visualizer bars from audio level.
  const bars = 7;
  const barHeights = Array.from({ length: bars }, (_, i) => {
    const center = Math.abs(i - 3) / 3;
    return Math.max(4, recorder.audioLevel * (1 - center * 0.5) * 48);
  });

  return (
    <div
      ref={panelRef}
      tabIndex={-1}
      className="flex flex-col items-center justify-center py-8 px-6 relative outline-none"
    >
      <button
        onClick={onExit}
        className="absolute top-4 right-4 p-2 rounded-[3px] text-ink-muted hover:text-ink hover:bg-bg-sunk transition-colors z-10"
        aria-label="Close push-to-talk"
      >
        <X size={18} />
      </button>

      <div className="relative mb-6">
        <AnimatePresence>
          {isRecording && (
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
          onMouseDown={() => {
            if (isBusy) return;
            mouseHoldingRef.current = true;
            void recorder.start();
          }}
          onMouseUp={() => {
            if (!mouseHoldingRef.current) return;
            mouseHoldingRef.current = false;
            recorder.stop();
          }}
          onMouseLeave={() => {
            // Only stop on mouseLeave if the mouse was the input source.
            // If the user is holding Spacebar, mouseLeave must NOT cancel
            // the recording.
            if (!mouseHoldingRef.current) return;
            mouseHoldingRef.current = false;
            recorder.stop();
          }}
          onTouchStart={(e) => {
            e.preventDefault();
            if (isBusy) return;
            mouseHoldingRef.current = true;
            void recorder.start();
          }}
          onTouchEnd={(e) => {
            e.preventDefault();
            if (!mouseHoldingRef.current) return;
            mouseHoldingRef.current = false;
            recorder.stop();
          }}
          className={`relative w-24 h-24 rounded-full flex items-center justify-center transition-all duration-200 select-none ${
            isRecording
              ? "bg-brand text-white"
              : status === "speaking"
              ? "bg-brand/80 text-white"
              : status === "error"
              ? "bg-mch-soft text-mch"
              : "bg-bg-sunk text-ink-muted"
          }`}
          aria-label="Hold to record"
          aria-keyshortcuts="Space"
        >
          <Mic size={32} />
        </button>
      </div>

      {/* Audio-level visualizer */}
      <div className="flex items-end gap-1 h-12 mb-4" aria-hidden>
        {barHeights.map((h, i) => (
          <motion.div
            key={i}
            animate={{ height: isRecording ? h : 4 }}
            transition={{ duration: 0.1 }}
            className="w-1 rounded-full bg-brand/70"
          />
        ))}
      </div>

      <div
        role="status"
        aria-live="polite"
        className="font-mono text-[11px] uppercase tracking-[0.04em] text-ink-muted"
      >
        {labels[status]}
      </div>
      <div className="mt-2 font-mono text-[10px] text-ink-subtle">
        Esc to close · works with foot pedals mapped to Space
      </div>
      <MicPermission />
      <VoiceSseClient
        turnId={turnId}
        onStatus={(next) => {
          if (next === "processing") setStatus("processing");
          if (next === "speaking") setStatus("speaking");
          if (next === "error") setStatus("error");
        }}
        onDone={() => {
          if (activeRef.current) setStatus("idle");
        }}
      />
    </div>
  );
}
