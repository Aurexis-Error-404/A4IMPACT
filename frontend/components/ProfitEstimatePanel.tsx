"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { fetchProfitEstimate, type ProfitEstimateResult } from "../lib/api";

type Props = {
  commodity: string;
};

function fmt(val: number | null, t: (k: string) => string): string {
  if (val == null) return t("na");
  const sign = val >= 0 ? "+" : "−";
  return `${sign} Rs.${Math.abs(val).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
}

export function ProfitEstimatePanel({ commodity }: Props) {
  const t = useTranslations("profit");
  const [qty, setQty] = useState("");
  const [cost, setCost] = useState("");
  const [result, setResult] = useState<ProfitEstimateResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCalculate() {
    const q = parseFloat(qty);
    if (!q || q <= 0) return;
    setLoading(true);
    setError(null);
    try {
      const c = cost.trim() ? parseFloat(cost) : undefined;
      const res = await fetchProfitEstimate(commodity, q, c);
      setResult(res);
    } catch {
      setError("Could not fetch estimate — check backend connection.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <article className="card profit-panel">
      <span className="card-label">{t("title")}</span>
      <p className="card-copy">{t("subtitle")}</p>

      <div className="profit-form">
        <label className="profit-field">
          <span>{t("quantity")}</span>
          <input
            type="number"
            min={0}
            step={0.5}
            placeholder="e.g. 50"
            value={qty}
            onChange={(e) => setQty(e.target.value)}
            className="profit-input mono"
          />
        </label>
        <label className="profit-field">
          <span>{t("inputCost")}</span>
          <input
            type="number"
            min={0}
            step={100}
            placeholder="e.g. 6000"
            value={cost}
            onChange={(e) => setCost(e.target.value)}
            className="profit-input mono"
          />
        </label>
        <button
          className="profit-btn"
          onClick={handleCalculate}
          disabled={loading || !qty}
        >
          {loading ? "…" : t("calculate")}
        </button>
      </div>

      {error && <p className="profit-error">{error}</p>}

      {result && (
        <div className="profit-results stagger">
          <div className={`profit-row ${result.profit_at_msp != null && result.profit_at_msp >= 0 ? "pos" : "neg"}`}>
            <span className="profit-row-label">{t("atMsp")}</span>
            <span className="profit-row-value mono">{fmt(result.profit_at_msp, t)}</span>
          </div>
          <div className={`profit-row ${result.profit_at_current != null && result.profit_at_current >= 0 ? "pos" : "neg"}`}>
            <span className="profit-row-label">{t("atCurrent")}</span>
            <span className="profit-row-value mono">{fmt(result.profit_at_current, t)}</span>
          </div>
          <div className={`profit-row ${result.profit_at_ceiling != null && result.profit_at_ceiling >= 0 ? "pos" : "neg"}`}>
            <span className="profit-row-label">{t("atCeiling")}</span>
            <span className="profit-row-value mono">{fmt(result.profit_at_ceiling, t)}</span>
          </div>
          <div className="profit-advice">
            <span className="profit-row-label">{t("stagingAdvice")}</span>
            <p className="profit-advice-text">{result.staging_advice}</p>
          </div>
        </div>
      )}
    </article>
  );
}
