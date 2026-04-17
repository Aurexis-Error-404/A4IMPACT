"use client";

import { useEffect, useState } from "react";
import { fetchAIRecommendation } from "../lib/api";
import { RecommendationCard } from "./RecommendationCard";
import type { CommodityInsightSummary } from "../lib/canned-data";

type Props = {
  commodity: string;
  basicInsights: CommodityInsightSummary;
};

export function AIRecommendationSection({ commodity, basicInsights }: Props) {
  const [aiInsights, setAiInsights] = useState<CommodityInsightSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    setLoading(true);
    setError(false);
    setAiInsights(null);

    fetchAIRecommendation(commodity)
      .then(setAiInsights)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [commodity]);

  if (loading) {
    return <RecommendationCard insights={basicInsights} loading />;
  }

  if (error || !aiInsights) {
    return <RecommendationCard insights={basicInsights} />;
  }

  return <RecommendationCard insights={aiInsights} />;
}
