"use client";

import { PulseEvent } from "../lib/canned-data";

type Props = {
  events: PulseEvent[];
};

export function MarketPulseFeed({ events }: Props) {
  return (
    <article className="card">
      <span className="card-label">Market pulse</span>
      <h3>Largest MSP deviations</h3>
      <p className="card-copy">
        Commodities ranked by how far their latest reference price sits from MSP.
      </p>
      <div className="pulse-feed stagger">
        {events.map((event) => (
          <div className="pulse-row" key={event.id}>
            <div>
              <span className="c">{event.commodity}</span>
              <span className="g">
                {event.group} - {event.label}
              </span>
            </div>
            <span className={`d ${event.delta >= 0 ? "pos" : "neg"}`}>
              {event.deltaLabel}
            </span>
            <span className="t">{event.timeAgo}</span>
          </div>
        ))}
      </div>
    </article>
  );
}
