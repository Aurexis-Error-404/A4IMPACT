import { useState, useRef, useEffect } from "react";

const VOICE_API_URL = "http://localhost:8000/voice/query";
const MAX_RECORD_SECONDS = 30;

// Set to true while Member A's backend isn't ready yet
const USE_MOCK = false;

type VoiceState = "idle" | "recording" | "processing" | "response";

interface VoiceResponse {
  text_response_te: string;
  audio_base64: string | null;
  commodity_detected: string;
}

const MOCK_RESPONSE: VoiceResponse = {
  text_response_te:
    "Patti dhara ippudu MSP kanna ekkuvaga undi — hold cheyyandi. Rendu vaараalu vachi chudandi.",
  audio_base64: null,
  commodity_detected: "Cotton",
};

function pickMimeType(): string {
  const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg"];
  return candidates.find((t) => MediaRecorder.isTypeSupported(t)) ?? "";
}

async function queryVoice(formData: FormData): Promise<VoiceResponse> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 2000));
    return MOCK_RESPONSE;
  }
  const res = await fetch(VOICE_API_URL, { method: "POST", body: formData });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export default function VoiceButton() {
  const [state, setState] = useState<VoiceState>("idle");
  const [response, setResponse] = useState<VoiceResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  function stopCurrentAudio() {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
  }

  async function startRecording() {
    setError(null);
    setResponse(null);
    stopCurrentAudio();

    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (e: unknown) {
      if (e instanceof DOMException) {
        if (e.name === "NotFoundError" || e.name === "DevicesNotFoundError") {
          setError("Voice not available on this device.");
        } else {
          setError("Please allow microphone access.");
        }
      } else {
        setError("Please allow microphone access.");
      }
      return;
    }

    chunksRef.current = [];
    const mimeType = pickMimeType();
    const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
    mediaRecorderRef.current = recorder;

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };

    recorder.onstop = async () => {
      if (timerRef.current) clearInterval(timerRef.current);
      stream.getTracks().forEach((t) => t.stop());

      const blob = new Blob(chunksRef.current, { type: mimeType || "audio/webm" });
      const formData = new FormData();
      // filename extension matches MIME so backend can detect format
      const ext = mimeType.includes("mp4") ? "mp4" : mimeType.includes("ogg") ? "ogg" : "webm";
      formData.append("audio", blob, `recording.${ext}`);

      setState("processing");
      try {
        const data = await queryVoice(formData);
        setResponse(data);
        setState("response");

        if (data.audio_base64) {
          const audio = new Audio("data:audio/mp3;base64," + data.audio_base64);
          audioRef.current = audio;
          audio.play();
        }
      } catch {
        setError("Voice query failed — please try again.");
        setState("idle");
      }
    };

    // Auto-stop at MAX_RECORD_SECONDS
    setElapsed(0);
    timerRef.current = setInterval(() => {
      setElapsed((s) => {
        if (s + 1 >= MAX_RECORD_SECONDS) {
          recorder.stop();
          return MAX_RECORD_SECONDS;
        }
        return s + 1;
      });
    }, 1000);

    recorder.start();
    setState("recording");
  }

  function stopRecording() {
    if (timerRef.current) clearInterval(timerRef.current);
    mediaRecorderRef.current?.stop();
  }

  function replay() {
    if (!response?.audio_base64) return;
    stopCurrentAudio();
    const audio = new Audio("data:audio/mp3;base64," + response.audio_base64);
    audioRef.current = audio;
    audio.play();
  }

  function reset() {
    stopCurrentAudio();
    setState("idle");
    setResponse(null);
    setError(null);
    setElapsed(0);
  }

  const remaining = MAX_RECORD_SECONDS - elapsed;

  return (
    <div style={styles.card}>
      <span style={styles.label}>
        VOICE QUERY{USE_MOCK ? <span style={styles.mockBadge}> · MOCK</span> : null}
      </span>

      {state === "idle" && (
        <button style={styles.btn} onClick={startRecording}>
          <MicIcon />
          <span style={styles.btnText}>Ask in Telugu</span>
        </button>
      )}

      {state === "recording" && (
        <button style={{ ...styles.btn, ...styles.btnRecording }} onClick={stopRecording}>
          <span style={styles.pulse} />
          <span style={styles.btnText}>
            Listening… {remaining < 10 ? `(${remaining}s)` : "(tap to stop)"}
          </span>
        </button>
      )}

      {state === "processing" && (
        <div style={styles.statusRow}>
          <Spinner />
          <span style={styles.mutedText}>Thinking…</span>
        </div>
      )}

      {state === "response" && response && (
        <div style={styles.responseBox}>
          {response.commodity_detected && (
            <span style={styles.commodityTag}>{response.commodity_detected}</span>
          )}
          <p style={styles.responseText}>{response.text_response_te}</p>
          {response.audio_base64 ? (
            <button style={styles.replayBtn} onClick={replay}>
              ▶ Replay
            </button>
          ) : (
            <span style={styles.audioNote}>
              Audio unavailable — Telugu response displayed above.
            </span>
          )}
          <button style={styles.resetBtn} onClick={reset}>
            Ask another
          </button>
        </div>
      )}

      {error && (
        <div style={styles.errorRow}>
          <p style={styles.errorText}>{error}</p>
          {state === "idle" && (
            <button style={styles.retryBtn} onClick={startRecording}>
              Try again
            </button>
          )}
        </div>
      )}
    </div>
  );
}

function MicIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ef9f27" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="9" y="2" width="6" height="12" rx="3" />
      <path d="M5 10a7 7 0 0 0 14 0" />
      <line x1="12" y1="19" x2="12" y2="22" />
      <line x1="9" y1="22" x2="15" y2="22" />
    </svg>
  );
}

function Spinner() {
  return <span style={styles.spinner} />;
}

const styles: Record<string, React.CSSProperties> = {
  card: {
    background: "rgba(255,255,255,0.04)",
    border: "1px solid rgba(255,255,255,0.08)",
    borderRadius: 14,
    padding: "20px 24px",
    display: "inline-flex",
    flexDirection: "column",
    gap: 12,
    minWidth: 280,
    fontFamily: "'Lora', Georgia, serif",
  },
  label: {
    fontFamily: "'Martian Mono', monospace",
    fontSize: 9,
    letterSpacing: "0.16em",
    textTransform: "uppercase" as const,
    color: "#9aa293",
  },
  mockBadge: {
    color: "#7f77dd",
  },
  btn: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    background: "rgba(239,159,39,0.10)",
    border: "1px solid rgba(239,159,39,0.3)",
    borderRadius: 10,
    padding: "12px 18px",
    cursor: "pointer",
    color: "#ef9f27",
    transition: "background 0.15s",
  },
  btnRecording: {
    background: "rgba(226,75,74,0.12)",
    border: "1px solid rgba(226,75,74,0.4)",
    color: "#e24b4a",
  },
  btnText: {
    fontFamily: "'Martian Mono', monospace",
    fontSize: 11,
    letterSpacing: "0.08em",
  },
  pulse: {
    width: 10,
    height: 10,
    borderRadius: "50%",
    background: "#e24b4a",
    display: "inline-block",
    animation: "pulse 1s infinite",
  },
  statusRow: {
    display: "flex",
    alignItems: "center",
    gap: 10,
  },
  spinner: {
    width: 16,
    height: 16,
    border: "2px solid rgba(255,255,255,0.1)",
    borderTop: "2px solid #ef9f27",
    borderRadius: "50%",
    display: "inline-block",
    animation: "spin 0.7s linear infinite",
  },
  mutedText: {
    fontFamily: "'Martian Mono', monospace",
    fontSize: 11,
    color: "#9aa293",
  },
  responseBox: {
    display: "flex",
    flexDirection: "column",
    gap: 10,
  },
  commodityTag: {
    fontFamily: "'Martian Mono', monospace",
    fontSize: 9,
    letterSpacing: "0.14em",
    textTransform: "uppercase" as const,
    color: "#1d9e75",
    display: "block",
  },
  responseText: {
    fontSize: 14,
    color: "#f0ece2",
    lineHeight: 1.65,
    margin: 0,
  },
  audioNote: {
    fontFamily: "'Martian Mono', monospace",
    fontSize: 10,
    color: "#9aa293",
  },
  replayBtn: {
    background: "transparent",
    border: "1px solid rgba(255,255,255,0.08)",
    borderRadius: 6,
    padding: "5px 12px",
    color: "#9aa293",
    fontFamily: "'Martian Mono', monospace",
    fontSize: 10,
    cursor: "pointer",
    width: "fit-content",
  },
  resetBtn: {
    background: "transparent",
    border: "1px solid rgba(239,159,39,0.25)",
    borderRadius: 6,
    padding: "6px 14px",
    color: "#ef9f27",
    fontFamily: "'Martian Mono', monospace",
    fontSize: 10,
    cursor: "pointer",
    width: "fit-content",
    marginTop: 4,
  },
  errorRow: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  errorText: {
    fontFamily: "'Martian Mono', monospace",
    fontSize: 11,
    color: "#e24b4a",
    margin: 0,
  },
  retryBtn: {
    background: "transparent",
    border: "1px solid rgba(226,75,74,0.3)",
    borderRadius: 6,
    padding: "5px 12px",
    color: "#e24b4a",
    fontFamily: "'Martian Mono', monospace",
    fontSize: 10,
    cursor: "pointer",
    width: "fit-content",
  },
};
