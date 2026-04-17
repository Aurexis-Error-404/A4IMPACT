import {
  SeasonPriceRecord,
  buildLinePath,
  formatCurrency,
  pointSeries,
} from "../lib/canned-data";

type Props = {
  records: SeasonPriceRecord[];
};

export function SeasonPriceChart({ records }: Props) {
  const width = 760;
  const height = 280;
  const padding = 28;

  const series = [
    { key: "msp", color: "#0f766e", label: "MSP" },
    { key: "kharif_price", color: "#bc6c25", label: "Kharif price" },
    { key: "rabi_price", color: "#4338ca", label: "Rabi price" },
  ] as const;

  const allValues = records.flatMap((record) => [
    record.msp,
    record.kharif_price,
    record.rabi_price,
  ]).filter((value): value is number => value !== null);

  const min = Math.min(...allValues);
  const max = Math.max(...allValues);

  return (
    <article className="chart-card">
      <p className="card-label">Season price view</p>
      <h3>Price trajectory across seasons</h3>
      <p className="card-copy">
        MSP, Kharif price, and Rabi price are plotted together so the spread is
        visible at a glance.
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
        <svg viewBox={`0 0 ${width} ${height}`} width="100%" role="img" aria-label="Season price chart">
          <rect x="0" y="0" width={width} height={height} rx="24" fill="#fff9ef" />
          {records.map((record, index) => {
            const x = padding + (index * (width - padding * 2)) / Math.max(records.length - 1, 1);
            return (
              <g key={record.season_year}>
                <line
                  x1={x}
                  x2={x}
                  y1={padding}
                  y2={height - padding}
                  stroke="rgba(106, 78, 38, 0.1)"
                />
                <text x={x} y={height - 8} textAnchor="middle" fill="#6a5738" fontSize="12">
                  {record.season_year}
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
            return (
              <g key={item.key}>
                <path
                  d={buildLinePath(points)}
                  fill="none"
                  stroke={item.color}
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                {points.map((point) => (
                  <g key={`${item.key}-${point.label}`}>
                    <circle cx={point.x} cy={point.y} r="4.5" fill={item.color} />
                    <title>{`${item.label} • ${point.label} • ${formatCurrency(point.value)}`}</title>
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
