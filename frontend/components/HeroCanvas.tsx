"use client";

import { CommodityInsightSummary, formatCurrency } from "../lib/canned-data";
import { TrendArrowBadge } from "./TrendArrowBadge";

type Props = {
  insights: CommodityInsightSummary | null;
  group: string;
  lastUpdated: string;
};

export function HeroCanvas({ insights, group, lastUpdated }: Props) {
  if (!insights) {
    return (
      <section className="hero-canvas">
        <div className="hero-content">
          <div>
            <span className="hero-eyebrow">Seasonal commodity intelligence</span>
            <h1 className="hero-headline">Select a commodity to begin.</h1>
          </div>
        </div>
      </section>
    );
  }

  const riskChip =
    insights.riskLevel === "High"
      ? "red"
      : insights.riskLevel === "Watch"
        ? "amber"
        : "gold";

  return (
    <section className="hero-canvas">
      <div className="hero-content">
        <div>
          <span className="hero-eyebrow">Seasonal - {group}</span>
          <h1 className="hero-headline">{insights.commodity}</h1>
          <p className="hero-sub">
            A heuristic read of price, MSP, and seasonal coverage across the
            reporting window. Values stay qualitative where the signal is thin.
          </p>
          <div className="hero-status">
            <span className={`chip ${riskChip}`}>
              <span className="dot" />
              Risk - {insights.riskLevel}
            </span>
            <span className="chip teal">
              <span className="dot" />
              {insights.seasonAvailability}
            </span>
            <span className="chip">
              <span className="dot" />
              Latest season {insights.latestSeason}
            </span>
          </div>
        </div>
        <div className="hero-badge-row">
          <TrendArrowBadge
            direction={insights.priceTrend}
            changePct={insights.trendChangePct}
          />
          <span className="chip">
            <span className="dot" />
            Refreshed {lastUpdated}
          </span>
        </div>
      </div>
      <aside className="hero-aside">
        <span className="big-label">Reference price - {insights.latestSeason}</span>
        <span className="big-number mono">
          {formatCurrency(insights.latestReferencePrice)}
        </span>
        <div className="split">
          <div className="stat">
            <span className="big-label">MSP floor</span>
            <span className="val mono">{formatCurrency(insights.latestMsp)}</span>
          </div>
          <div className="stat">
            <span className="big-label">vs MSP</span>
            <span className="val mono">{insights.latestDeltaLabel}</span>
          </div>
        </div>
      </aside>
    </section>
  );
}
