"use client";

import { useState, useRef, useCallback } from "react";

export type PlayerState = "idle" | "loading" | "playing";

interface UseAudioPlayerReturn {
  state: PlayerState;
  play: (url: string) => Promise<void>;
  stop: () => void;
}

export function useAudioPlayer(): UseAudioPlayerReturn {
  const [state, setState] = useState<PlayerState>("idle");
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const play = useCallback((url: string): Promise<void> => {
    return new Promise((resolve, reject) => {
      // Stop any current playback
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.removeAttribute("src");
        audioRef.current = null;
      }

      setState("loading");

      const audio = new Audio();
      audio.crossOrigin = "anonymous"; // needed for CORS audio from different port
      audioRef.current = audio;

      let resolved = false;
      const finish = () => {
        if (resolved) return;
        resolved = true;
        setState("idle");
        audioRef.current = null;
      };

      audio.addEventListener("canplaythrough", () => {
        setState("playing");
        audio.play().then(() => {
          // playing successfully
        }).catch((err) => {
          console.warn("Audio play() rejected:", err);
          // Autoplay blocked — try to continue anyway
          finish();
          resolve();
        });
      }, { once: true });

      audio.addEventListener("ended", () => {
        finish();
        resolve();
      }, { once: true });

      audio.addEventListener("error", (e) => {
        console.warn("Audio load error:", e);
        finish();
        // Resolve instead of reject so the voice loop continues
        resolve();
      }, { once: true });

      // Timeout fallback — if audio doesn't load in 10 seconds, move on
      const timeout = setTimeout(() => {
        if (!resolved) {
          console.warn("Audio playback timed out");
          audio.pause();
          finish();
          resolve();
        }
      }, 10000);

      audio.addEventListener("ended", () => clearTimeout(timeout), { once: true });
      audio.addEventListener("error", () => clearTimeout(timeout), { once: true });

      audio.src = url;
      audio.load();
    });
  }, []);

  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.removeAttribute("src");
      audioRef.current = null;
    }
    setState("idle");
  }, []);

  return { state, play, stop };
}
