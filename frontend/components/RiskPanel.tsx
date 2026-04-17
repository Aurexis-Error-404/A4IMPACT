"use client";

import { useTranslations } from "next-intl";
import { CommodityInsightSummary, formatCurrency } from "../lib/canned-data";
import { PriceDeviationGauge } from "./PriceDeviationGauge";

type Props = {
  insights: CommodityInsightSummary;
};

export function RiskPanel({ insights }: Props) {
  const t = useTranslations("risk");
  const cls = insights.riskLevel.toLowerCase();

  return (
    <article className="card feature">
      <span className="card-label">{t("review")}</span>
      <div className="risk-headline">
        <h3>{insights.commodity}</h3>
        <span className={`risk-badge ${cls}`}>{t(insights.riskLevel as Parameters<typeof t>[0])}</span>
      </div>
      <PriceDeviationGauge deltaPct={insights.latestDeltaPct} />
      <div className="risk-panel" style={{ marginTop: 18 }}>
        <div className="risk-item">
          <span className="label">{t("latestRefPrice")}</span>
          <span className="value">{formatCurrency(insights.latestReferencePrice)}</span>
        </div>
        <div className="risk-item">
          <span className="label">{t("mspFloor")}</span>
          <span className="value">{formatCurrency(insights.latestMsp)}</span>
        </div>
        <div className="risk-item">
          <span className="label">{t("deviation")}</span>
          <span className="value">
            {(insights.latestDeltaPct * 100).toFixed(1)}%
          </span>
        </div>
        <div className="risk-item">
          <span className="label">{t("seasonCoverage")}</span>
          <span className="value">{insights.seasonAvailability}</span>
        </div>
      </div>
    </article>
  );
}
