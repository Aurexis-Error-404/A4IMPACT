import { CommodityInsightSummary } from "../lib/canned-data";

type Props = {
  insights: CommodityInsightSummary | null;
};

export function InsightCards({ insights }: Props) {
  if (!insights) {
    return null;
  }

  return (
    <section className="insight-grid">
      <div className="mini-stat">
        <span>Latest season</span>
        <strong>{insights.latestSeason}</strong>
      </div>
      <div className="mini-stat">
        <span>Price vs MSP</span>
        <strong>{insights.latestDeltaLabel}</strong>
      </div>
      <div className="mini-stat">
        <span>Best season</span>
        <strong>{insights.highestSeason}</strong>
      </div>
      <div className="mini-stat">
        <span>Peak price</span>
        <strong>{insights.highestPriceLabel}</strong>
      </div>
    </section>
  );
}
