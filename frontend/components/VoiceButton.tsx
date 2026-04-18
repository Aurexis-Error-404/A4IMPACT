"use client";

import { useState, useRef, useEffect } from "react";

const CHAT_URL = "http://localhost:8000/voice/chat";
const MAX_RECORD_SECONDS = 60;

type Role = "user" | "assistant";

interface Message {
  role: Role;
  content: string;        // displayed text (transcript or Telugu reply)
  audio_base64?: string | null;
}

type RecState = "idle" | "recording" | "processing";

function pickMimeType(): string {
  const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg"];
  return candidates.find((t) => MediaRecorder.isTypeSupported(t)) ?? "";
}

export default function VoiceButton() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [recState, setRecState] = useState<RecState>("idle");
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, recState]);

  useEffect(() => {
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, []);

  function stopCurrentAudio() {
    if (audioRef.current) { audioRef.current.pause(); audioRef.current.currentTime = 0; }
  }

  function playAudio(base64: string) {
    stopCurrentAudio();
    const audio = new Audio("data:audio/mp3;base64," + base64);
    audioRef.current = audio;
    audio.play().catch(() => {});
  }

  async function startRecording() {
    setError(null);
    stopCurrentAudio();

    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setError("Microphone access denied.");
      return;
    }

    chunksRef.current = [];
    const mimeType = pickMimeType();
    const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
    mediaRecorderRef.current = recorder;

    recorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };

    recorder.onstop = async () => {
      if (timerRef.current) clearInterval(timerRef.current);
      stream.getTracks().forEach((t) => t.stop());

      const blob = new Blob(chunksRef.current, { type: mimeType || "audio/webm" });
      const ext = mimeType.includes("mp4") ? "mp4" : mimeType.includes("ogg") ? "ogg" : "webm";
      const formData = new FormData();
      formData.append("audio", blob, `recording.${ext}`);

      // Send conversation history (role + content only, no audio_base64)
      const historyForApi = messages.map(({ role, content }) => ({ role, content }));
      formData.append("history", JSON.stringify(historyForApi));

      setRecState("processing");
      try {
        const res = await fetch(CHAT_URL, { method: "POST", body: formData });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        const userMsg: Message = { role: "user", content: data.transcript || "…" };
        const assistantMsg: Message = {
          role: "assistant",
          content: data.reply_te,
          audio_base64: data.audio_base64,
        };

        setMessages((prev) => [...prev, userMsg, assistantMsg]);
        if (data.audio_base64) playAudio(data.audio_base64);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Request failed.");
      } finally {
        setRecState("idle");
        setElapsed(0);
      }
    };

    setElapsed(0);
    timerRef.current = setInterval(() => {
      setElapsed((s) => {
        if (s + 1 >= MAX_RECORD_SECONDS) { recorder.stop(); return MAX_RECORD_SECONDS; }
        return s + 1;
      });
    }, 1000);

    recorder.start();
    setRecState("recording");
  }

  function stopRecording() {
    if (timerRef.current) clearInterval(timerRef.current);
    mediaRecorderRef.current?.stop();
  }

  function replayMessage(msg: Message) {
    if (msg.audio_base64) playAudio(msg.audio_base64);
  }

  function clearConversation() {
    stopCurrentAudio();
    setMessages([]);
    setError(null);
    setRecState("idle");
  }

  const remaining = MAX_RECORD_SECONDS - elapsed;

  return (
    <div style={s.card}>
      {/* Header */}
      <div style={s.header}>
        <span style={s.label}>తెలుగు సంభాషణ · Voice Chat</span>
        {messages.length > 0 && (
          <button style={s.clearBtn} onClick={clearConversation}>కొత్త సంభాషణ ×</button>
        )}
      </div>

      {/* Conversation thread */}
      <div style={s.thread}>
        {messages.length === 0 && recState === "idle" && (
          <p style={s.emptyHint}>
            🎙 మైక్ నొక్కి మాట్లాడండి — పత్తి, వరి, వేరుశనగ… ఏ పంట గురించైనా అడగండి.
          </p>
        )}

        {messages.map((msg, i) => (
          <div key={i} style={msg.role === "user" ? s.bubbleUser : s.bubbleAssistant}>
            <span style={s.roleTag}>{msg.role === "user" ? "మీరు" : "KrishiCFO"}</span>
            <p style={s.bubbleText}>{msg.content}</p>
            {msg.role === "assistant" && msg.audio_base64 && (
              <button style={s.replayBtn} onClick={() => replayMessage(msg)}>▶</button>
            )}
          </div>
        ))}

        {recState === "processing" && (
          <div style={{ ...s.bubbleAssistant, opacity: 0.5 }}>
            <span style={s.roleTag}>KrishiCFO</span>
            <Dots />
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Error */}
      {error && <p style={s.errorText}>{error}</p>}

      {/* Mic controls */}
      <div style={s.controls}>
        {recState === "idle" && (
          <button style={s.micBtn} onClick={startRecording} title="మాట్లాడండి">
            <MicIcon />
            <span style={s.micLabel}>మాట్లాడండి</span>
          </button>
        )}

        {recState === "recording" && (
          <button style={{ ...s.micBtn, ...s.micRecording }} onClick={stopRecording}>
            <span style={s.pulse} />
            <span style={s.micLabel}>
              వింటున్నాను… {remaining < 15 ? `(${remaining}s)` : ""}
            </span>
          </button>
        )}

        {recState === "processing" && (
          <button style={{ ...s.micBtn, ...s.micDisabled }} disabled>
            <Spinner />
            <span style={s.micLabel}>ఆలోచిస్తున్నాను…</span>
          </button>
        )}
      </div>
    </div>
  );
}

function MicIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="9" y="2" width="6" height="12" rx="3" />
      <path d="M5 10a7 7 0 0 0 14 0" />
      <line x1="12" y1="19" x2="12" y2="22" />
      <line x1="9" y1="22" x2="15" y2="22" />
    </svg>
  );
}

function Spinner() {
  return <span style={s.spinner} />;
}

function Dots() {
  return <span style={s.bubbleText}>· · ·</span>;
}

const s: Record<string, React.CSSProperties> = {
  card: {
    background: "rgba(255,255,255,0.04)",
    border: "1px solid rgba(255,255,255,0.08)",
    borderRadius: 14,
    display: "flex",
    flexDirection: "column",
    gap: 0,
    fontFamily: "'Lora', Georgia, serif",
    overflow: "hidden",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "14px 20px 10px",
    borderBottom: "1px solid rgba(255,255,255,0.06)",
  },
  label: {
    fontFamily: "'Martian Mono', monospace",
    fontSize: 9,
    letterSpacing: "0.16em",
    textTransform: "uppercase" as const,
    color: "#9aa293",
  },
  clearBtn: {
    background: "transparent",
    border: "none",
    color: "#9aa293",
    fontFamily: "'Martian Mono', monospace",
    fontSize: 9,
    cursor: "pointer",
    padding: "2px 6px",
  },
  thread: {
    display: "flex",
    flexDirection: "column",
    gap: 10,
    padding: "14px 16px",
    minHeight: 120,
    maxHeight: 320,
    overflowY: "auto" as const,
  },
  emptyHint: {
    fontFamily: "'Martian Mono', monospace",
    fontSize: 10,
    color: "#9aa293",
    textAlign: "center" as const,
    margin: "20px 0",
    lineHeight: 1.6,
  },
  bubbleUser: {
    alignSelf: "flex-end" as const,
    background: "rgba(127,119,221,0.12)",
    border: "1px solid rgba(127,119,221,0.2)",
    borderRadius: "12px 12px 2px 12px",
    padding: "8px 12px",
    maxWidth: "85%",
    display: "flex",
    flexDirection: "column" as const,
    gap: 3,
  },
  bubbleAssistant: {
    alignSelf: "flex-start" as const,
    background: "rgba(29,158,117,0.08)",
    border: "1px solid rgba(29,158,117,0.18)",
    borderRadius: "12px 12px 12px 2px",
    padding: "8px 12px",
    maxWidth: "90%",
    display: "flex",
    flexDirection: "column" as const,
    gap: 3,
  },
  roleTag: {
    fontFamily: "'Martian Mono', monospace",
    fontSize: 8,
    letterSpacing: "0.12em",
    color: "#9aa293",
    textTransform: "uppercase" as const,
  },
  bubbleText: {
    fontSize: 13,
    color: "#f0ece2",
    lineHeight: 1.6,
    margin: 0,
  },
  replayBtn: {
    background: "transparent",
    border: "none",
    color: "#1d9e75",
    fontSize: 11,
    cursor: "pointer",
    padding: 0,
    alignSelf: "flex-start" as const,
    fontFamily: "'Martian Mono', monospace",
  },
  controls: {
    padding: "10px 16px 16px",
    borderTop: "1px solid rgba(255,255,255,0.06)",
    display: "flex",
    justifyContent: "center",
  },
  micBtn: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    background: "rgba(239,159,39,0.10)",
    border: "1px solid rgba(239,159,39,0.3)",
    borderRadius: 10,
    padding: "10px 20px",
    cursor: "pointer",
    color: "#ef9f27",
  },
  micRecording: {
    background: "rgba(226,75,74,0.12)",
    border: "1px solid rgba(226,75,74,0.4)",
    color: "#e24b4a",
  },
  micDisabled: {
    background: "rgba(255,255,255,0.04)",
    border: "1px solid rgba(255,255,255,0.08)",
    color: "#9aa293",
    cursor: "not-allowed" as const,
  },
  micLabel: {
    fontFamily: "'Martian Mono', monospace",
    fontSize: 10,
    letterSpacing: "0.08em",
  },
  pulse: {
    width: 10, height: 10,
    borderRadius: "50%",
    background: "#e24b4a",
    display: "inline-block",
    animation: "pulse 1s infinite",
  },
  spinner: {
    width: 14, height: 14,
    border: "2px solid rgba(255,255,255,0.1)",
    borderTop: "2px solid #9aa293",
    borderRadius: "50%",
    display: "inline-block",
    animation: "spin 0.7s linear infinite",
  },
  errorText: {
    fontFamily: "'Martian Mono', monospace",
    fontSize: 10,
    color: "#e24b4a",
    padding: "0 16px 8px",
    margin: 0,
  },
};
