import { SeasonPriceRecord, formatTonnes } from "../lib/canned-data";

type Props = {
  records: SeasonPriceRecord[];
};

export function SeasonArrivalChart({ records }: Props) {
  const arrivalValues = records.flatMap((record) => [
    record.kharif_arrival_tonnes,
    record.rabi_arrival_tonnes,
  ]).filter((value): value is number => value !== null);

  const maxArrival = Math.max(...arrivalValues, 1);

  return (
    <article className="chart-card">
      <p className="card-label">Season arrival view</p>
      <h3>Kharif and Rabi arrivals</h3>
      <p className="card-copy">
        Arrival bars show whether a commodity appears in Kharif, Rabi, or both,
        and how heavily that season contributes to the overall record.
      </p>
      <div className="legend">
        <span className="legend-item">
          <span className="swatch" style={{ background: "#bc6c25" }} />
          Kharif arrival
        </span>
        <span className="legend-item">
          <span className="swatch" style={{ background: "#4338ca" }} />
          Rabi arrival
        </span>
      </div>
      <div style={{ display: "grid", gap: 14 }}>
        {records.map((record) => {
          const kharifWidth = ((record.kharif_arrival_tonnes ?? 0) / maxArrival) * 100;
          const rabiWidth = ((record.rabi_arrival_tonnes ?? 0) / maxArrival) * 100;

          return (
            <div key={record.season_year} className="mini-stat">
              <strong>{record.season_year}</strong>
              <span className="subtle">
                Kharif: {formatTonnes(record.kharif_arrival_tonnes)} | Rabi:{" "}
                {formatTonnes(record.rabi_arrival_tonnes)}
              </span>
              <div style={{ display: "grid", gap: 8 }}>
                <div style={{ background: "#f0e7d9", borderRadius: 999, overflow: "hidden" }}>
                  <div
                    style={{
                      width: `${kharifWidth}%`,
                      height: 12,
                      background: "#bc6c25",
                    }}
                  />
                </div>
                <div style={{ background: "#ede7ff", borderRadius: 999, overflow: "hidden" }}>
                  <div
                    style={{
                      width: `${rabiWidth}%`,
                      height: 12,
                      background: "#4338ca",
                    }}
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
