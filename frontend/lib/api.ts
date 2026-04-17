import {
  getAlerts,
  getAllCommodityCards,
  getAllCommoditySlugs,
  getCommodityDetailModel,
  getDashboardSummary,
} from "./canned-data";

export async function fetchDashboardSummary() {
  return getDashboardSummary();
}

export async function fetchCommodityCards() {
  return getAllCommodityCards();
}

export async function fetchCommodityDetail(slug: string) {
  return getCommodityDetailModel(slug);
}

export async function fetchCommoditySlugs() {
  return getAllCommoditySlugs();
}

export async function fetchAlerts(limit?: number) {
  return getAlerts(limit);
}
