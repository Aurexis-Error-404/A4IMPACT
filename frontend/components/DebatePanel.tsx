"use client";

import { useEffect, useRef, useState } from "react";

const WS_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000")
  .replace(/^http/, "ws") + "/ws";

type AgentStage = "optimist" | "pessimist" | "risk" | "mediator";

type AgentCard = {
  stage: AgentStage;
  verdict?: string;
  confidence?: number;
  reasoning?: string;
  risk_level?: string;
  recommendationLabel?: string;
  confidenceLabel?: string;
  recommendationRationale?: string;
  actionable_timing?: string;
  conflict_score?: string;
  error?: string;
};

type DebateAlertEvent = {
  severity: "red" | "amber";
  commodity: string;
  headline: string;
  riskLevel: "High" | "Watch";
};

interface DebatePanelProps {
  commodity: string;
  open: boolean;
  onClose: () => void;
  onAlert?: (event: DebateAlertEvent) => void;
}

const AGENT_META: Record<AgentStage, { label: string; color: string; borderColor: string }> = {
  optimist: { label: "Season Optimist", color: "#22c55e", borderColor: "rgba(34,197,94,0.5)" },
  pessimist: { label: "Season Pessimist", color: "#ef4444", borderColor: "rgba(239,68,68,0.5)" },
  risk: { label: "Risk Analyst", color: "#f59e0b", borderColor: "rgba(245,158,11,0.5)" },
  mediator: { label: "Mediator", color: "#a78bfa", borderColor: "rgba(167,139,250,0.5)" },
};

const STAGE_ORDER: AgentStage[] = ["optimist", "pessimist", "risk", "mediator"];

const VERDICT_PLAIN: Record<string, string> = {
  HOLD: "Hold — keep your stock",
  LEAN_SELL: "Consider selling now",
  DEFER: "Wait — price may recover",
  PROTECT: "Do not sell — protect your stock",
};

const AGENT_ROLE: Record<AgentStage, string> = {
  optimist: "Looking for upside",
  pessimist: "Checking for risk",
  risk: "Assessing danger level",
  mediator: "Final recommendation",
};

