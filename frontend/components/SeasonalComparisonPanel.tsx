"use client";

import { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import {
  CommodityInsightSummary,
  SeasonPriceRecord,
  formatTonnes,
} from "../lib/canned-data";
import { SeasonSplitBar } from "./SeasonSplitBar";

type Props = {
  records: SeasonPriceRecord[];
  insights: CommodityInsightSummary;
};

export function SeasonalComparisonPanel({ records, insights }: Props) {
  const t = useTranslations("seasonalComparison");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const id = requestAnimationFrame(() => setMounted(true));
    return () => cancelAnimationFrame(id);
  }, [records]);

  const arrivalValues = records
    .flatMap((record) => [
      record.kharif_arrival_tonnes,
      record.rabi_arrival_tonnes,
    ])
    .filter((value): value is number => value !== null);
  const maxArrival = Math.max(...arrivalValues, 1);

  return (
    <article className="card feature">
      <span className="card-label">{t("label")}</span>
      <h3>{t("title")}</h3>
      <p className="card-copy">{t("desc")}</p>
      <SeasonSplitBar
        kharifShare={insights.kharifShare}
        rabiShare={insights.rabiShare}
      />
      <div className="comparison-mini-stack">
        {records.map((record) => {
          const kharifWidth = ((record.kharif_arrival_tonnes ?? 0) / maxArrival) * 100;
          const rabiWidth = ((record.rabi_arrival_tonnes ?? 0) / maxArrival) * 100;

          return (
            <div key={record.season_year}>
              <div className="arrival-row-meta">
                <span>{record.season_year}</span>
                <span>
                  K {formatTonnes(record.kharif_arrival_tonnes)} - R{" "}
                  {formatTonnes(record.rabi_arrival_tonnes)}
                </span>
              </div>
              <div className="comparison-track">
                <div
                  className="comparison-fill kharif"
                  style={{ width: mounted ? `${kharifWidth}%` : "0%" }}
                />
                <div
                  className="comparison-fill rabi"
                  style={{ width: mounted ? `${rabiWidth}%` : "0%" }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </article>
  );
}
