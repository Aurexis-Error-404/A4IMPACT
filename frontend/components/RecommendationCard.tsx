"use client";

import { CommodityInsightSummary } from "../lib/canned-data";

type Props = {
  insights: CommodityInsightSummary;
};

export function RecommendationCard({ insights }: Props) {
  return (
    <article className="rec-card refresh-fade" key={insights.commodity}>
      <span className="rec-label">AI recommendation</span>
      <h3 className="rec-headline">{insights.recommendationLabel}</h3>
      <span className="rec-confidence">{insights.confidenceLabel}</span>
      <p className="rec-rationale">{insights.recommendationRationale}</p>
    </article>
  );
}
