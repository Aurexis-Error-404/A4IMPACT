"use client";

import { PulseEvent } from "../lib/canned-data";
import { useTranslations } from "next-intl";

type Props = {
  events: PulseEvent[];
};

export function MarketPulseFeed({ events }: Props) {
  const t = useTranslations("pulse");
  return (
    <article className="card">
      <span className="card-label">{t("pulseLabel")}</span>
      <h3>{t("deviationsTitle")}</h3>
      <p className="card-copy">
        {t("deviationsDesc")}
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
