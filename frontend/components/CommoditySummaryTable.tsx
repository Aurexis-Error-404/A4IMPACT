"use client";

import { useTranslations } from "next-intl";
import {
  SeasonPriceRecord,
  formatCurrency,
  formatTonnes,
} from "../lib/canned-data";

type Props = {
  records: SeasonPriceRecord[];
};

export function CommoditySummaryTable({ records }: Props) {
  const t = useTranslations("summaryTable");
  return (
    <article className="card">
      <span className="card-label">{t("label")}</span>
      <h3>{t("title")}</h3>
      <p className="card-copy">{t("desc")}</p>
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
              {(["season", "msp", "kharifPrice", "kharifArrival", "rabiPrice", "rabiArrival"] as const).map(
                (key) => (
                  <th
                    key={key}
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
                    {t(key)}
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
