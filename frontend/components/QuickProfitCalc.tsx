"use client";

import { useState } from "react";
import type { CommodityInsightSummary } from "../lib/canned-data";
import { formatCurrency } from "../lib/canned-data";

interface QuickProfitCalcProps {
  insights: CommodityInsightSummary;
}

export function QuickProfitCalc({ insights }: QuickProfitCalcProps) {
  const [open, setOpen] = useState(false);
  const [quantity, setQuantity] = useState(10);
  const [cost, setCost] = useState(0);

  const current = insights.latestReferencePrice;
  const msp = insights.latestMsp;
  const ceiling = insights.expectedPriceRange?.ceiling ?? null;

  const profit = (price: number) => (price - cost) * quantity;
  const sign = (n: number) => (n >= 0 ? "+" : "");
  const color = (n: number) =>
    n > 0 ? "var(--teal)" : n < 0 ? "var(--red)" : "var(--muted)";

  const rows: { label: string; price: number }[] = [
    { label: "At current price", price: current },
    { label: "At MSP floor", price: msp },
    ...(ceiling !== null ? [{ label: "At ceiling", price: ceiling }] : []),
  ];

  return (
    <div
      style={{
        background: "var(--panel)",
        border: "1px solid var(--border)",
        borderRadius: "12px",
        overflow: "hidden",
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
          <span style={{ fontSize: "14px" }}>₹</span>
          <span style={{ fontSize: "13px", fontWeight: 600 }}>Quick Profit Calculator</span>
        </div>
        <span style={{ fontSize: "12px", color: "var(--muted)", transform: open ? "rotate(180deg)" : undefined, transition: "transform 0.2s" }}>
          ▾
        </span>
      </button>

      {open && (
        <div style={{ padding: "0 16px 16px", borderTop: "1px solid var(--border)" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginTop: "14px" }}>
            <label style={{ fontSize: "11px", color: "var(--muted)" }}>
              Quantity (quintals)
              <input
                type="number"
                min={1}
                value={quantity}
                onChange={(e) => setQuantity(Math.max(1, Number(e.target.value)))}
                style={{
                  display: "block",
                  width: "100%",
                  marginTop: "4px",
                  background: "var(--glass)",
                  border: "1px solid var(--border)",
                  borderRadius: "6px",
                  color: "var(--ink)",
                  padding: "6px 8px",
                  fontSize: "14px",
                  fontFamily: "inherit",
                }}
              />
            </label>
            <label style={{ fontSize: "11px", color: "var(--muted)" }}>
              Cost / quintal (Rs.)
              <input
                type="number"
                min={0}
                value={cost}
                onChange={(e) => setCost(Math.max(0, Number(e.target.value)))}
                style={{
                  display: "block",
                  width: "100%",
                  marginTop: "4px",
                  background: "var(--glass)",
                  border: "1px solid var(--border)",
                  borderRadius: "6px",
                  color: "var(--ink)",
                  padding: "6px 8px",
                  fontSize: "14px",
                  fontFamily: "inherit",
                }}
              />
            </label>
          </div>

          <div style={{ marginTop: "14px", display: "flex", flexDirection: "column", gap: "8px" }}>
            {rows.map(({ label, price }) => {
              const p = profit(price);
              return (
                <div
                  key={label}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    background: "var(--glass)",
                    borderRadius: "8px",
                    padding: "10px 12px",
                  }}
                >
                  <div>
                    <div style={{ fontSize: "11px", color: "var(--muted)" }}>{label}</div>
                    <div style={{ fontSize: "12px", color: "var(--ink)" }}>{formatCurrency(price)} / qtl</div>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontSize: "16px", fontWeight: 700, color: color(p), fontVariantNumeric: "tabular-nums" }}>
                      {sign(p)}{formatCurrency(Math.abs(p))}
                    </div>
                    <div style={{ fontSize: "10px", color: "var(--muted)" }}>
                      {sign(p)}{formatCurrency(Math.abs(p / quantity))} / qtl
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {cost > 0 && current < cost && (
            <p style={{ marginTop: "10px", fontSize: "11px", color: "var(--red)", lineHeight: 1.4 }}>
              ⚠ Current price is below your cost price — selling now results in a loss.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
