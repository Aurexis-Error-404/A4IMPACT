import { CommodityInsightSummary, formatCurrency } from "../lib/canned-data";

type Props = {
  insights: CommodityInsightSummary | null;
};

export function MSPComparisonCard({ insights }: Props) {
  if (!insights) {
    return null;
  }

  const chipClass =
    insights.latestDelta > 0
      ? "delta-positive"
      : insights.latestDelta < 0
        ? "delta-negative"
        : "delta-neutral";

  return (
    <article className="summary-card">
      <p className="card-label">MSP comparison</p>
      <h3>{insights.commodity}</h3>
      <p className="card-copy">
        The latest available seasonal market price is compared against MSP using
        whichever seasonal value exists for the most recent season.
      </p>
      <div className={`delta-chip ${chipClass}`}>{insights.latestDeltaLabel}</div>
      <div className="two-column-copy" style={{ marginTop: 18 }}>
        <div className="mini-stat">
          <span>Latest reference price</span>
          <strong>{formatCurrency(insights.latestReferencePrice)}</strong>
        </div>
        <div className="mini-stat">
          <span>Latest MSP</span>
          <strong>{formatCurrency(insights.latestMsp)}</strong>
        </div>
      </div>
    </article>
  );
}
