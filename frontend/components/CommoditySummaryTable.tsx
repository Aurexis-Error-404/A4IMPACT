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
    <article className="table-card">
      <p className="card-label">Detailed view</p>
      <h3>Season-by-season breakdown</h3>
      <p className="card-copy">
        A compact tabular view for checking exact values across MSP, price, and
        arrivals.
      </p>
      <table>
        <thead>
          <tr>
            <th>Season</th>
            <th>MSP</th>
            <th>Kharif price</th>
            <th>Kharif arrival</th>
            <th>Rabi price</th>
            <th>Rabi arrival</th>
          </tr>
        </thead>
        <tbody>
          {records.map((record) => (
            <tr key={`${record.commodity}-${record.season_year}`}>
              <td>{record.season_year}</td>
              <td>{formatCurrency(record.msp)}</td>
              <td>{formatCurrency(record.kharif_price)}</td>
              <td>{formatTonnes(record.kharif_arrival_tonnes)}</td>
              <td>{formatCurrency(record.rabi_price)}</td>
              <td>{formatTonnes(record.rabi_arrival_tonnes)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </article>
  );
}
