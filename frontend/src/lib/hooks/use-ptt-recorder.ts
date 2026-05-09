"use client";

/**
 * Push-to-talk recorder.
 *
 * Records audio only while `start()` is in effect — stops on `stop()`.
 * No VAD, no silence detection. Caller (typically a keyboard- or
 * button-hold handler) decides when to begin and end. This is the
 * bench-friendly alternative to use-audio-recorder.ts (VAD-based).
 *
 * Hands-free wake-word triggering is intentionally not in this hook;
 * that lives in a future PR using openWakeWord (Apache-2.0).
 */

import { useCallback, useEffect, useRef, useState } from "react";

export type PttState = "idle" | "recording" | "stopped";

interface UsePttRecorderReturn {
  state: PttState;
  audioLevel: number; // 0..1, drives the visualizer
  audioBlob: Blob | null;
  error: string | null;
  start: () => Promise<void>;
  stop: () => void;
  reset: () => void;
}

// Anything shorter than ~200ms is almost always a stray Space press
// (key bounce, accidental tap on the mic button) — we discard it
// rather than ship a 100ms blob to Whisper.
const MIN_RECORDING_MS = 250;

// Negotiate the MediaRecorder mimeType. Safari (iPad bench tablets) does
// not support audio/webm reliably; pick the first supported type and
// fall back to the platform default.
function pickMimeType(): string | undefined {
  if (typeof MediaRecorder === "undefined") return undefined;
  const candidates = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/mp4;codecs=mp4a.40.2",
    "audio/mp4",
  ];
  for (const c of candidates) {
    if (MediaRecorder.isTypeSupported(c)) return c;
  }
  return undefined;
}

export function usePttRecorder(): UsePttRecorderReturn {
  const [state, setState] = useState<PttState>("idle");
  const [audioLevel, setAudioLevel] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animFrameRef = useRef<number>(0);
  const chunksRef = useRef<Blob[]>([]);
  const recordingStartedAtRef = useRef<number>(0);
  // Set true if stop() arrives while start() is mid-await. start()
  // checks this after setup completes and immediately tears down so
  // a quick tap (Space-down/Space-up before getUserMedia resolves)
  // doesn't strand a recorder in the "recording" state.
  const pendingStopRef = useRef<boolean>(false);

  const cleanup = useCallback(() => {
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      try { mediaRecorderRef.current.stop(); } catch { /* ignore */ }
    }
    try { sourceRef.current?.disconnect(); } catch { /* ignore */ }
    streamRef.current?.getTracks().forEach((t) => t.stop());
    audioContextRef.current?.close().catch(() => { /* ignore */ });
    mediaRecorderRef.current = null;
    audioContextRef.current = null;
    analyserRef.current = null;
    sourceRef.current = null;
    streamRef.current = null;
  }, []);

  // Cleanup on unmount.
  useEffect(() => () => cleanup(), [cleanup]);

  const start = useCallback(async () => {
    setError(null);
    setAudioBlob(null);
    chunksRef.current = [];
    pendingStopRef.current = false;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const Ctor = window.AudioContext ||
        (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const audioContext = new Ctor();
      audioContextRef.current = audioContext;
      // Some browsers create the AudioContext suspended when not
      // started by a user gesture; getUserMedia usually launders the
      // gesture, but this is a defensive nudge for Safari quirks.
      if (audioContext.state === "suspended") {
        await audioContext.resume().catch(() => { /* ignore */ });
      }

      const source = audioContext.createMediaStreamSource(stream);
      sourceRef.current = source;
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;

      const mimeType = pickMimeType();
      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        // Use the recorder's actual mimeType, not a hardcoded one — Safari
        // produces audio/mp4, others produce audio/webm.
        const blob = new Blob(chunksRef.current, {
          type: recorder.mimeType || "audio/webm",
        });
        setAudioBlob(blob);
        setState("stopped");
        try { sourceRef.current?.disconnect(); } catch { /* ignore */ }
        streamRef.current?.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
        if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      };

      recordingStartedAtRef.current = Date.now();
      recorder.start();
      setState("recording");

      // If stop() arrived while we were awaiting getUserMedia, honor it
      // now: tear down without producing a blob (the user clearly
      // didn't want this recording). Clear onstop first so the discard
      // path doesn't emit an empty Blob and falsely look like a real
      // recording downstream.
      if (pendingStopRef.current) {
        pendingStopRef.current = false;
        recorder.onstop = null;
        try { recorder.stop(); } catch { /* ignore */ }
        chunksRef.current = [];
        try { sourceRef.current?.disconnect(); } catch { /* ignore */ }
        streamRef.current?.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
        setState("idle");
        return;
      }

      // Audio-level animation for the visualizer.
      const buffer = new Uint8Array(analyser.frequencyBinCount);
      const tick = () => {
        if (!analyserRef.current) return;
        analyserRef.current.getByteFrequencyData(buffer);
        const sum = buffer.reduce((a, b) => a + b, 0);
        const avg = sum / buffer.length;
        setAudioLevel(Math.min(1, avg / 96));
        animFrameRef.current = requestAnimationFrame(tick);
      };
      animFrameRef.current = requestAnimationFrame(tick);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "microphone unavailable";
      setError(msg);
      setState("idle");
    }
  }, []);

  const stop = useCallback(() => {
    const recorder = mediaRecorderRef.current;
    if (!recorder) {
      // start() is mid-await; mark a pending stop so it tears down
      // immediately when setup completes.
      pendingStopRef.current = true;
      return;
    }
    if (recorder.state === "inactive") return;
    const elapsed = Date.now() - recordingStartedAtRef.current;
    if (elapsed < MIN_RECORDING_MS) {
      // Discard: clear onstop so it can't fire later with an empty
      // Blob and confuse downstream consumers.
      recorder.onstop = null;
      try { recorder.stop(); } catch { /* ignore */ }
      chunksRef.current = [];
      try { sourceRef.current?.disconnect(); } catch { /* ignore */ }
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      setState("idle");
      return;
    }
    try { recorder.stop(); } catch { /* ignore */ }
  }, []);

  const reset = useCallback(() => {
    setAudioBlob(null);
    setAudioLevel(0);
    setState("idle");
    chunksRef.current = [];
  }, []);

  return { state, audioLevel, audioBlob, error, start, stop, reset };
}
