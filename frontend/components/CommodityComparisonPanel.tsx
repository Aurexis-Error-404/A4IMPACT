"use client";

import { useState } from "react";
import type { CommodityCardSummary, CommodityInsightSummary } from "../lib/canned-data";
import { formatCurrency } from "../lib/canned-data";

interface CommodityComparisonPanelProps {
  allCommodities: CommodityCardSummary[];
  insights: Record<string, CommodityInsightSummary>;
  onRequestInsights: (slug: string) => void;
}

const RISK_COLOR: Record<string, string> = {
  High: "var(--red)",
  Watch: "var(--gold)",
  Low: "var(--teal)",
};

const TREND_ICON: Record<string, string> = {
  up: "↑",
  down: "↓",
  flat: "→",
};

const TREND_COLOR: Record<string, string> = {
  up: "var(--teal)",
  down: "var(--red)",
  flat: "var(--muted)",
};

const REC_COLOR: Record<string, string> = {
  Hold: "var(--teal)",
  "Lean sell": "var(--gold)",
  Defer: "var(--muted)",
  Protect: "var(--red)",
};

export function CommodityComparisonPanel({
  allCommodities,
  insights,
  onRequestInsights,
}: CommodityComparisonPanelProps) {
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState<string[]>([]);

  const toggle = (slug: string) => {
    setSelected((prev) => {
      if (prev.includes(slug)) return prev.filter((s) => s !== slug);
      if (prev.length >= 3) return prev;
      if (!insights[slug]) onRequestInsights(slug);
      return [...prev, slug];
    });
  };

  const selectedData = selected
    .map((slug) => ({
      slug,
      card: allCommodities.find((c) => c.slug === slug)!,
      insight: insights[slug] ?? null,
    }))
    .filter((d) => d.card);

  return (
    <div
      style={{
        background: "var(--panel)",
        border: "1px solid var(--border)",
        borderRadius: "12px",
        overflow: "hidden",
        marginTop: "16px",
      }}
    >
      <button
        onClick={() => setOpen((v) => !v)}
        style={{
          width: "100%",
          background: "none",
          border: "none",
          padding: "14px 16px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          cursor: "pointer",
          color: "var(--ink)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontSize: "13px", fontWeight: 600 }}>Compare Commodities</span>
          {selected.length > 0 && (
            <span
              style={{
                background: "var(--violet)",
                color: "white",
                borderRadius: "99px",
                padding: "1px 8px",
                fontSize: "11px",
                fontWeight: 600,
              }}
            >
              {selected.length} selected
            </span>
          )}
        </div>
        <span
          style={{
            fontSize: "12px",
            color: "var(--muted)",
            transform: open ? "rotate(180deg)" : undefined,
            transition: "transform 0.2s",
          }}
        >
          ▾
        </span>
      </button>

      {open && (
        <div style={{ padding: "0 16px 16px", borderTop: "1px solid var(--border)" }}>
          <p style={{ fontSize: "11px", color: "var(--muted)", margin: "12px 0 10px" }}>
            Select up to 3 commodities to compare side-by-side.
          </p>

          <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "16px" }}>
            {allCommodities.map((c) => {
              const isSelected = selected.includes(c.slug);
              return (
                <button
                  key={c.slug}
                  onClick={() => toggle(c.slug)}
                  disabled={!isSelected && selected.length >= 3}
                  style={{
                    background: isSelected ? "var(--violet)" : "var(--glass)",
                    border: `1px solid ${isSelected ? "var(--violet)" : "var(--border)"}`,
                    color: isSelected ? "white" : "var(--ink)",
                    borderRadius: "99px",
                    padding: "4px 12px",
                    fontSize: "12px",
                    cursor: selected.length >= 3 && !isSelected ? "not-allowed" : "pointer",
                    opacity: selected.length >= 3 && !isSelected ? 0.45 : 1,
                    transition: "all 0.15s",
                  }}
                >
                  {c.commodity}
                </button>
              );
            })}
          </div>

          {selectedData.length >= 2 && (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
                <thead>
                  <tr>
                    {["Commodity", "Season", "Price", "vs MSP", "Trend", "Risk", "Recommendation"].map(
                      (h) => (
                        <th
                          key={h}
                          style={{
                            textAlign: "left",
                            padding: "6px 10px",
                            color: "var(--muted)",
                            fontWeight: 500,
                            fontSize: "11px",
                            borderBottom: "1px solid var(--border)",
                            whiteSpace: "nowrap",
                          }}
                        >
                          {h}
                        </th>
                      ),
                    )}
                  </tr>
                </thead>
                <tbody>
                  {selectedData.map(({ slug, card, insight }) => {
                    const ins = insight ?? null;
                    return (
                      <tr key={slug}>
                        <td style={{ padding: "10px", fontWeight: 600, color: "var(--ink)", whiteSpace: "nowrap" }}>
                          <div>{card.commodity}</div>
                          <div style={{ fontSize: "10px", color: "var(--muted)", fontWeight: 400 }}>{card.group}</div>
                        </td>
                        <td style={{ padding: "10px", color: "var(--muted)" }}>
                          {card.latestSeason}
                        </td>
                        <td style={{ padding: "10px", color: "var(--ink)", fontVariantNumeric: "tabular-nums" }}>
                          {card.latestReferencePrice != null ? formatCurrency(card.latestReferencePrice) : "—"}
                        </td>
                        <td
                          style={{
                            padding: "10px",
                            color: card.latestDeltaPct >= 0 ? "var(--teal)" : "var(--red)",
                            fontVariantNumeric: "tabular-nums",
                          }}
                        >
                          {card.latestDeltaPct >= 0 ? "+" : ""}
                          {(card.latestDeltaPct * 100).toFixed(1)}%
                        </td>
                        <td style={{ padding: "10px" }}>
                          <span style={{ color: TREND_COLOR[card.priceTrend], fontSize: "14px" }}>
                            {TREND_ICON[card.priceTrend]}
                          </span>
                        </td>
                        <td style={{ padding: "10px" }}>
                          <span
                            style={{
                              color: RISK_COLOR[card.riskLevel],
                              fontWeight: 600,
                              fontSize: "11px",
                            }}
                          >
                            {card.riskLevel}
                          </span>
                        </td>
                        <td style={{ padding: "10px" }}>
                          {ins ? (
                            <span
                              style={{
                                color: REC_COLOR[ins.recommendationLabel] ?? "var(--ink)",
                                fontWeight: 600,
                                fontSize: "11px",
                              }}
                            >
                              {ins.recommendationLabel}
                            </span>
                          ) : (
                            <span style={{ color: "var(--muted)", fontSize: "11px" }}>Loading…</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {selectedData.length === 1 && (
            <p style={{ fontSize: "12px", color: "var(--muted)", margin: 0 }}>
              Select one more commodity to see the comparison.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
