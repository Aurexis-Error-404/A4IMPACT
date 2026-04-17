"use client";

import Link from "next/link";
import { useState, useMemo, useEffect } from "react";
import { AlertSeverityStack } from "../../components/AlertSeverityStack";
import { CommodityFilterBar } from "../../components/CommodityFilterBar";
import { HeroCanvas } from "../../components/HeroCanvas";
import { MarketPulseFeed } from "../../components/MarketPulseFeed";
import { MSPComparisonRail } from "../../components/MSPComparisonCard";
import { RecommendationCard } from "../../components/RecommendationCard";
import { RiskPanel } from "../../components/RiskPanel";
import { SeasonArrivalChart } from "../../components/SeasonArrivalChart";
import { SeasonPriceChart } from "../../components/SeasonPriceChart";
import { TopNav } from "../../components/TopNav";
import { TrendArrowBadge } from "../../components/TrendArrowBadge";
import {
  formatCurrency,
  getCommodityGroups,
  getCommoditiesForGroup,
  getCommodityInsights,
  getCommoditySeries,
  getDashboardSummary,
} from "../../lib/canned-data";

export default function DashboardPage() {
  const summary = getDashboardSummary();
  const groups = useMemo(() => getCommodityGroups(), []);

  // Default to spotlight commodity's group, or first group
  const defaultGroup = summary.spotlight?.group ?? groups[0] ?? "";
  const [selectedGroup, setSelectedGroup] = useState(defaultGroup);

  const commoditiesInGroup = useMemo(
    () => getCommoditiesForGroup(selectedGroup),
    [selectedGroup],
  );

  // Default to spotlight commodity if it belongs to the selected group
  const defaultCommodity =
    summary.spotlight?.group === selectedGroup
      ? summary.spotlight.commodity
      : commoditiesInGroup[0] ?? "";
  const [selectedCommodity, setSelectedCommodity] = useState(defaultCommodity);

  // Repair selectedCommodity when group changes and current no longer belongs
  useEffect(() => {
    if (!commoditiesInGroup.includes(selectedCommodity)) {
      setSelectedCommodity(commoditiesInGroup[0] ?? "");
    }
  }, [selectedGroup, commoditiesInGroup, selectedCommodity]);

  // Derive insights + records from selected filters
  const insights = useMemo(
    () => getCommodityInsights(selectedGroup, selectedCommodity),
    [selectedGroup, selectedCommodity],
  );
  const records = useMemo(
    () => getCommoditySeries(selectedGroup, selectedCommodity),
    [selectedGroup, selectedCommodity],
  );

  return (
    <main className="page-shell dashboard-page">
      <TopNav activeCommodityLabel={insights?.commodity ?? selectedCommodity} />

      <CommodityFilterBar
        groups={groups}
        selectedGroup={selectedGroup}
        onGroupChange={setSelectedGroup}
        commodities={commoditiesInGroup}
        selectedCommodity={selectedCommodity}
        onCommodityChange={setSelectedCommodity}
      />

      {insights ? (
        <>
          <section className="overview-shell">
            <HeroCanvas
              insights={insights}
              group={selectedGroup}
              lastUpdated={summary.updatedAt}
            />
            <div className="overview-aside">
              <div className="metric-card feature-card">
                <span className="metric-label">Spotlight recommendation</span>
                <strong>{insights.recommendationLabel}</strong>
                <p>{insights.recommendationRationale}</p>
              </div>
              <div className="metric-grid compact">
                <div className="metric-card">
                  <span className="metric-label">Reference price</span>
                  <strong>
                    {formatCurrency(insights.latestReferencePrice)}
                  </strong>
                </div>
                <div className="metric-card">
                  <span className="metric-label">MSP floor</span>
                  <strong>{formatCurrency(insights.latestMsp)}</strong>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Trend</span>
                  <strong>{insights.priceTrend}</strong>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Coverage</span>
                  <strong>{insights.seasonAvailability}</strong>
                </div>
              </div>
            </div>
          </section>

          <MSPComparisonRail insights={insights} />

          <section className="dashboard-grid">
            <div className="chart-stack">
              <SeasonPriceChart records={records} />
              <SeasonArrivalChart records={records} />
            </div>
            <div className="side-stack">
              <RecommendationCard insights={insights} />
              <RiskPanel insights={insights} />
            </div>
          </section>
        </>
      ) : null}

      {/* Global overview widgets — not filtered to selected commodity */}
      <section className="dashboard-grid lower">
        <MarketPulseFeed events={summary.pulseEvents} />
        <article className="card feature">
          <span className="card-label">Alert stack</span>
          <h3>Commodity pressure points</h3>
          <p className="card-copy">
            Signals are grouped by price pressure, momentum, and coverage risk.
          </p>
          <AlertSeverityStack alerts={summary.alerts} />
        </article>
      </section>

      <section className="directory-shell">
        <div className="section-heading">
          <div>
            <span className="section-kicker">Commodity routes</span>
            <h2>Open a dedicated commodity detail page.</h2>
          </div>
          {insights ? (
            <TrendArrowBadge
              direction={insights.priceTrend}
              changePct={insights.trendChangePct}
            />
          ) : null}
        </div>
        <div className="commodity-card-grid">
          {summary.movers.map((card) => {
            const riskClass =
              card.riskLevel === "High"
                ? "risk-high"
                : card.riskLevel === "Watch"
                  ? "risk-watch"
                  : "risk-low";
            return (
              <Link
                className={`commodity-link-card ${riskClass}`}
                key={card.slug}
                href={`/commodity/${card.slug}`}
              >
                <span className="micro-label">{card.group}</span>
                <h3>{card.commodity}</h3>
                <p>
                  {card.recommendationLabel} · {card.seasonAvailability}
                </p>
                <div className="commodity-link-meta">
                  <span>{card.latestSeason}</span>
                  <span
                    className={
                      card.latestDeltaPct >= 0 ? "positive" : "negative"
                    }
                  >
                    {card.latestDeltaPct >= 0 ? "+" : ""}
                    {(card.latestDeltaPct * 100).toFixed(1)}%
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      </section>
    </main>
  );
}
