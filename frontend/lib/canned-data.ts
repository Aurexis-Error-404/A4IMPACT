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

export type SeasonAvailability = "Kharif only" | "Rabi only" | "Both" | "Sparse";
export type RiskLevel = "Low" | "Watch" | "High";
export type TrendDirection = "up" | "down" | "flat";
export type RecommendationLabel = "Hold" | "Lean sell" | "Defer" | "Protect";

export type CommodityInsightSummary = {
  commodity: string;
  group: string;
  latestSeason: string;
  latestMsp: number | null;
  latestReferencePrice: number | null;
  latestDelta: number;
  latestDeltaPct: number;
  latestDeltaLabel: string;
  highestSeason: string;
  highestPriceLabel: string;
  priceTrend: TrendDirection;
  trendChangePct: number;
  seasonAvailability: SeasonAvailability;
  kharifShare: number;
  rabiShare: number;
  riskLevel: RiskLevel;
  recommendationLabel: RecommendationLabel;
  confidenceLabel: string;
  recommendationRationale: string;
  // Extended intelligence fields — optional; populated by /api/recommendation
  deltaPctHistory?: number[];
  expectedPriceRange?: { floor: number; ceiling: number; basis: string };
  recommendedChannel?: string;
  sellPctNow?: number;
  holdPct?: number;
  actionableTiming?: string;
  conflictScore?: "LOW" | "MEDIUM" | "HIGH";
};

export type AlertItem = {
  id: string;
  severity: "red" | "amber" | "green";
  commodity: string;
  group: string;
  headline: string;
  detail: string;
  season: string;
};

export type PulseEvent = {
  id: string;
  commodity: string;
  group: string;
  season: string;
  deltaLabel: string;
  delta: number;
  label: string;
  timeAgo: string;
};

export type CommodityCardSummary = {
  slug: string;
  commodity: string;
  group: string;
  latestSeason: string;
  latestReferencePrice: number | null;
  latestMsp: number | null;
  latestDeltaPct: number;
  riskLevel: RiskLevel;
  seasonAvailability: SeasonAvailability;
  recommendationLabel: RecommendationLabel;
  priceTrend: TrendDirection;
};

export type DashboardSummary = {
  dataMode: string;
  totalCommodities: number;
  totalGroups: number;
  spotlight: CommodityCardSummary | null;
  movers: CommodityCardSummary[];
  alerts: AlertItem[];
  pulseEvents: PulseEvent[];
  updatedAt: string;
};

