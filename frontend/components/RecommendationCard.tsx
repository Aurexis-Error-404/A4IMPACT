"use client";

import { CommodityInsightSummary } from "../lib/canned-data";

type Props = {
  insights: CommodityInsightSummary;
  loading?: boolean;
};

export function RecommendationCard({ insights, loading = false }: Props) {
  if (loading) {
    return (
      <article className="rec-card rec-card--loading">
        <span className="rec-label">AI recommendation</span>
        <div className="rec-thinking">
          <div className="rec-thinking-dots">
            <span />
            <span />
            <span />
          </div>
          <p className="rec-thinking-text">Analysing with Groq AI…</p>
        </div>
        <div className="rec-skeleton rec-skeleton--headline" />
        <div className="rec-skeleton rec-skeleton--badge" />
        <div className="rec-skeleton rec-skeleton--body" />
        <div className="rec-skeleton rec-skeleton--body rec-skeleton--short" />
      </article>
    );
  }

  return (
    <article className="rec-card refresh-fade" key={insights.commodity}>
      <span className="rec-label">AI recommendation</span>
      <h3 className="rec-headline">{insights.recommendationLabel}</h3>
      <span className="rec-confidence">{insights.confidenceLabel}</span>
      <p className="rec-rationale">{insights.recommendationRationale}</p>
    </article>
  );
}
