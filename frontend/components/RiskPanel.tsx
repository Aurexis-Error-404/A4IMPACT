"use client";

import { CommodityInsightSummary, formatCurrency } from "../lib/canned-data";
import { PriceDeviationGauge } from "./PriceDeviationGauge";

type Props = {
  insights: CommodityInsightSummary;
};

export function RiskPanel({ insights }: Props) {
  const cls = insights.riskLevel.toLowerCase();
  return (
    <article className="card feature">
      <span className="card-label">Risk review</span>
      <div className="risk-headline">
        <h3>{insights.commodity}</h3>
        <span className={`risk-badge ${cls}`}>{insights.riskLevel}</span>
      </div>
      <PriceDeviationGauge deltaPct={insights.latestDeltaPct} />
      <div className="risk-panel" style={{ marginTop: 18 }}>
        <div className="risk-item">
          <span className="label">Latest ref price</span>
          <span className="value">{formatCurrency(insights.latestReferencePrice)}</span>
        </div>
        <div className="risk-item">
          <span className="label">MSP floor</span>
          <span className="value">{formatCurrency(insights.latestMsp)}</span>
        </div>
        <div className="risk-item">
          <span className="label">Deviation</span>
          <span className="value">
            {(insights.latestDeltaPct * 100).toFixed(1)}%
          </span>
        </div>
        <div className="risk-item">
          <span className="label">Season coverage</span>
          <span className="value">{insights.seasonAvailability}</span>
        </div>
      </div>
    </article>
  );
}
