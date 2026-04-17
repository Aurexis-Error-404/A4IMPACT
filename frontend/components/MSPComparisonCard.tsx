"use client";

import { CommodityInsightSummary, formatCurrency } from "../lib/canned-data";
import { PriceDeviationGauge } from "./PriceDeviationGauge";
import { useTranslations } from "next-intl";

type Props = {
  insights: CommodityInsightSummary | null;
};

export function MSPComparisonRail({ insights }: Props) {
  const t = useTranslations("mspComparison");
  if (!insights) return null;

  const deltaClass =
    insights.latestDelta > 0 ? "pos" : insights.latestDelta < 0 ? "neg" : "neu";

  return (
    <div className="grid-rail stagger" id="msp">
      <div className="kpi">
        <span className="kpi-label">{t("mspFloor")}</span>
        <span className="kpi-value mono">{formatCurrency(insights.latestMsp)}</span>
        <span className="kpi-sub">{insights.latestSeason}</span>
      </div>
      <div className="kpi">
        <span className="kpi-label">{t("referencePrice")}</span>
        <span className="kpi-value mono">{formatCurrency(insights.latestReferencePrice)}</span>
        <span className="kpi-sub">
          {insights.seasonAvailability === "Rabi only" ? t("rabiBasis") : t("kharifBasis")}
        </span>
      </div>
      <div className="kpi">
        <span className="kpi-label">{t("deviation")}</span>
        <span
          className="kpi-value mono"
          style={{
            color:
              deltaClass === "pos"
                ? "#c7d69d"
                : deltaClass === "neg"
                  ? "#f1b2b2"
                  : "var(--ink)",
          }}
        >
          {(insights.latestDeltaPct * 100).toFixed(1)}%
        </span>
        <span className="kpi-sub">
          {insights.latestDelta > 0 ? t("aboveMsp") : insights.latestDelta < 0 ? t("belowMsp") : t("atMsp")}
        </span>
      </div>
      <div className="kpi">
        <span className="kpi-label">{t("gauge")}</span>
        <PriceDeviationGauge deltaPct={insights.latestDeltaPct} />
      </div>
    </div>
  );
}
