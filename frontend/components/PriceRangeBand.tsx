"use client";

import { useTranslations } from "next-intl";

type Props = {
  floor: number;
  ceiling: number;
  current: number | null;
  basis: string;
};

export function PriceRangeBand({ floor, ceiling, current, basis }: Props) {
  const t = useTranslations("insights");
  const span = ceiling - floor;
  const currentPct =
    current != null && span > 0
      ? Math.min(100, Math.max(0, ((current - floor) / span) * 100))
      : null;

  return (
    <div className="price-range-band">
      <div className="prb-header">
        <span className="prb-label">{t("expectedRange")}</span>
        <span className="prb-basis mono">{basis}</span>
      </div>
      <div className="prb-track">
        <div className="prb-fill" />
        {currentPct != null && (
          <div
            className="prb-marker"
            style={{ left: `${currentPct}%` }}
            title={`Current Rs.${current?.toLocaleString("en-IN")}`}
          />
        )}
      </div>
      <div className="prb-labels">
        <span className="prb-end">
          {t("floor")} Rs.{floor.toLocaleString("en-IN")}
        </span>
        <span className="prb-end">
          {t("ceiling")} Rs.{ceiling.toLocaleString("en-IN")}
        </span>
      </div>
    </div>
  );
}
