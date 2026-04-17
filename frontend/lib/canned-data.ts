import payload from "../../crop_data/season_report_summary.json";

export type SeasonPriceRecord = {
  season_year: string;
  commodity_group: string;
  commodity: string;
  msp: number | null;
  kharif_price: number | null;
  kharif_arrival_tonnes: number | null;
  rabi_price: number | null;
  rabi_arrival_tonnes: number | null;
  source_file: string;
};

export type CommodityInsightSummary = {
  commodity: string;
  latestSeason: string;
  latestMsp: number | null;
  latestReferencePrice: number | null;
  latestDelta: number;
  latestDeltaLabel: string;
  highestSeason: string;
  highestPriceLabel: string;
};

type Point = {
  x: number;
  y: number;
  label: string;
  value: number;
};

type ChartConfig = {
  width: number;
  height: number;
  padding: number;
  min: number;
  max: number;
};

type NumericField = "msp" | "kharif_price" | "rabi_price";

const records = payload.records as SeasonPriceRecord[];

export function getCommodityGroups() {
  return Array.from(new Set(records.map((record) => record.commodity_group))).sort();
}

export function getCommoditiesForGroup(group: string) {
  return Array.from(
    new Set(
      records
        .filter((record) => record.commodity_group === group)
        .map((record) => record.commodity),
    ),
  ).sort();
}

export function getCommoditySeries(group: string, commodity: string) {
  return records
    .filter(
      (record) =>
        record.commodity_group === group && record.commodity === commodity,
    )
    .sort((left, right) => left.season_year.localeCompare(right.season_year));
}

export function getCommodityInsights(group: string, commodity: string): CommodityInsightSummary | null {
  const series = getCommoditySeries(group, commodity);
  if (series.length === 0) {
    return null;
  }

  const latest = series[series.length - 1];
  const latestReferencePrice = latest.kharif_price ?? latest.rabi_price ?? null;
  const latestMsp = latest.msp ?? null;
  const latestDelta =
    latestReferencePrice !== null && latestMsp !== null
      ? latestReferencePrice - latestMsp
      : 0;

  const pricedSeries = series
    .map((record) => ({
      season: record.season_year,
      value: record.kharif_price ?? record.rabi_price,
    }))
    .filter((item): item is { season: string; value: number } => item.value !== null)
    .sort((left, right) => right.value - left.value);

  const highest = pricedSeries[0] ?? { season: latest.season_year, value: latestReferencePrice ?? 0 };

  return {
    commodity,
    latestSeason: latest.season_year,
    latestMsp,
    latestReferencePrice,
    latestDelta,
    latestDeltaLabel:
      latestReferencePrice === null || latestMsp === null
        ? "No comparable price"
        : `${latestDelta >= 0 ? "+" : ""}${formatCurrency(latestDelta)} vs MSP`,
    highestSeason: highest.season,
    highestPriceLabel: formatCurrency(highest.value),
  };
}

export function formatCurrency(value: number | null) {
  if (value === null) {
    return "N/A";
  }

  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatTonnes(value: number | null) {
  if (value === null) {
    return "N/A";
  }

  return `${new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: 2,
  }).format(value)} t`;
}

export function pointSeries(
  series: SeasonPriceRecord[],
  field: NumericField,
  config: ChartConfig,
) {
  return series
    .map((record, index) => {
      const value = record[field];
      if (value === null) {
        return null;
      }

      const x =
        config.padding +
        (index * (config.width - config.padding * 2)) /
          Math.max(series.length - 1, 1);
      const scale = (value - config.min) / Math.max(config.max - config.min, 1);
      const y = config.height - config.padding - scale * (config.height - config.padding * 2);

      return {
        x,
        y,
        label: record.season_year,
        value,
      } satisfies Point;
    })
    .filter((point): point is Point => point !== null);
}

export function buildLinePath(points: Point[]) {
  if (points.length === 0) {
    return "";
  }

  return points
    .map((point, index) =>
      `${index === 0 ? "M" : "L"} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`,
    )
    .join(" ");
}
