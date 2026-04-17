"use client";

import { useTranslations } from "next-intl";
import { CommodityInsightSummary, formatCurrency } from "../lib/canned-data";
import { TrendArrowBadge } from "./TrendArrowBadge";

type Props = {
  insights: CommodityInsightSummary | null;
  group: string;
  lastUpdated: string;
};

export function HeroCanvas({ insights, group, lastUpdated }: Props) {
  const t = useTranslations("hero");
  const tr = useTranslations("risk");

  if (!insights) {
    return (
      <section className="hero-canvas">
        <div className="hero-content">
          <div>
            <span className="hero-eyebrow">{t("intelligenceLabel")}</span>
            <h1 className="hero-headline">{t("selectPrompt")}</h1>
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
          <span className="hero-eyebrow">{t("seasonal")} - {group}</span>
          <h1 className="hero-headline">{insights.commodity}</h1>
          <p className="hero-sub">{t("tagline")}</p>
          <div className="hero-status">
            <span className={`chip ${riskChip}`}>
              <span className="dot" />
              {t("riskPrefix")} - {tr(insights.riskLevel as Parameters<typeof tr>[0])}
            </span>
            <span className="chip teal">
              <span className="dot" />
              {insights.seasonAvailability}
            </span>
            <span className="chip">
              <span className="dot" />
              {t("latestSeason")} {insights.latestSeason}
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
            {t("refreshed")} {lastUpdated}
          </span>
        </div>
      </div>
      <aside className="hero-aside">
        <span className="big-label">{t("refPrice")} - {insights.latestSeason}</span>
        <span className="big-number mono">
          {formatCurrency(insights.latestReferencePrice)}
        </span>
        <div className="split">
          <div className="stat">
            <span className="big-label">{tr("mspFloor")}</span>
            <span className="val mono">{formatCurrency(insights.latestMsp)}</span>
          </div>
          <div className="stat">
            <span className="big-label">{t("vsMsp")}</span>
            <span className="val mono">
              {insights.latestDeltaPct > 0 ? "+" : insights.latestDeltaPct < 0 ? "−" : ""}
              {(Math.abs(insights.latestDeltaPct) * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      </aside>
    </section>
  );
}
