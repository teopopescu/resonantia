"use client";

import { useEffect, useRef, useState } from "react";
import { CheckCircle2, Loader2, Radio, Volume2 } from "lucide-react";
import { API_URL, getActiveOrgId } from "@/lib/api";
import { useAudioPlayer } from "@/lib/hooks/use-audio-player";
import { useLabStore } from "@/stores/lab-store";
import { ApprovalCard } from "./approval-card";

type VoiceStreamStatus = "processing" | "speaking" | "done" | "error";

interface VoiceSseClientProps {
  turnId: string | null;
  onStatus?: (status: VoiceStreamStatus) => void;
  onDone?: () => void;
}

interface ApprovalPayload {
  token: string;
  tool_name: string;
  gate_kind: "soft_review" | "hard_approval";
  preview: Record<string, unknown>;
}

function parseSseFrames(buffer: string) {
  const frames = buffer.split("\n\n");
  const rest = frames.pop() ?? "";
  return {
    rest,
    events: frames.map((frame) => {
      let event = "message";
      const data: string[] = [];
      for (const line of frame.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        if (line.startsWith("data:")) data.push(line.slice(5).trim());
      }
      return { event, data: data.join("\n") };
    }),
  };
}

function approvalFromPayload(payload: unknown): ApprovalPayload | null {
  if (!payload || typeof payload !== "object") return null;
  const toolCall = (payload as { tool_call?: unknown }).tool_call;
  if (!toolCall || typeof toolCall !== "object") return null;
  let result = (toolCall as { result?: unknown }).result;
  if (typeof result === "string") {
    try {
      result = JSON.parse(result);
    } catch {
      return null;
    }
  }
  if (!result || typeof result !== "object") return null;
  const card = (result as { approval_card?: ApprovalPayload }).approval_card;
  if (!card) return null;
  return card;
}

export function VoiceSseClient({ turnId, onStatus, onDone }: VoiceSseClientProps) {
  const { addMessage } = useLabStore();
  const player = useAudioPlayer();
  const [transcript, setTranscript] = useState("");
  const [response, setResponse] = useState("");
  const [progress, setProgress] = useState<string[]>([]);
  const [approval, setApproval] = useState<ApprovalPayload | null>(null);
  const [confidence, setConfidence] = useState<number | null>(null);
  const seenRef = useRef({ transcript: false, response: false });

  useEffect(() => {
    if (!turnId) return;

    const abort = new AbortController();
    seenRef.current = { transcript: false, response: false };
    setTranscript("");
    setResponse("");
    setProgress([]);
    setApproval(null);
    setConfidence(null);
    onStatus?.("processing");

    async function connect() {
      try {
        const res = await fetch(`${API_URL}/api/v1/voice/turns/${turnId}/events`, {
          headers: { "X-Org-Id": getActiveOrgId() },
          signal: abort.signal,
        });
        if (!res.ok || !res.body) throw new Error("Voice event stream failed");

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const parsed = parseSseFrames(buffer);
          buffer = parsed.rest;

          for (const item of parsed.events) {
            const payload = item.data ? JSON.parse(item.data) : {};
            if (item.event === "transcript") {
              const text = String(payload.text || "");
              setTranscript(text);
              setConfidence(typeof payload.confidence === "number" ? payload.confidence : 1);
              if (!seenRef.current.transcript && text) {
                seenRef.current.transcript = true;
                addMessage("user", text);
              }
            }
            if (item.event === "tool_call") {
              const name = payload.tool_call?.name || "tool";
              setProgress((current) => [...current, `${name} running`]);
            }
            if (item.event === "tool_result") {
              setProgress((current) => [...current, "tool result ready"]);
            }
            if (item.event === "approval_required") {
              const card = approvalFromPayload(payload);
              if (card) setApproval(card);
            }
            if (item.event === "response") {
              const text = String(payload.text || "");
              setResponse(text);
              if (!seenRef.current.response && text) {
                seenRef.current.response = true;
                addMessage("assistant", text);
              }
            }
            if (item.event === "audio_ready" && payload.audio_url) {
              onStatus?.("speaking");
              await player.play(`${API_URL}${payload.audio_url}`);
            }
            if (item.event === "done") {
              onStatus?.("done");
              onDone?.();
              return;
            }
          }
        }
      } catch (err) {
        if (!abort.signal.aborted) {
          const message = err instanceof Error ? err.message : "Voice stream failed";
          setProgress((current) => [...current, message]);
          addMessage("assistant", `Voice error: ${message}`);
          onStatus?.("error");
        }
      }
    }

    void connect();
    return () => abort.abort();
  }, [turnId]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!turnId) return null;

  return (
    <div className="mt-4 w-full max-w-sm space-y-3 text-left">
      {transcript && (
        <div
          className="rounded border border-line bg-bg-sunk px-3 py-2 text-sm text-ink"
          style={{ opacity: confidence ?? 1 }}
        >
          {transcript}
        </div>
      )}
      {progress.length > 0 && (
        <div className="space-y-1 text-xs text-ink-muted">
          {progress.slice(-3).map((item, index) => (
            <div key={`${item}-${index}`} className="flex items-center gap-2">
              <Radio size={12} />
              <span>{item}</span>
            </div>
          ))}
        </div>
      )}
      {approval && (
        <ApprovalCard
          token={approval.token}
          toolName={approval.tool_name}
          gateKind={approval.gate_kind}
          preview={approval.preview}
        />
      )}
      {response && (
        <div className="rounded border border-brand/20 bg-brand-soft/20 px-3 py-2 text-sm text-ink">
          {player.state === "playing" ? (
            <Volume2 size={13} className="mr-2 inline text-brand" />
          ) : (
            <CheckCircle2 size={13} className="mr-2 inline text-brand" />
          )}
          {response}
        </div>
      )}
      {!response && !approval && (
        <div className="flex items-center gap-2 text-xs text-ink-muted">
          <Loader2 size={13} className="animate-spin" />
          processing
        </div>
      )}
    </div>
  );
}
