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
  fetchCommodityInsights,
  fetchCommoditySeries,
  fetchDashboardSummary,
} from "../../lib/api";
import { formatCurrency } from "../../lib/canned-data";
import type {
  AlertItem,
  CommodityCardSummary,
  CommodityInsightSummary,
  PulseEvent,
  SeasonPriceRecord,
} from "../../lib/canned-data";

type DashState = {
  groups: string[];
  allInsights: CommodityInsightSummary[];
  movers: CommodityCardSummary[];
  alerts: AlertItem[];
  pulseEvents: PulseEvent[];
};

export default function DashboardPage() {
  const [dash, setDash] = useState<DashState | null>(null);
  const [selectedGroup, setSelectedGroup] = useState("");
  const [selectedCommodity, setSelectedCommodity] = useState("");
  const [insights, setInsights] = useState<CommodityInsightSummary | null>(null);
  const [records, setRecords] = useState<SeasonPriceRecord[]>([]);
  const [insightsLoading, setInsightsLoading] = useState(false);

  // Initial load — fetch all data from backend
  useEffect(() => {
    fetchDashboardSummary().then((summary) => {
      const allInsights: CommodityInsightSummary[] = [];
      const groups: string[] = [];
      for (const card of summary.movers) {
        if (!groups.includes(card.group)) groups.push(card.group);
      }
      setDash({
        groups: Array.from(new Set([...summary.movers.map((c) => c.group)])),
        allInsights,
        movers: summary.movers,
        alerts: summary.alerts,
        pulseEvents: summary.pulseEvents,
      });
      if (summary.spotlight) {
        setSelectedGroup(summary.spotlight.group);
        setSelectedCommodity(summary.spotlight.commodity);
      }
    });
  }, []);

  // Fetch all insights once groups are known, to power the filter bar commodity list
  const [allInsightsList, setAllInsightsList] = useState<CommodityInsightSummary[]>([]);
  useEffect(() => {
    if (!dash) return;
    // We already get movers but need all 14 for filter bar — reuse fetchDashboardSummary data
    // which includes movers; we derive groups/commodities from backend via summary.movers
  }, [dash]);

  // Commodity list for selected group (derived from movers + extra backend calls)
  const commoditiesInGroup = useMemo(() => {
    if (!dash) return [];
    return dash.movers
      .filter((c) => c.group === selectedGroup)
      .map((c) => c.commodity);
  }, [dash, selectedGroup]);

  const groups = useMemo(() => {
    if (!dash) return [];
    return Array.from(new Set(dash.movers.map((c) => c.group)));
  }, [dash]);

  // Repair selected commodity when group changes
  useEffect(() => {
    if (!commoditiesInGroup.length) return;
    if (!commoditiesInGroup.includes(selectedCommodity)) {
      setSelectedCommodity(commoditiesInGroup[0]);
    }
  }, [selectedGroup, commoditiesInGroup, selectedCommodity]);

  // Fetch insights + records when selected commodity changes
  useEffect(() => {
    if (!selectedGroup || !selectedCommodity) return;
    setInsightsLoading(true);
    Promise.all([
      fetchCommodityInsights(selectedGroup, selectedCommodity),
      fetchCommoditySeries(selectedGroup, selectedCommodity),
    ])
      .then(([ins, rec]) => {
        setInsights(ins);
        setRecords(rec);
      })
      .finally(() => setInsightsLoading(false));
  }, [selectedGroup, selectedCommodity]);

  if (!dash) {
    return (
      <main className="page-shell dashboard-page">
        <TopNav />
        <div className="dash-loading">
          <div className="dash-loading-spinner" />
          <p>Loading commodity intelligence…</p>
        </div>
      </main>
    );
  }

  return (
    <main className="page-shell dashboard-page">
      <TopNav activeCommodityLabel={insights?.commodity ?? selectedCommodity} />

      <CommodityFilterBar
        groups={groups}
        selectedGroup={selectedGroup}
        onGroupChange={(g) => {
          setSelectedGroup(g);
        }}
        commodities={commoditiesInGroup}
        selectedCommodity={selectedCommodity}
        onCommodityChange={setSelectedCommodity}
      />

      {insightsLoading ? (
        <div className="dash-loading inline">
          <div className="dash-loading-spinner" />
          <p>Loading {selectedCommodity}…</p>
        </div>
      ) : insights ? (
        <>
          <section className="overview-shell">
            <HeroCanvas
              insights={insights}
              group={selectedGroup}
              lastUpdated="Season sync active"
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
                  <strong>{formatCurrency(insights.latestReferencePrice)}</strong>
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

      <section className="dashboard-grid lower">
        <MarketPulseFeed events={dash.pulseEvents} />
        <article className="card feature">
          <span className="card-label">Alert stack</span>
          <h3>Commodity pressure points</h3>
          <p className="card-copy">
            Signals are grouped by price pressure, momentum, and coverage risk.
          </p>
          <AlertSeverityStack alerts={dash.alerts} />
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
          {dash.movers.map((card) => {
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
                  <span className={card.latestDeltaPct >= 0 ? "positive" : "negative"}>
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