export function DebatePanel({ commodity, open, onClose, onAlert }: DebatePanelProps) {
  const wsRef = useRef<WebSocket | null>(null);
  const [cards, setCards] = useState<Partial<Record<AgentStage, AgentCard>>>({});
  const [pending, setPending] = useState<AgentStage[]>([]);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!open || !commodity) return;

    setCards({});
    setDone(false);
    setPending([...STAGE_ORDER]);

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify({ action: "start", commodity }));
    };

    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      const stage: string | undefined = msg.stage;

      if (stage === "alert") {
        onAlert?.({
          severity: msg.severity,
          commodity: msg.commodity,
          headline: msg.headline,
          riskLevel: msg.riskLevel,
        });
        return;
      }

      if (stage === "done") {
        setDone(true);
        return;
      }

      if (stage === "error") return;

      if (stage && STAGE_ORDER.includes(stage as AgentStage)) {
        const s = stage as AgentStage;
        setCards((prev) => ({ ...prev, [s]: { stage: s, ...msg.data } }));
        setPending((prev) => prev.filter((p) => p !== s));
      }
    };

    ws.onerror = () => setDone(true);

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [open, commodity]);  // eslint-disable-line react-hooks/exhaustive-deps

  if (!open) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 1000,
        background: "rgba(0,0,0,0.72)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "16px",
      }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        style={{
          background: "var(--shell-strong)",
          border: "1px solid var(--border)",
          borderRadius: "16px",
          width: "100%",
          maxWidth: "820px",
          maxHeight: "90vh",
          overflowY: "auto",
          padding: "24px",
          boxShadow: "var(--shadow)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "20px" }}>
          <div>
            <span style={{ fontSize: "11px", color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
              Live AI Debate
            </span>
            <h2 style={{ margin: "2px 0 0", fontSize: "18px", color: "var(--ink)" }}>
              {commodity}
            </h2>
          </div>
          <button
            onClick={onClose}
            style={{
              background: "var(--panel)",
              border: "1px solid var(--border)",
              color: "var(--ink)",
              borderRadius: "8px",
              padding: "6px 14px",
              cursor: "pointer",
              fontSize: "13px",
            }}
          >
            Close
          </button>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
          {STAGE_ORDER.map((stage) => {
            const meta = AGENT_META[stage];
            const card = cards[stage];
            const isWaiting = pending.includes(stage);

            return (
              <div
                key={stage}
                style={{
                  background: "var(--panel)",
                  border: `1px solid ${card ? meta.borderColor : "var(--border)"}`,
                  borderRadius: "12px",
                  padding: "16px",
                  animation: card ? "debateFadeIn 0.4s var(--ease) both" : undefined,
                  transition: "border-color 0.3s",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "10px" }}>
                  <span
                    style={{
                      width: "8px",
                      height: "8px",
                      borderRadius: "50%",
                      background: isWaiting ? "var(--muted)" : meta.color,
                      flexShrink: 0,
                      boxShadow: isWaiting ? "none" : `0 0 6px ${meta.color}`,
                      animation: isWaiting ? "debatePulse 1.4s ease-in-out infinite" : undefined,
                    }}
                  />
                  <div>
                    <span style={{ fontSize: "12px", fontWeight: 600, color: card ? meta.color : "var(--muted)", display: "block" }}>
                      {meta.label}
                    </span>
                    <span style={{ fontSize: "10px", color: "var(--muted)" }}>
                      {AGENT_ROLE[stage]}
                    </span>
                  </div>
                </div>

                {isWaiting ? (
                  <div style={{ color: "var(--muted)", fontSize: "13px" }}>
                    <span style={{ animation: "debatePulse 1.4s ease-in-out infinite", display: "inline-block" }}>
                      Thinking…
                    </span>
                    <div style={{ marginTop: "8px", display: "flex", gap: "4px" }}>
                      {[0, 1, 2].map((i) => (
                        <span
                          key={i}
                          style={{
                            width: "6px",
                            height: "6px",
                            borderRadius: "50%",
                            background: "var(--muted)",
                            animation: `debateDot 1.2s ease-in-out ${i * 0.2}s infinite`,
                            display: "inline-block",
                          }}
                        />
                      ))}
                    </div>
                  </div>
                ) : card?.error ? (
                  <p style={{ color: "var(--red)", fontSize: "12px", margin: 0 }}>
                    Error: {card.error}
                  </p>
                ) : card ? (
                  <div style={{ fontSize: "13px", color: "var(--ink)" }}>
                    {stage === "mediator" ? (
                      <>
                        <div style={{ fontWeight: 700, fontSize: "15px", color: meta.color, marginBottom: "4px" }}>
                          {card.recommendationLabel}
                        </div>
                        <div style={{ color: "var(--muted)", fontSize: "11px", marginBottom: "8px" }}>
                          {card.confidenceLabel}
                          {card.conflict_score && (
                            <span style={{ marginLeft: "8px", color: card.conflict_score === "HIGH" ? "var(--red)" : card.conflict_score === "MEDIUM" ? "var(--gold)" : "var(--teal)" }}>
                              · {card.conflict_score === "LOW" ? "All agreed" : card.conflict_score === "MEDIUM" ? "Mixed" : "Split"}
                            </span>
                          )}
                        </div>
                        <p style={{ margin: "0 0 8px", lineHeight: 1.5, color: "var(--muted)", fontSize: "12px", whiteSpace: "pre-wrap" }}>
                          {card.recommendationRationale}
                        </p>
                        {card.actionable_timing && (
                          <div style={{ borderTop: "1px solid var(--border)", paddingTop: "8px", color: "var(--gold)", fontSize: "11px" }}>
                            ⏱ {card.actionable_timing}
                          </div>
                        )}
                      </>
                    ) : (
                      <>
                        <div style={{ fontWeight: 700, fontSize: "14px", color: meta.color, marginBottom: "2px" }}>
                          {card.verdict ? (VERDICT_PLAIN[card.verdict] ?? card.verdict) : "—"}
                        </div>
                        <div style={{ fontSize: "11px", color: "var(--muted)", marginBottom: "6px" }}>
                          {card.confidence !== undefined && `${card.confidence}% confidence`}
                          {card.risk_level && ` · Risk: ${card.risk_level}`}
                        </div>
                        <p style={{ margin: 0, lineHeight: 1.5, color: "var(--muted)", fontSize: "12px", whiteSpace: "pre-wrap" }}>
                          {card.reasoning}
                        </p>
                      </>
                    )}
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>

        {done && (
          <div style={{ marginTop: "16px", textAlign: "center", color: "var(--teal)", fontSize: "12px" }}>
            ✓ Debate complete
          </div>
        )}
      </div>

      <style>{`
        @keyframes debateFadeIn {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes debatePulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
        @keyframes debateDot {
          0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
          40% { transform: scale(1); opacity: 1; }
        }
      `}</style>
    </div>
  );
}
