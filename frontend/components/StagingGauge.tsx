"use client";

import { useTranslations } from "next-intl";

type Props = {
  sellPct: number;
  holdPct: number;
};

export function StagingGauge({ sellPct, holdPct }: Props) {
  const t = useTranslations("rec");
  return (
    <div className="staging-gauge">
      <div className="sg-bar">
        <div
          className="sg-sell"
          style={{ width: `${sellPct}%` }}
          title={`${t("sellNow")} ${sellPct}%`}
        />
        <div
          className="sg-hold"
          style={{ width: `${holdPct}%` }}
          title={`${t("holdLabel")} ${holdPct}%`}
        />
      </div>
      <div className="sg-legend">
        <span className="sg-sell-label">
          <span className="sg-dot sell" />
          {t("sellNow")} {sellPct}%
        </span>
        <span className="sg-hold-label">
          <span className="sg-dot hold" />
          {t("holdLabel")} {holdPct}%
        </span>
      </div>
    </div>
  );
}
