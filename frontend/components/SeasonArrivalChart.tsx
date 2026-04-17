"use client";

import { useEffect, useState } from "react";
import { SeasonPriceRecord, formatTonnes } from "../lib/canned-data";

type Props = {
  records: SeasonPriceRecord[];
};

export function SeasonArrivalChart({ records }: Props) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(false);
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
    <article className="card">
      <span className="card-label">Season arrival view</span>
      <h3>Kharif and Rabi arrivals</h3>
      <p className="card-copy">
        Arrival volume per season, scaled against the peak observed value.
      </p>
      <div className="legend">
        <span className="legend-item">
          <span className="swatch" style={{ background: "#ef9f27" }} />
          Kharif arrival
        </span>
        <span className="legend-item">
          <span className="swatch" style={{ background: "#1d9e75" }} />
          Rabi arrival
        </span>
      </div>
      <div className="arrival-stack">
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
              <div className="arrival-bars">
                <div className="arrival-track">
                  <div
                    className="arrival-fill kharif"
                    style={{ width: mounted ? `${kharifWidth}%` : "0%" }}
                  />
                </div>
                <div className="arrival-track">
                  <div
                    className="arrival-fill rabi"
                    style={{ width: mounted ? `${rabiWidth}%` : "0%" }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </article>
  );
}
