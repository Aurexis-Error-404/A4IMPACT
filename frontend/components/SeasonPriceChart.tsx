"use client";

import { useEffect, useState } from "react";
import {
  SeasonPriceRecord,
  buildLinePath,
  formatCurrency,
  pointSeries,
} from "../lib/canned-data";
import { useTranslations } from "next-intl";

type Props = {
  records: SeasonPriceRecord[];
};

export function SeasonPriceChart({ records }: Props) {
  const t = useTranslations("charts");
  const width = 760;
  const height = 280;
  const padding = 32;
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(false);
    const id = requestAnimationFrame(() => setMounted(true));
    return () => cancelAnimationFrame(id);
  }, [records]);

  const series = [
    { key: "msp" as const, color: "#d4a24c", label: t("msp") },
    { key: "kharif_price" as const, color: "#8a9a5b", label: t("kharifPrice") },
    { key: "rabi_price" as const, color: "#4fa69a", label: t("rabiPrice") },
  ];

  const allValues = records
    .flatMap((r) => [r.msp, r.kharif_price, r.rabi_price])
    .filter((v): v is number => v !== null);

  if (allValues.length === 0) {
    return (
      <article className="card">
        <span className="card-label">{t("priceView")}</span>
        <h3>{t("priceTrajectoryTitle")}</h3>
        <p className="card-copy">{t("noPriceData")}</p>
      </article>
    );
  }

  const min = Math.min(...allValues) * 0.92;
  const max = Math.max(...allValues) * 1.05;

  return (
    <article className="card feature">
      <span className="card-label">{t("priceView")}</span>
      <h3>{t("priceTrajectoryTitle")}</h3>
      <p className="card-copy">
        {t("priceTrajectoryDesc")}
      </p>
      <div className="legend">
        {series.map((item) => (
          <span className="legend-item" key={item.key}>
            <span className="swatch" style={{ background: item.color }} />
            {item.label}
          </span>
        ))}
      </div>
      <div className="chart-wrap">
        <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Season price chart">
          <defs>
            <linearGradient id="grid-fade" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0" stopColor="rgba(236,241,232,0.06)" />
              <stop offset="1" stopColor="rgba(236,241,232,0.01)" />
            </linearGradient>
          </defs>
          <rect x="0" y="0" width={width} height={height} rx="18" fill="rgba(0,0,0,0.25)" />
          {[0.25, 0.5, 0.75].map((t) => (
            <line
              key={t}
              x1={padding}
              x2={width - padding}
              y1={padding + t * (height - padding * 2)}
              y2={padding + t * (height - padding * 2)}
              stroke="rgba(236,241,232,0.06)"
              strokeDasharray="3 4"
            />
          ))}
          {records.map((r, i) => {
            const x = padding + (i * (width - padding * 2)) / Math.max(records.length - 1, 1);
            return (
              <g key={r.season_year}>
                <text
                  x={x}
                  y={height - 10}
                  textAnchor="middle"
                  fill="#8a968e"
                  fontSize="11"
                  fontFamily="var(--font-mono)"
                  letterSpacing="0.06em"
                >
                  {r.season_year}
                </text>
              </g>
            );
          })}
          {series.map((item) => {
            const points = pointSeries(records, item.key, {
              width,
              height,
              padding,
              min,
              max,
            });
            const path = buildLinePath(points);
            return (
              <g key={item.key}>
                <path
                  d={path}
                  fill="none"
                  stroke={item.color}
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  pathLength={1}
                  style={{
                    strokeDasharray: 1,
                    strokeDashoffset: mounted ? 0 : 1,
                    transition: "stroke-dashoffset 900ms cubic-bezier(0.22,1,0.36,1)",
                  }}
                />
                {points.map((p) => (
                  <g key={`${item.key}-${p.label}`}>
                    <circle
                      cx={p.x}
                      cy={p.y}
                      r="3.5"
                      fill={item.color}
                      style={{
                        opacity: mounted ? 1 : 0,
                        transition: "opacity 400ms 300ms var(--ease)",
                      }}
                    />
                    <title>{`${item.label} • ${p.label} • ${formatCurrency(p.value)}`}</title>
                  </g>
                ))}
              </g>
            );
          })}
        </svg>
      </div>
    </article>
  );
}
