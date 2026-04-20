"use client";

import Link from "next/link";
import { useState, useMemo, useEffect, useCallback } from "react";
import { useTranslations } from "next-intl";
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
import { PriceRangeBand } from "../../components/PriceRangeBand";
import { DeltaHistorySparkline } from "../../components/DeltaHistorySparkline";
import { TrendArrowBadge } from "../../components/TrendArrowBadge";
import { DebatePanel } from "../../components/DebatePanel";
import { QuickProfitCalc } from "../../components/QuickProfitCalc";
import VoiceButton from "../../components/VoiceButton";
import { CommodityComparisonPanel } from "../../components/CommodityComparisonPanel";
import { AlertBanner } from "../../components/AlertBanner";
import type { DebateAlertEvent } from "../../components/AlertBanner";
import { useFavourites } from "../../hooks/useFavourites";
import {
  fetchAllCommodityPairs,
  fetchCommodityInsights,
  fetchCommodityCards,
  fetchCommoditySeries,
  fetchDashboardSummary,
  fetchAIRecommendation,
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
  movers: CommodityCardSummary[];
  alerts: AlertItem[];
  pulseEvents: PulseEvent[];
  offline: boolean;
};

type Pair = { group: string; commodity: string; slug: string };

export default function DashboardPage() {
  const t = useTranslations("dashboard");
  const [dash, setDash] = useState<DashState | null>(null);
  const [allPairs, setAllPairs] = useState<Pair[]>([]);
  const [allCards, setAllCards] = useState<CommodityCardSummary[]>([]);
  const [selectedGroup, setSelectedGroup] = useState("");
  const [selectedCommodity, setSelectedCommodity] = useState("");
  const [insights, setInsights] = useState<CommodityInsightSummary | null>(null);
  const [records, setRecords] = useState<SeasonPriceRecord[]>([]);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [aiRec, setAiRec] = useState<CommodityInsightSummary | null>(null);
  const [recLoading, setRecLoading] = useState(false);
  const [debateOpen, setDebateOpen] = useState(false);
  const [liveAlerts, setLiveAlerts] = useState<DebateAlertEvent[]>([]);
  const [comparisonInsights, setComparisonInsights] = useState<Record<string, CommodityInsightSummary>>({});
  const [loadError, setLoadError] = useState(false);
  const { favourites, toggle: toggleFavourite, isFavourite } = useFavourites();

  useEffect(() => {
    Promise.all([fetchDashboardSummary(), fetchAllCommodityPairs(), fetchCommodityCards()])
      .then(([summary, pairs, cards]) => {
        setAllPairs(pairs);
        setAllCards(cards);
        setDash({
          movers: summary.movers,
          alerts: summary.alerts,
          pulseEvents: summary.pulseEvents,
          offline: summary.dataMode === "canned",
        });
        if (summary.spotlight) {
          setSelectedGroup(summary.spotlight.group);
          setSelectedCommodity(summary.spotlight.commodity);
        } else if (pairs.length) {
          setSelectedGroup(pairs[0].group);
          setSelectedCommodity(pairs[0].commodity);
        }
      })
      .catch((err) => {
        console.error("Dashboard load failed:", err);
        setLoadError(true);
      });
  }, []);

  const handleRequestComparisonInsights = useCallback((slug: string) => {
    const pair = allPairs.find((p) => p.slug === slug);
    if (!pair) return;
    fetchCommodityInsights(pair.group, pair.commodity).then((ins) => {
      setComparisonInsights((prev) => ({ ...prev, [slug]: ins }));
    }).catch(() => {});
  }, [allPairs]);

  const groups = useMemo(
    () => [...new Set(allPairs.map((p) => p.group))],
    [allPairs],
  );

  const commoditiesInGroup = useMemo(
    () => allPairs.filter((p) => p.group === selectedGroup).map((p) => p.commodity),
    [allPairs, selectedGroup],
  );

  // Fetch insights + records when selected commodity changes.
  // cancelled flag prevents stale responses from a previous selection overwriting
  // the current one when the user switches commodities before the fetch completes.
  useEffect(() => {
    if (!selectedGroup || !selectedCommodity) return;
    let cancelled = false;
    setInsightsLoading(true);
    setRecLoading(true);
    setAiRec(null);
    Promise.all([
      fetchCommodityInsights(selectedGroup, selectedCommodity),
      fetchCommoditySeries(selectedGroup, selectedCommodity),
    ])
      .then(([ins, rec]) => {
        if (cancelled) return;
        setInsights(ins);
        setRecords(rec);
        setInsightsLoading(false);

        fetchAIRecommendation(selectedCommodity)
          .then((aiData) => { if (!cancelled) setAiRec(aiData); })
          .catch((err) => { if (!cancelled) console.error("AI fetch error:", err); })
          .finally(() => { if (!cancelled) setRecLoading(false); });
      })
      .catch((err) => {
        if (!cancelled) {
          console.error(err);
          setInsightsLoading(false);
          setRecLoading(false);
        }
      });
    return () => { cancelled = true; };
  }, [selectedGroup, selectedCommodity]);

  if (loadError) {
    return (
      <main className="page-shell dashboard-page">
        <TopNav />
        <div className="dash-loading">
          <p>{t("loadError")}</p>
        </div>
      </main>
    );
  }

  if (!dash) {
    return (
      <main className="page-shell dashboard-page">
        <TopNav />
        <div className="dash-loading">
          <div className="dash-loading-spinner" />
          <p>{t("loading")}</p>
        </div>
      </main>
    );
  }

  return (
    <main className="page-shell dashboard-page">
      <AlertBanner
        alerts={liveAlerts}
        onDismiss={(i) => setLiveAlerts((prev) => prev.filter((_, idx) => idx !== i))}
      />

      <TopNav activeCommodityLabel={insights?.commodity ?? selectedCommodity} />

      {dash.offline && (
        <div style={{
          background: "rgba(255,180,0,0.12)",
          border: "1px solid rgba(255,180,0,0.4)",
          borderRadius: "8px",
          padding: "8px 14px",
          fontSize: "12px",
          color: "var(--gold, #f0b429)",
          marginBottom: "4px",
        }}>
          Offline mode — showing cached data. Start the backend at localhost:8000 for live AI insights.
        </div>
      )}

      <div style={{ position: "relative", display: "flex", alignItems: "center", gap: "10px" }}>
        <CommodityFilterBar
          groups={groups}
          selectedGroup={selectedGroup}
          onGroupChange={(newGroup) => {
            const first = allPairs.find((p) => p.group === newGroup)?.commodity ?? "";
            setSelectedGroup(newGroup);
            setSelectedCommodity(first);
          }}
          commodities={commoditiesInGroup}
          selectedCommodity={selectedCommodity}
          onCommodityChange={setSelectedCommodity}
          allPairs={allPairs}
          onCropSelect={(group, commodity) => {
            setSelectedGroup(group);
            setSelectedCommodity(commodity);
          }}
        />
        {selectedCommodity && (
          <button
            onClick={() => setDebateOpen(true)}
            style={{
              background: "linear-gradient(135deg, rgba(127,119,221,0.25), rgba(127,119,221,0.12))",
              border: "1px solid rgba(127,119,221,0.5)",
              color: "var(--violet)",
              borderRadius: "10px",
              padding: "12px 26px",
              fontSize: "15px",
              fontWeight: 600,
              cursor: "pointer",
              whiteSpace: "nowrap",
              letterSpacing: "0.02em",
              flexShrink: 0,
            }}
          >
            ⚡ Live Debate
          </button>
        )}
      </div>

      <DebatePanel
        commodity={selectedCommodity}
        open={debateOpen}
        onClose={() => setDebateOpen(false)}
        onAlert={(ev) => setLiveAlerts((prev) => [...prev, ev])}
      />

      {insightsLoading ? (
        <div className="dash-loading inline">
          <div className="dash-loading-spinner" />
          <p>{t("loadingCommodity", { commodity: selectedCommodity })}</p>
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
              <div className="metric-grid compact">
                <div className="metric-card">
                  <span className="metric-label">{t("referencePrice")}</span>
                  <strong>{formatCurrency(insights.latestReferencePrice)}</strong>
                </div>
                <div className="metric-card">
                  <span className="metric-label">{t("mspFloor")}</span>
                  <strong>{formatCurrency(insights.latestMsp)}</strong>
                </div>
                <div className="metric-card">
                  <span className="metric-label">{t("trend")}</span>
                  <strong>{insights.priceTrend}</strong>
                  {(aiRec ?? insights).deltaPctHistory && (
                    <DeltaHistorySparkline history={(aiRec ?? insights).deltaPctHistory!} />
                  )}
                </div>
                <div className="metric-card">
                  <span className="metric-label">{t("coverage")}</span>
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
              <RecommendationCard insights={aiRec ?? insights} loading={recLoading} />
              <QuickProfitCalc insights={aiRec ?? insights} />
              <RiskPanel insights={insights} />
              <VoiceButton />
              {(aiRec ?? insights).expectedPriceRange && (() => {
                const r = (aiRec ?? insights).expectedPriceRange!;
                return (
                  <PriceRangeBand
                    floor={r.floor}
                    ceiling={r.ceiling}
                    current={insights.latestReferencePrice}
                    basis={r.basis}
                  />
                );
              })()}
            </div>
          </section>
        </>
      ) : null}

      <section className="dashboard-grid lower">
        <MarketPulseFeed events={dash.pulseEvents} />
        <article className="card feature">
          <span className="card-label">Alert stack</span>
          <h3>{t("pressurePointsTitle")}</h3>
          <p className="card-copy">
            {t("pressurePointsDesc")}
          </p>
          <AlertSeverityStack alerts={dash.alerts} />
        </article>
      </section>

      <section className="directory-shell">
        <div className="section-heading">
          <div>
            <span className="section-kicker">{t("routesKicker")}</span>
            <h2>{t("routesTitle")}</h2>
          </div>
          {insights ? (
            <TrendArrowBadge
              direction={insights.priceTrend}
              changePct={insights.trendChangePct}
            />
          ) : null}
        </div>

        {favourites.length > 0 && (
          <div style={{ marginBottom: "20px" }}>
            <span className="section-kicker" style={{ marginBottom: "8px", display: "block" }}>
              My crops
            </span>
            <div className="commodity-card-grid">
              {allCards.filter((c) => isFavourite(c.slug)).map((card) => {
                const riskClass = card.riskLevel === "High" ? "risk-high" : card.riskLevel === "Watch" ? "risk-watch" : "risk-low";
                return (
                  <div key={card.slug} style={{ position: "relative" }}>
                    <button
                      onClick={() => toggleFavourite(card.slug)}
                      title="Remove from My Crops"
                      style={{ position: "absolute", top: "8px", right: "8px", background: "none", border: "none", cursor: "pointer", fontSize: "16px", zIndex: 1, lineHeight: 1 }}
                    >
                      ★
                    </button>
                    <Link className={`commodity-link-card ${riskClass}`} href={`/commodity/${card.slug}`}>
                      <span className="micro-label">{card.group}</span>
                      <h3>{card.commodity}</h3>
                      <p>{card.recommendationLabel} · {card.seasonAvailability}</p>
                      <div className="commodity-link-meta">
                        <span>{card.latestSeason}</span>
                        <span className={card.latestDeltaPct >= 0 ? "positive" : "negative"}>
                          {card.latestDeltaPct >= 0 ? "+" : ""}{(card.latestDeltaPct * 100).toFixed(1)}%
                        </span>
                      </div>
                    </Link>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <div className="commodity-card-grid">
          {dash.movers.map((card) => {
            const riskClass =
              card.riskLevel === "High"
                ? "risk-high"
                : card.riskLevel === "Watch"
                  ? "risk-watch"
                  : "risk-low";
            return (
              <div key={card.slug} style={{ position: "relative" }}>
                <button
                  onClick={() => toggleFavourite(card.slug)}
                  title={isFavourite(card.slug) ? "Remove from My Crops" : "Add to My Crops"}
                  style={{
                    position: "absolute", top: "8px", right: "8px",
                    background: "none", border: "none", cursor: "pointer",
                    fontSize: "16px", zIndex: 1, lineHeight: 1,
                    color: isFavourite(card.slug) ? "var(--gold, #f0b429)" : "var(--muted)",
                  }}
                >
                  {isFavourite(card.slug) ? "★" : "☆"}
                </button>
                <Link
                  className={`commodity-link-card ${riskClass}`}
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
              </div>
            );
          })}
        </div>

        {allCards.length > 0 && (
          <CommodityComparisonPanel
            allCommodities={allCards}
            insights={comparisonInsights}
            onRequestInsights={handleRequestComparisonInsights}
          />
        )}
      </section>
    </main>
  );
}
