"use client";

import { useEffect, useRef } from "react";

export type DebateAlertEvent = {
  severity: "red" | "amber";
  commodity: string;
  headline: string;
  riskLevel: "High" | "Watch";
};

interface AlertBannerProps {
  alerts: DebateAlertEvent[];
  onDismiss: (index: number) => void;
}

export function AlertBanner({ alerts, onDismiss }: AlertBannerProps) {
  const timersRef = useRef<Map<number, ReturnType<typeof setTimeout>>>(new Map());

  useEffect(() => {
    alerts.forEach((_, i) => {
      if (!timersRef.current.has(i)) {
        timersRef.current.set(
          i,
          setTimeout(() => {
            onDismiss(i);
            timersRef.current.delete(i);
          }, 5000),
        );
      }
    });

    return () => {
      timersRef.current.forEach((t) => clearTimeout(t));
    };
  }, [alerts, onDismiss]);

  if (alerts.length === 0) return null;

  return (
    <>
      <div
        style={{
          position: "fixed",
          top: "16px",
          right: "16px",
          zIndex: 2000,
          display: "flex",
          flexDirection: "column",
          gap: "8px",
          maxWidth: "340px",
          width: "100%",
          pointerEvents: "none",
        }}
      >
        {alerts.map((alert, i) => (
          <div
            key={i}
            style={{
              background: alert.severity === "red"
                ? "rgba(226,75,74,0.18)"
                : "rgba(239,159,39,0.18)",
              border: `1px solid ${alert.severity === "red" ? "var(--red)" : "var(--gold)"}`,
              borderRadius: "10px",
              padding: "12px 14px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-start",
              gap: "10px",
              backdropFilter: "blur(12px)",
              animation: "alertSlideIn 0.35s var(--ease) both",
              pointerEvents: "all",
            }}
          >
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "3px" }}>
                <span
                  style={{
                    width: "7px",
                    height: "7px",
                    borderRadius: "50%",
                    background: alert.severity === "red" ? "var(--red)" : "var(--gold)",
                    flexShrink: 0,
                  }}
                />
                <span
                  style={{
                    fontSize: "11px",
                    fontWeight: 700,
                    color: alert.severity === "red" ? "var(--red)" : "var(--gold)",
                    textTransform: "uppercase",
                    letterSpacing: "0.06em",
                  }}
                >
                  {alert.riskLevel} Risk · {alert.commodity}
                </span>
              </div>
              <p style={{ margin: 0, fontSize: "12px", color: "var(--ink)", lineHeight: 1.4 }}>
                {alert.headline}
              </p>
            </div>
            <button
              onClick={() => onDismiss(i)}
              style={{
                background: "none",
                border: "none",
                color: "var(--muted)",
                cursor: "pointer",
                fontSize: "14px",
                padding: "0",
                flexShrink: 0,
                lineHeight: 1,
              }}
              aria-label="Dismiss alert"
            >
              ×
            </button>
          </div>
        ))}
      </div>

      <style>{`
        @keyframes alertSlideIn {
          from { opacity: 0; transform: translateX(40px); }
          to   { opacity: 1; transform: translateX(0); }
        }
      `}</style>
    </>
  );
}
