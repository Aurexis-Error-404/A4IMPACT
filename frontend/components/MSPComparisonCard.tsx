"use client";

import { CommodityInsightSummary, formatCurrency } from "../lib/canned-data";
import { PriceDeviationGauge } from "./PriceDeviationGauge";

type Props = {
  insights: CommodityInsightSummary | null;
};

export function MSPComparisonRail({ insights }: Props) {
  if (!insights) return null;

  const deltaClass =
    insights.latestDelta > 0 ? "pos" : insights.latestDelta < 0 ? "neg" : "neu";

  return (
    <div className="grid-rail stagger" id="msp">
      <div className="kpi">
        <span className="kpi-label">MSP floor</span>
        <span className="kpi-value mono">{formatCurrency(insights.latestMsp)}</span>
        <span className="kpi-sub">{insights.latestSeason}</span>
      </div>
      <div className="kpi">
        <span className="kpi-label">Reference price</span>
        <span className="kpi-value mono">{formatCurrency(insights.latestReferencePrice)}</span>
        <span className="kpi-sub">
          {insights.seasonAvailability === "Rabi only" ? "Rabi basis" : "Kharif basis"}
        </span>
      </div>
      <div className="kpi">
        <span className="kpi-label">Deviation</span>
        <span
          className="kpi-value mono"
          style={{
            color:
              deltaClass === "pos"
                ? "#c7d69d"
                : deltaClass === "neg"
                  ? "#f1b2b2"
                  : "var(--ink)",
          }}
        >
          {(insights.latestDeltaPct * 100).toFixed(1)}%
        </span>
        <span className="kpi-sub">
          {insights.latestDelta > 0 ? "above MSP" : insights.latestDelta < 0 ? "below MSP" : "at MSP"}
        </span>
      </div>
      <div className="kpi">
        <span className="kpi-label">Gauge</span>
        <PriceDeviationGauge deltaPct={insights.latestDeltaPct} />
      </div>
    </div>
  );
}