export type CommodityDetailModel = {
  slug: string;
  commodity: string;
  group: string;
  records: SeasonPriceRecord[];
  insights: CommodityInsightSummary;
  alerts: AlertItem[];
  relatedPulse: PulseEvent[];
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

function referencePriceOf(record: SeasonPriceRecord): number | null {
  return record.kharif_price ?? record.rabi_price ?? null;
}

function classifyAvailability(series: SeasonPriceRecord[]): {
  availability: SeasonAvailability;
  kharifShare: number;
  rabiShare: number;
} {
  let kharif = 0;
  let rabi = 0;
  for (const record of series) {
    if (record.kharif_price !== null || record.kharif_arrival_tonnes !== null) {
      kharif += 1;
    }
    if (record.rabi_price !== null || record.rabi_arrival_tonnes !== null) {
      rabi += 1;
    }
  }

  const total = kharif + rabi;
  const kharifShare = total === 0 ? 0 : kharif / total;
  const rabiShare = total === 0 ? 0 : rabi / total;

  let availability: SeasonAvailability;
  if (kharif > 0 && rabi > 0) {
    availability = "Both";
  } else if (kharif > 0) {
    availability = "Kharif only";
  } else if (rabi > 0) {
    availability = "Rabi only";
  } else {
    availability = "Sparse";
  }

  if (series.length < 2 && availability !== "Both") {
    availability = "Sparse";
  }

  return { availability, kharifShare, rabiShare };
}

function classifyRisk(
  latestPrice: number | null,
  latestMsp: number | null,
  availability: SeasonAvailability,
): RiskLevel {
  if (latestPrice === null || latestMsp === null) {
    return "Watch";
  }

  const pct = (latestPrice - latestMsp) / latestMsp;
  if (pct < -0.02) {
    return "High";
  }
  if (availability === "Sparse" && pct < 0.1) {
    return "High";
  }
  if (pct < 0.08) {
    return "Watch";
  }
  return "Low";
}

function recommendFor(
  risk: RiskLevel,
  trend: TrendDirection,
  availability: SeasonAvailability,
): { label: RecommendationLabel; confidence: string; rationale: string } {
  if (risk === "High" && trend !== "up") {
    return {
      label: "Protect",
      confidence: "Moderate confidence",
      rationale:
        "Latest price sits at or below MSP. Protect margins and avoid aggressive selling.",
    };
  }
  if (risk === "High") {
    return {
      label: "Defer",
      confidence: "Low confidence",
      rationale:
        "Prices are weak but lifting. Defer large moves until the next seasonal refresh.",
    };
  }
  if (risk === "Watch" && trend === "down") {
    return {
      label: "Defer",
      confidence: "Moderate confidence",
      rationale:
        "Price is near MSP and softening. Wait unless storage or cash pressure is high.",
    };
  }
  if (risk === "Low" && trend === "up") {
    return {
      label: "Lean sell",
      confidence: "High confidence",
      rationale:
        "Price is above MSP and momentum is positive. A measured sell posture is reasonable.",
    };
  }
  if (availability === "Sparse") {
    return {
      label: "Hold",
      confidence: "Low confidence",
      rationale:
        "Seasonal coverage is sparse. Hold the call lightly until more comparable windows exist.",
    };
  }
  return {
    label: "Hold",
    confidence: "Moderate confidence",
    rationale:
      "Price is above MSP without a strong directional break. A neutral hold posture fits.",
  };
}

export function getCommodityInsights(
  group: string,
  commodity: string,
): CommodityInsightSummary | null {
  const series = getCommoditySeries(group, commodity);
  if (series.length === 0) {
    return null;
  }

  const latest = series[series.length - 1];
  const previous = series.length >= 2 ? series[series.length - 2] : null;
  const latestReferencePrice = referencePriceOf(latest);
  const latestMsp = latest.msp ?? null;
  const latestDelta =
    latestReferencePrice !== null && latestMsp !== null
      ? latestReferencePrice - latestMsp
      : 0;
  const latestDeltaPct =
    latestReferencePrice !== null && latestMsp !== null && latestMsp > 0
      ? latestDelta / latestMsp
      : 0;

  const previousPrice = previous ? referencePriceOf(previous) : null;
  let trend: TrendDirection = "flat";
  let trendChangePct = 0;
  if (latestReferencePrice !== null && previousPrice !== null && previousPrice > 0) {
    trendChangePct = (latestReferencePrice - previousPrice) / previousPrice;
    if (trendChangePct > 0.015) {
      trend = "up";
    } else if (trendChangePct < -0.015) {
      trend = "down";
    }
  }

  const pricedSeries = series
    .map((record) => ({
      season: record.season_year,
      value: referencePriceOf(record),
    }))
    .filter((item): item is { season: string; value: number } => item.value !== null)
    .sort((left, right) => right.value - left.value);

  const highest = pricedSeries[0] ?? {
    season: latest.season_year,
    value: latestReferencePrice ?? 0,
  };

  const { availability, kharifShare, rabiShare } = classifyAvailability(series);
  const risk = classifyRisk(latestReferencePrice, latestMsp, availability);
  const rec = recommendFor(risk, trend, availability);

  return {
    commodity,
    group,
    latestSeason: latest.season_year,
    latestMsp,
    latestReferencePrice,
    latestDelta,
    latestDeltaPct,
    latestDeltaLabel:
      latestReferencePrice === null || latestMsp === null
        ? "No comparable price"
        : `${latestDelta >= 0 ? "+" : ""}${formatCurrency(latestDelta)} vs MSP`,
    highestSeason: highest.season,
    highestPriceLabel: formatCurrency(highest.value),
    priceTrend: trend,
    trendChangePct,
    seasonAvailability: availability,
    kharifShare,
    rabiShare,
    riskLevel: risk,
    recommendationLabel: rec.label,
    confidenceLabel: rec.confidence,
    recommendationRationale: rec.rationale,
  };
}

export function slugify(value: string) {
  return value
    .toLowerCase()
    .replace(/&/g, " and ")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function commoditySlug(group: string, commodity: string) {
  return `${slugify(group)}--${slugify(commodity)}`;
}

export function getAllCommodityCards(): CommodityCardSummary[] {
  const cards: CommodityCardSummary[] = [];

  for (const group of getCommodityGroups()) {
    for (const commodity of getCommoditiesForGroup(group)) {
      const insights = getCommodityInsights(group, commodity);
      if (!insights) {
        continue;
      }

      cards.push({
        slug: commoditySlug(group, commodity),
        commodity,
        group,
        latestSeason: insights.latestSeason,
        latestReferencePrice: insights.latestReferencePrice,
        latestMsp: insights.latestMsp,
        latestDeltaPct: insights.latestDeltaPct,
        riskLevel: insights.riskLevel,
        seasonAvailability: insights.seasonAvailability,
        recommendationLabel: insights.recommendationLabel,
        priceTrend: insights.priceTrend,
      });
    }
  }

  return cards.sort(
    (left, right) => Math.abs(right.latestDeltaPct) - Math.abs(left.latestDeltaPct),
  );
}

export function getAllCommoditySlugs() {
  return getAllCommodityCards().map((card) => ({ slug: card.slug }));
}

export function getCommodityCardBySlug(slug: string) {
  return getAllCommodityCards().find((card) => card.slug === slug) ?? null;
}

export function getCommodityDetailModel(slug: string): CommodityDetailModel | null {
  const card = getCommodityCardBySlug(slug);
  if (!card) {
    return null;
  }

  const records = getCommoditySeries(card.group, card.commodity);
  const insights = getCommodityInsights(card.group, card.commodity);

  if (!insights) {
    return null;
  }

  const relatedAlerts = getAlerts(20).filter(
    (alert) => alert.group === card.group && alert.commodity === card.commodity,
  );
  const relatedPulse = getPulseEvents(20).filter(
    (event) => event.group === card.group && event.commodity === card.commodity,
  );

  return {
    slug,
    commodity: card.commodity,
    group: card.group,
    records,
    insights,
    alerts: relatedAlerts,
    relatedPulse,
  };
}

export function getAlerts(limit = 6): AlertItem[] {
  const alerts: AlertItem[] = [];
  const groups = getCommodityGroups();

  for (const group of groups) {
    for (const commodity of getCommoditiesForGroup(group)) {
      const insights = getCommodityInsights(group, commodity);
      if (!insights) {
        continue;
      }

      if (insights.riskLevel === "High") {
        alerts.push({
          id: `${group}-${commodity}-high`,
          severity: "red",
          commodity,
          group,
          headline: `${commodity} below MSP floor`,
          detail: `${insights.latestSeason} reference price is ${formatCurrency(
            insights.latestReferencePrice,
          )} against MSP ${formatCurrency(insights.latestMsp)}.`,
          season: insights.latestSeason,
        });
      } else if (insights.riskLevel === "Watch") {
        alerts.push({
          id: `${group}-${commodity}-watch`,
          severity: "amber",
          commodity,
          group,
          headline: `${commodity} hovering near MSP`,
          detail: `Latest price is ${(insights.latestDeltaPct * 100).toFixed(
            1,
          )}% from MSP in ${insights.latestSeason}.`,
          season: insights.latestSeason,
        });
      } else if (insights.priceTrend === "up" && insights.latestDeltaPct > 0.15) {
        alerts.push({
          id: `${group}-${commodity}-strong`,
          severity: "green",
          commodity,
          group,
          headline: `${commodity} strengthening`,
          detail: `Reference price is ${(insights.latestDeltaPct * 100).toFixed(
            0,
          )}% above MSP in ${insights.latestSeason}.`,
          season: insights.latestSeason,
        });
      }
    }
  }

  const priority: Record<AlertItem["severity"], number> = {
    red: 0,
    amber: 1,
    green: 2,
  };
  alerts.sort((left, right) => priority[left.severity] - priority[right.severity]);
  return alerts.slice(0, limit);
}

export function getPulseEvents(limit = 7): PulseEvent[] {
  const events: PulseEvent[] = [];

  for (const group of getCommodityGroups()) {
    for (const commodity of getCommoditiesForGroup(group)) {
      const insights = getCommodityInsights(group, commodity);
      if (
        !insights ||
        insights.latestReferencePrice === null ||
        insights.latestMsp === null
      ) {
        continue;
      }

      const delta = insights.latestDeltaPct;
      events.push({
        id: `${group}-${commodity}`,
        commodity,
        group,
        season: insights.seasonAvailability === "Kharif only" ? "Kharif"
               : insights.seasonAvailability === "Rabi only" ? "Rabi"
               : "Both",
        delta,
        deltaLabel: `${delta >= 0 ? "+" : ""}${(delta * 100).toFixed(1)}%`,
        label:
          insights.priceTrend === "up"
            ? "firming vs MSP"
            : insights.priceTrend === "down"
              ? "softening vs MSP"
              : "steady vs MSP",
        timeAgo: insights.latestSeason,
      });
    }
  }

  events.sort((left, right) => Math.abs(right.delta) - Math.abs(left.delta));
  return events.slice(0, limit);
}

export function getCommodityInsightByName(commodity: string): CommodityInsightSummary | null {
  for (const group of getCommodityGroups()) {
    for (const c of getCommoditiesForGroup(group)) {
      if (c === commodity) return getCommodityInsights(group, c);
    }
  }
  return null;
}

export function getDashboardSummary(): DashboardSummary {
  const cards = getAllCommodityCards();
  return {
    dataMode: "seasonal_commodity",
    totalCommodities: cards.length,
    totalGroups: getCommodityGroups().length,
    spotlight: cards[0] ?? null,
    movers: cards.slice(0, 6),
    alerts: getAlerts(5),
    pulseEvents: getPulseEvents(6),
    updatedAt: "Season sync active",
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
      const y =
        config.height -
        config.padding -
        scale * (config.height - config.padding * 2);

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
