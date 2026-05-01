"use client";

import { useState, useRef, useCallback, useEffect } from "react";

export type RecorderState = "idle" | "listening" | "silence_detected" | "stopped";

const SILENCE_THRESHOLD = 15; // 0-255 scale
const SILENCE_DURATION_MS = 1500;

interface UseAudioRecorderReturn {
  state: RecorderState;
  audioLevel: number;
  silenceCountdown: number;
  audioBlob: Blob | null;
  error: string | null;
  start: () => Promise<void>;
  stop: () => void;
  reset: () => void;
}

export function useAudioRecorder(): UseAudioRecorderReturn {
  const [state, setState] = useState<RecorderState>("idle");
  const [audioLevel, setAudioLevel] = useState(0);
  const [silenceCountdown, setSilenceCountdown] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animFrameRef = useRef<number>(0);
  const chunksRef = useRef<Blob[]>([]);
  const silenceStartRef = useRef<number>(0);
  const hasSpeechRef = useRef(false);

  const cleanup = useCallback(() => {
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    mediaRecorderRef.current?.stop();
    streamRef.current?.getTracks().forEach((t) => t.stop());
    audioContextRef.current?.close();
    mediaRecorderRef.current = null;
    audioContextRef.current = null;
    analyserRef.current = null;
    streamRef.current = null;
  }, []);

  useEffect(() => () => cleanup(), [cleanup]);

  const start = useCallback(async () => {
    setError(null);
    setAudioBlob(null);
    chunksRef.current = [];
    hasSpeechRef.current = false;
    setSilenceCountdown(0);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const ctx = new AudioContext();
      audioContextRef.current = ctx;
      const source = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 2048;
      analyser.smoothingTimeConstant = 0.8;
      source.connect(analyser);
      analyserRef.current = analyser;

      const recorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
          ? "audio/webm;codecs=opus"
          : "audio/webm",
      });
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        if (hasSpeechRef.current && blob.size > 0) {
          setAudioBlob(blob);
          setState("stopped");
        } else {
          setState("idle");
        }
      };

      recorder.start(100); // collect chunks every 100ms
      silenceStartRef.current = 0;
      setState("listening");

      // VAD loop
      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const poll = () => {
        if (!analyserRef.current) return;
        analyserRef.current.getByteFrequencyData(dataArray);

        // RMS energy
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) sum += dataArray[i] * dataArray[i];
        const rms = Math.sqrt(sum / dataArray.length);
        setAudioLevel(Math.min(rms / 128, 1)); // normalize to 0-1

        const now = Date.now();

        if (rms > SILENCE_THRESHOLD) {
          // Speech detected
          hasSpeechRef.current = true;
          silenceStartRef.current = 0;
          setSilenceCountdown(0);
          setState("listening");
        } else if (hasSpeechRef.current) {
          // Silence after speech
          if (silenceStartRef.current === 0) {
            silenceStartRef.current = now;
          }
          const elapsed = now - silenceStartRef.current;
          setSilenceCountdown(Math.max(0, SILENCE_DURATION_MS - elapsed));

          if (elapsed > 200) {
            setState("silence_detected");
          }

          if (elapsed >= SILENCE_DURATION_MS) {
            // Speech finished — stop recording
            recorder.stop();
            cleanup();
            return; // exit loop
          }
        }

        animFrameRef.current = requestAnimationFrame(poll);
      };
      animFrameRef.current = requestAnimationFrame(poll);
    } catch (err: unknown) {
      const e = err as { name?: string; message?: string };
      if (e.name === "NotAllowedError") {
        setError("Microphone permission denied. Please allow microphone access.");
      } else if (e.name === "NotFoundError") {
        setError("No microphone found.");
      } else {
        setError(e.message || "Could not access microphone.");
      }
      setState("idle");
    }
  }, [cleanup]);

  const stop = useCallback(() => {
    // Manual stop
    hasSpeechRef.current = true; // force accept even short recordings
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
    }
    cleanup();
  }, [cleanup]);

  const reset = useCallback(() => {
    cleanup();
    setState("idle");
    setAudioBlob(null);
    setAudioLevel(0);
    setSilenceCountdown(0);
    setError(null);
  }, [cleanup]);

  return { state, audioLevel, silenceCountdown, audioBlob, error, start, stop, reset };
}
