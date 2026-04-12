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
        audioRef.current = null;
      }

      setState("loading");
      const audio = new Audio(url);
      audioRef.current = audio;

      audio.oncanplaythrough = () => {
        setState("playing");
        audio.play().catch(reject);
      };

      audio.onended = () => {
        setState("idle");
        audioRef.current = null;
        resolve();
      };

      audio.onerror = () => {
        setState("idle");
        audioRef.current = null;
        reject(new Error("Audio playback failed"));
      };

      audio.load();
    });
  }, []);

  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    setState("idle");
  }, []);

  return { state, play, stop };
}
