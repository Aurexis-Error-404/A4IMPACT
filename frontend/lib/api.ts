import {
  getCommodityGroups,
  getCommoditiesForGroup,
  getCommodityInsights,
  getCommoditySeries,
} from "./canned-data";

export async function fetchCommodityGroups() {
  return getCommodityGroups();
}

export async function fetchCommoditiesForGroup(group: string) {
  return getCommoditiesForGroup(group);
}

export async function fetchCommoditySeries(group: string, commodity: string) {
  return getCommoditySeries(group, commodity);
}

export async function fetchCommodityInsights(group: string, commodity: string) {
  return getCommodityInsights(group, commodity);
}
