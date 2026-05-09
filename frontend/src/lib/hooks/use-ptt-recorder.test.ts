/**
 * Tests for the push-to-talk recorder hook.
 *
 * jsdom doesn't have MediaRecorder or AudioContext, so we mock both.
 * The interesting case is the start-before-stop race that was flagged
 * during adversarial review: the user can press-and-release Space
 * faster than getUserMedia resolves, and the hook must not strand a
 * recorder in the "recording" state.
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { act, renderHook, waitFor } from "@testing-library/react";

import { usePttRecorder } from "./use-ptt-recorder";

class FakeMediaRecorder {
  static isTypeSupported = vi.fn(() => true);
  state: "inactive" | "recording" = "inactive";
  ondataavailable: ((e: { data: Blob }) => void) | null = null;
  onstop: (() => void) | null = null;
  mimeType: string;
  constructor(_stream: MediaStream, opts?: { mimeType?: string }) {
    this.mimeType = opts?.mimeType ?? "audio/webm";
  }
  start() { this.state = "recording"; }
  stop() {
    if (this.state === "inactive") return;
    this.state = "inactive";
    this.onstop?.();
  }
}

class FakeAudioContext {
  state: "running" | "suspended" = "running";
  resume = vi.fn(async () => { this.state = "running"; });
  close = vi.fn(async () => undefined);
  createMediaStreamSource() {
    return { connect: vi.fn(), disconnect: vi.fn() };
  }
  createAnalyser() {
    return {
      fftSize: 256,
      frequencyBinCount: 128,
      getByteFrequencyData: (_: Uint8Array) => undefined,
    };
  }
}

function fakeStream(): MediaStream {
  return {
    getTracks: () => [{ stop: vi.fn() }],
  } as unknown as MediaStream;
}

describe("usePttRecorder", () => {
  beforeEach(() => {
    vi.useRealTimers();
    (globalThis as unknown as { MediaRecorder: unknown }).MediaRecorder = FakeMediaRecorder;
    (globalThis as unknown as { AudioContext: unknown }).AudioContext = FakeAudioContext;
    Object.defineProperty(window, "AudioContext", { value: FakeAudioContext, configurable: true });
  });

  it("starts as idle with no audioBlob", () => {
    const { result } = renderHook(() => usePttRecorder());
    expect(result.current.state).toBe("idle");
    expect(result.current.audioBlob).toBeNull();
  });

  it("transitions to recording then stopped on a normal hold", async () => {
    Object.defineProperty(navigator, "mediaDevices", {
      value: { getUserMedia: async () => fakeStream() },
      configurable: true,
    });

    const { result } = renderHook(() => usePttRecorder());

    await act(async () => { await result.current.start(); });
    expect(result.current.state).toBe("recording");

    // Wait long enough that MIN_RECORDING_MS doesn't discard the blob.
    await new Promise((resolve) => setTimeout(resolve, 300));

    act(() => { result.current.stop(); });

    await waitFor(() => expect(result.current.state).toBe("stopped"));
    expect(result.current.audioBlob).not.toBeNull();
  });

  it("does NOT strand the recorder when stop() arrives before start() resolves", async () => {
    // The BLOCKER from the adversarial review: tap Space-down/Space-up
    // faster than getUserMedia resolves. start() should honor the
    // pending stop and tear down to idle, not get stuck in "recording".
    let resolveStream: (s: MediaStream) => void = () => undefined;
    const slowGetUserMedia = vi.fn(() => new Promise<MediaStream>((resolve) => {
      resolveStream = resolve;
    }));
    Object.defineProperty(navigator, "mediaDevices", {
      value: { getUserMedia: slowGetUserMedia },
      configurable: true,
    });

    const { result } = renderHook(() => usePttRecorder());

    // Fire start() but don't await yet — the await is parked in
    // getUserMedia until we resolve it below.
    let startPromise!: Promise<void>;
    act(() => { startPromise = result.current.start(); });

    // The user releases Space before getUserMedia resolves.
    act(() => { result.current.stop(); });

    // Now resolve getUserMedia — start() should detect the pending
    // stop and tear down to idle.
    await act(async () => {
      resolveStream(fakeStream());
      await startPromise;
    });

    expect(result.current.state).toBe("idle");
    expect(result.current.audioBlob).toBeNull();
  });

  it("discards recordings shorter than MIN_RECORDING_MS", async () => {
    Object.defineProperty(navigator, "mediaDevices", {
      value: { getUserMedia: async () => fakeStream() },
      configurable: true,
    });

    const { result } = renderHook(() => usePttRecorder());

    await act(async () => { await result.current.start(); });
    expect(result.current.state).toBe("recording");

    // Stop immediately — under MIN_RECORDING_MS.
    act(() => { result.current.stop(); });

    expect(result.current.state).toBe("idle");
    expect(result.current.audioBlob).toBeNull();
  });

  it("surfaces getUserMedia errors", async () => {
    Object.defineProperty(navigator, "mediaDevices", {
      value: {
        getUserMedia: async () => {
          throw new Error("Permission denied");
        },
      },
      configurable: true,
    });

    const { result } = renderHook(() => usePttRecorder());
    await act(async () => { await result.current.start(); });
    expect(result.current.state).toBe("idle");
    expect(result.current.error).toContain("Permission denied");
  });
});
