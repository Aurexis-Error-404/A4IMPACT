"use client";

import { useTranslations } from "next-intl";
import { CommodityInsightSummary } from "../lib/canned-data";
import { StagingGauge } from "./StagingGauge";
import { ChannelBadge } from "./ChannelBadge";

type Props = {
  insights: CommodityInsightSummary;
  loading?: boolean;
};

export function RecommendationCard({ insights, loading = false }: Props) {
  const t = useTranslations("rec");
  const tc = useTranslations("confidence");

  if (loading) {
    return (
      <article className="rec-card rec-card--loading">
        <span className="rec-label">{t("aiLabel")}</span>
        <div className="rec-thinking">
          <div className="rec-thinking-dots">
            <span />
            <span />
            <span />
          </div>
          <p className="rec-thinking-text">{t("analysing")}</p>
        </div>
        <div className="rec-skeleton rec-skeleton--headline" />
        <div className="rec-skeleton rec-skeleton--badge" />
        <div className="rec-skeleton rec-skeleton--body" />
        <div className="rec-skeleton rec-skeleton--body rec-skeleton--short" />
      </article>
    );
  }

  const recLabel =
    t(insights.recommendationLabel as Parameters<typeof t>[0]) ?? insights.recommendationLabel;
  const confLabel =
    tc(insights.confidenceLabel as Parameters<typeof tc>[0]) ?? insights.confidenceLabel;

  return (
    <article className="rec-card refresh-fade" key={insights.commodity}>
      <span className="rec-label">{t("aiLabel")}</span>
      <h3 className="rec-headline">{recLabel}</h3>
      <span className="rec-confidence">{confLabel}</span>
      <p className="rec-rationale">{insights.recommendationRationale}</p>

      {insights.actionableTiming && (
        <div className="rec-timing-chip">
          <span className="rec-timing-icon">⏱</span>
          <span className="rec-timing-text">{insights.actionableTiming}</span>
        </div>
      )}

      {insights.conflictScore && (
        <span className={`rec-conflict-badge rec-conflict--${insights.conflictScore.toLowerCase()}`}>
          {insights.conflictScore === "LOW"
            ? "Agents agreed"
            : insights.conflictScore === "MEDIUM"
            ? "Mixed signals"
            : "Agents split"}
        </span>
      )}

      {insights.sellPctNow !== undefined && insights.holdPct !== undefined && (
        <StagingGauge sellPct={insights.sellPctNow} holdPct={insights.holdPct} />
      )}

      {insights.recommendedChannel && (
        <ChannelBadge channel={insights.recommendedChannel} />
      )}
    </article>
  );
}
