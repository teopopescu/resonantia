# Voice Mode — Implementation Plan

## How OpenAI and Anthropic Do It

### OpenAI: Two Architectures

OpenAI's docs (developers.openai.com/api/docs/guides/voice-agents) explicitly describe **two approaches**:

| Architecture | How It Works | Best For |
|---|---|---|
| **Speech-to-speech (Realtime API)** | A single model (`gpt-realtime-1.5`) handles live audio input AND output directly. Uses WebRTC in browser or WebSocket on server. The model natively processes audio — no separate STT/TTS steps. Server-side VAD handles turn detection. | Natural, low-latency conversations. ~300ms response time. |
| **Chained voice pipeline** | App explicitly chains: STT (Whisper) → text agent (GPT-4o) → TTS. Each step is a separate API call. App controls the flow. | Predictable workflows, durable transcripts, extending existing text agents, deterministic logic between stages. |

OpenAI's guidance: *"The chained path is often the better fit for support flows, approval-heavy flows, or cases where you want durable transcripts and deterministic logic between each stage."*

### Anthropic: No Native Voice

Anthropic does not have a Realtime speech API. Claude is text/image only. Voice implementations with Claude use the chained approach (Whisper → Claude → external TTS).

### What's Right for Resonantia

**The chained pipeline is the correct choice.** Here's why:

1. **We need tool execution between STT and TTS.** Our chat runs an agentic loop with up to 5 rounds of tool calls (querying Postgres, running dose-response fitting, checking inventory). The Realtime API's speech-to-speech model can call tools, but our 32 custom tools with database queries are complex — the chained approach gives us full control.

2. **We need durable transcripts.** Every voice interaction appears as text in the chat thread. Scientists need a record of what they asked and what the system did.

3. **We already have the text agent built.** 32 tools, guardrails, Langfuse tracing, Temporal workflows — all text-based. The chained approach reuses 100% of this.

4. **We use OpenAI for the LLM but could switch.** The chained approach is model-agnostic — we can swap GPT-4o for Claude or a local model without changing the voice layer.

5. **Latency is acceptable.** ~2.5-5.5 seconds per turn for a lab assistant is fine. This isn't a real-time conversation — it's a scientist giving a command and waiting for a result.

### How Our Plan Differs from OpenAI's Realtime API

| Aspect | OpenAI Realtime | Our Plan |
|---|---|---|
| Model | `gpt-realtime-1.5` (native audio) | Whisper + GPT-4o + TTS-1 (chained) |
| Connection | WebRTC/WebSocket persistent stream | HTTP POST per turn |
| VAD | Server-side (`semantic_vad`) | Client-side (energy-based + manual) |
| Latency | ~300ms first token | ~2.5-5.5s full response |
| Tool execution | Inside the realtime session | Between STT and TTS, full agentic loop |
| Transcript | Requires separate transcription call | Built-in (STT output IS the transcript) |
| Cost | $0.06/min audio input + output | Whisper ($0.006/min) + GPT-4o tokens + TTS ($0.015/1K chars) |
| Flexibility | Tied to OpenAI realtime model | Model-agnostic, works with any LLM |

**Cost comparison for a 1-minute voice turn:**
- OpenAI Realtime: ~$0.12 (audio in + out)
- Our chained approach: ~$0.03-0.05 (Whisper + GPT-4o tokens + TTS)

---

## Architecture

```
Voice Mode ON → Loop:

  [Browser] Web Audio API + MediaRecorder
     │── AnalyserNode monitors volume → drives waveform UI
     │── VAD: 1.5s silence below threshold → stop recording
     │── MediaRecorder outputs audio/webm blob
     ▼
  [Backend] POST /api/v1/voice/chat (single endpoint)
     │── Whisper STT → transcribed text        (~500-1000ms)
     │── agent.chat(text) → agentic tool loop  (~1000-3000ms)
     │── OpenAI TTS → mp3 audio response       (~500-1000ms)
     │── Return { transcription, response, audio_url }
     ▼
  [Browser] Display + Playback
     │── User message (transcription) appears in chat
     │── Assistant message (response) appears in chat
     │── TTS audio plays via <audio> element
     │── When playback finishes → auto-resume listening
     └── Loop continues
```

## VAD: Energy-Based with Manual Fallback

- Web Audio API `AnalyserNode` polls audio levels via `requestAnimationFrame`
- RMS energy below threshold (15 on 0-255 scale) for 1.5s → speech finished
- User can tap mic to manually stop (push-to-talk fallback)
- Visual countdown ring during silence detection
- Minimum 500ms speech required (ignore accidental clicks)

## Backend: POST /api/v1/voice/chat

Single endpoint orchestrating STT → agent → TTS:
1. Save audio to temp file
2. `openai.audio.transcriptions.create(model="whisper-1")` → text
3. `agent.chat(text)` → full agentic loop (32 tools, guardrails, Langfuse)
4. `openai.audio.speech.create(model="tts-1", voice="nova")` → mp3
5. Return `{ transcription, response, audio_url, conversation_id, tool_calls }`

Config: `tts_voice=nova`, `tts_model=tts-1`, `stt_model=whisper-1`

## Frontend: VoiceMode Component

States: Listening (pulsing amber) → Silence detected (countdown) → Transcribing → Thinking → Speaking

Three new files:
- `use-audio-recorder.ts` — Web Audio capture + VAD
- `use-audio-player.ts` — TTS playback (promise-based for auto-listen loop)
- `voice-mode.tsx` — UI overlay with waveform visualization

## Files to create
- `backend/src/resonantia/api/voice.py`
- `frontend/src/lib/hooks/use-audio-recorder.ts`
- `frontend/src/lib/hooks/use-audio-player.ts`
- `frontend/src/components/lab/voice-mode.tsx`

## Files to modify
- `backend/src/resonantia/config.py` — add tts_voice, tts_model, stt_model
- `backend/src/resonantia/api/router.py` — register voice router
- `frontend/src/components/lab/chat-interface.tsx` — add mic button, conditional VoiceMode render
- `frontend/src/stores/lab-store.ts` — add voiceModeActive state

## Verification
1. Backend: `curl -X POST /api/v1/voice/chat -F "audio=@test.webm"` → transcription + response + audio
2. Click mic → speak → waveform → silence → transcription → response plays
3. After playback → auto-resumes listening (loop)
4. Tap mic → manual stop & send
5. X button or Escape → exits voice mode
6. Tool use via voice: "What plates do we have?" → agent queries DB → speaks answer
