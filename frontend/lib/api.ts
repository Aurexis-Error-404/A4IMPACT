import type {
  AlertItem,
  CommodityCardSummary,
  CommodityDetailModel,
  CommodityInsightSummary,
  DashboardSummary,
  PulseEvent,
  SeasonPriceRecord,
} from "./canned-data";
import { slugify } from "./canned-data";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function commoditySlug(group: string, commodity: string) {
  return `${slugify(group)}--${slugify(commodity)}`;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

async function post<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`POST ${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

async function allCommodityPairs(): Promise<{ group: string; commodity: string }[]> {
  const groups = await get<string[]>("/api/commodity-groups");
  const nested = await Promise.all(
    groups.map(async (g) => {
      const cs = await get<string[]>(`/api/commodities?group=${encodeURIComponent(g)}`);
      return cs.map((c) => ({ group: g, commodity: c }));
    }),
  );
  return nested.flat();
}

async function allInsights(): Promise<CommodityInsightSummary[]> {
  const pairs = await allCommodityPairs();
  return Promise.all(
    pairs.map(({ group, commodity }) =>
      get<CommodityInsightSummary>(
        `/api/commodity-insights?group=${encodeURIComponent(group)}&commodity=${encodeURIComponent(commodity)}`,
      ),
    ),
  );
}

function toCard(ins: CommodityInsightSummary): CommodityCardSummary {
  return {
    slug: commoditySlug(ins.group, ins.commodity),
    commodity: ins.commodity,
    group: ins.group,
    latestSeason: ins.latestSeason,
    latestReferencePrice: ins.latestReferencePrice,
    latestMsp: ins.latestMsp,
    latestDeltaPct: ins.latestDeltaPct,
    riskLevel: ins.riskLevel,
    seasonAvailability: ins.seasonAvailability,
    recommendationLabel: ins.recommendationLabel,
    priceTrend: ins.priceTrend,
  };
}

function toPulseEvents(insights: CommodityInsightSummary[], limit: number): PulseEvent[] {
  return insights
    .filter((ins) => ins.latestReferencePrice !== null && ins.latestMsp !== null)
    .map((ins) => ({
      id: `${ins.group}-${ins.commodity}`,
      commodity: ins.commodity,
      group: ins.group,
      season: ins.latestSeason,
      delta: ins.latestDeltaPct,
      deltaLabel: `${ins.latestDeltaPct >= 0 ? "+" : ""}${(ins.latestDeltaPct * 100).toFixed(1)}%`,
      label:
        ins.priceTrend === "up"
          ? "firming vs MSP"
          : ins.priceTrend === "down"
            ? "softening vs MSP"
            : "steady vs MSP",
      timeAgo: ins.latestSeason,
    }))
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
    .slice(0, limit);
}

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const [insights, allAlerts] = await Promise.all([
    allInsights(),
    get<AlertItem[]>("/api/alerts"),
  ]);

  const cards = insights
    .map(toCard)
    .sort((a, b) => Math.abs(b.latestDeltaPct) - Math.abs(a.latestDeltaPct));

  return {
    dataMode: "seasonal_commodity",
    totalCommodities: cards.length,
    totalGroups: new Set(insights.map((i) => i.group)).size,
    spotlight: cards[0] ?? null,
    movers: cards.slice(0, 6),
    alerts: allAlerts.slice(0, 5),
    pulseEvents: toPulseEvents(insights, 6),
    updatedAt: "Season sync active",
  };
}

export async function fetchCommodityCards(): Promise<CommodityCardSummary[]> {
  const insights = await allInsights();
  return insights
    .map(toCard)
    .sort((a, b) => Math.abs(b.latestDeltaPct) - Math.abs(a.latestDeltaPct));
}

export async function fetchCommodityDetail(
  targetSlug: string,
): Promise<CommodityDetailModel | null> {
  const pairs = await allCommodityPairs();
  const match = pairs.find(
    ({ group, commodity }) => commoditySlug(group, commodity) === targetSlug,
  );
  if (!match) return null;

  const { group, commodity } = match;

  const [records, aiInsights, allAlerts] = await Promise.all([
    get<SeasonPriceRecord[]>(
      `/api/commodity-series?group=${encodeURIComponent(group)}&commodity=${encodeURIComponent(commodity)}`,
    ),
    post<CommodityInsightSummary>(`/api/recommendation/${encodeURIComponent(commodity)}`),
    get<AlertItem[]>("/api/alerts"),
  ]);

  const relatedAlerts = allAlerts.filter(
    (a) => a.group === group && a.commodity === commodity,
  );

  const relatedPulse: PulseEvent[] = [
    {
      id: `${group}-${commodity}`,
      commodity,
      group,
      season: aiInsights.latestSeason,
      delta: aiInsights.latestDeltaPct,
      deltaLabel: `${aiInsights.latestDeltaPct >= 0 ? "+" : ""}${(aiInsights.latestDeltaPct * 100).toFixed(1)}%`,
      label:
        aiInsights.priceTrend === "up"
          ? "firming vs MSP"
          : aiInsights.priceTrend === "down"
            ? "softening vs MSP"
            : "steady vs MSP",
      timeAgo: aiInsights.latestSeason,
    },
  ];

  return {
    slug: targetSlug,
    commodity,
    group,
    records,
    insights: aiInsights,
    alerts: relatedAlerts,
    relatedPulse,
  };
}

export async function fetchCommoditySlugs(): Promise<{ slug: string }[]> {
  const pairs = await allCommodityPairs();
  return pairs.map(({ group, commodity }) => ({
    slug: commoditySlug(group, commodity),
  }));
}

export async function fetchAlerts(limit = 6): Promise<AlertItem[]> {
  const alerts = await get<AlertItem[]>("/api/alerts");
  return alerts.slice(0, limit);
}

// Granular helpers used by individual pages
export async function fetchAllCommodityPairs(): Promise<{ group: string; commodity: string; slug: string }[]> {
  const pairs = await allCommodityPairs();
  return pairs.map((p) => ({ ...p, slug: commoditySlug(p.group, p.commodity) }));
}

export async function fetchCommodityGroups(): Promise<string[]> {
  return get<string[]>("/api/commodity-groups");
}

export async function fetchCommoditiesForGroup(group: string): Promise<string[]> {
  return get<string[]>(`/api/commodities?group=${encodeURIComponent(group)}`);
}

export async function fetchCommodityInsights(group: string, commodity: string): Promise<CommodityInsightSummary> {
  return get<CommodityInsightSummary>(
    `/api/commodity-insights?group=${encodeURIComponent(group)}&commodity=${encodeURIComponent(commodity)}`,
  );
}

export async function fetchCommoditySeries(group: string, commodity: string): Promise<SeasonPriceRecord[]> {
  return get<SeasonPriceRecord[]>(
    `/api/commodity-series?group=${encodeURIComponent(group)}&commodity=${encodeURIComponent(commodity)}`,
  );
}

export async function fetchAIRecommendation(commodity: string): Promise<CommodityInsightSummary> {
  return post<CommodityInsightSummary>(`/api/recommendation/${encodeURIComponent(commodity)}`);
}

export { commoditySlug };
