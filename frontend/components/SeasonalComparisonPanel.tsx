"use client";

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
  const arrivalValues = records
    .flatMap((record) => [
      record.kharif_arrival_tonnes,
      record.rabi_arrival_tonnes,
    ])
    .filter((value): value is number => value !== null);
  const maxArrival = Math.max(...arrivalValues, 1);

  return (
    <article className="card feature">
      <span className="card-label">Seasonal comparison</span>
      <h3>Kharif vs Rabi mix</h3>
      <p className="card-copy">
        Coverage split and arrival intensity across observed seasons.
      </p>
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
                  style={{ width: `${kharifWidth}%` }}
                />
                <div
                  className="comparison-fill rabi"
                  style={{ width: `${rabiWidth}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </article>
  );
}
