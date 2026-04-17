"use client";

import {
  SeasonPriceRecord,
  formatCurrency,
  formatTonnes,
} from "../lib/canned-data";

type Props = {
  records: SeasonPriceRecord[];
};

export function CommoditySummaryTable({ records }: Props) {
  return (
    <article className="card">
      <span className="card-label">Detailed view</span>
      <h3>Season-by-season breakdown</h3>
      <p className="card-copy">
        Exact values across MSP, price, and arrivals for every observed season.
      </p>
      <div style={{ overflowX: "auto" }}>
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            fontFamily: "var(--font-mono)",
            fontSize: "0.88rem",
          }}
        >
          <thead>
            <tr>
              {["Season", "MSP", "Kharif price", "Kharif arrival", "Rabi price", "Rabi arrival"].map(
                (h) => (
                  <th
                    key={h}
                    style={{
                      textAlign: "left",
                      padding: "10px 12px",
                      color: "var(--muted)",
                      fontWeight: 500,
                      fontSize: "0.7rem",
                      textTransform: "uppercase",
                      letterSpacing: "0.14em",
                      borderBottom: "1px solid var(--line-strong)",
                    }}
                  >
                    {h}
                  </th>
                ),
              )}
            </tr>
          </thead>
          <tbody>
            {records.map((r) => (
              <tr key={`${r.commodity}-${r.season_year}`}>
                <td style={{ padding: "12px", borderBottom: "1px solid var(--line)", color: "var(--ink)" }}>
                  {r.season_year}
                </td>
                <td style={{ padding: "12px", borderBottom: "1px solid var(--line)" }}>
                  {formatCurrency(r.msp)}
                </td>
                <td style={{ padding: "12px", borderBottom: "1px solid var(--line)" }}>
                  {formatCurrency(r.kharif_price)}
                </td>
                <td style={{ padding: "12px", borderBottom: "1px solid var(--line)" }}>
                  {formatTonnes(r.kharif_arrival_tonnes)}
                </td>
                <td style={{ padding: "12px", borderBottom: "1px solid var(--line)" }}>
                  {formatCurrency(r.rabi_price)}
                </td>
                <td style={{ padding: "12px", borderBottom: "1px solid var(--line)" }}>
                  {formatTonnes(r.rabi_arrival_tonnes)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </article>
  );
}
