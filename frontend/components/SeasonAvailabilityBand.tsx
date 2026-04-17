"use client";

import { SeasonAvailability } from "../lib/canned-data";

type Props = {
  availability: SeasonAvailability;
};

const STATES: SeasonAvailability[] = ["Kharif only", "Rabi only", "Both", "Sparse"];

export function SeasonAvailabilityBand({ availability }: Props) {
  return (
    <div className="availability-band">
      <span className="tag">Season availability</span>
      <span className="pills">
        {STATES.map((s) => (
          <span key={s} className={`pill ${s === availability ? "on" : ""}`}>
            {s}
          </span>
        ))}
      </span>
    </div>
  );
}
