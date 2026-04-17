"use client";

import { useEffect, useMemo, useState } from "react";
import { CommodityGroupSelector } from "../../components/CommodityGroupSelector";
import { CommoditySelector } from "../../components/CommoditySelector";
import { InsightCards } from "../../components/InsightCards";
import { MSPComparisonCard } from "../../components/MSPComparisonCard";
import { SeasonArrivalChart } from "../../components/SeasonArrivalChart";
import { SeasonPriceChart } from "../../components/SeasonPriceChart";
import { CommoditySummaryTable } from "../../components/CommoditySummaryTable";
import {
  getCommodityGroups,
  getCommoditiesForGroup,
  getCommodityInsights,
  getCommoditySeries,
} from "../../lib/canned-data";

export default function DashboardPage() {
  const groups = useMemo(() => getCommodityGroups(), []);
  const [selectedGroup, setSelectedGroup] = useState(groups[0] ?? "");

  const commodities = useMemo(
    () => getCommoditiesForGroup(selectedGroup),
    [selectedGroup],
  );

  const [selectedCommodity, setSelectedCommodity] = useState(commodities[0] ?? "");

  useEffect(() => {
    if (!commodities.includes(selectedCommodity)) {
      setSelectedCommodity(commodities[0] ?? "");
    }
  }, [commodities, selectedCommodity]);

  const records = useMemo(
    () => getCommoditySeries(selectedGroup, selectedCommodity),
    [selectedGroup, selectedCommodity],
  );
  const insights = useMemo(
    () => getCommodityInsights(selectedGroup, selectedCommodity),
    [selectedGroup, selectedCommodity],
  );

  return (
    <main className="dashboard-shell">
      <section className="dashboard-header">
        <div>
          <p className="eyebrow">Seasonal Commodity Intelligence</p>
          <h1>Compare MSP, prices, and arrivals across seasons.</h1>
          <p className="section-copy">
            The dashboard is powered by the normalized crop reports in
            <code> crop_data/season_report_summary.json</code>.
          </p>
        </div>
      </section>

      <section className="filter-grid">
        <CommodityGroupSelector
          groups={groups}
          selectedGroup={selectedGroup}
          onChange={(group) => {
            setSelectedGroup(group);
            setSelectedCommodity(getCommoditiesForGroup(group)[0] ?? "");
          }}
        />
        <CommoditySelector
          commodities={commodities}
          selectedCommodity={selectedCommodity}
          onChange={setSelectedCommodity}
        />
      </section>

      <InsightCards insights={insights} />

      <section className="content-grid">
        <SeasonPriceChart records={records} />
        <MSPComparisonCard insights={insights} />
      </section>

      <section className="content-grid">
        <SeasonArrivalChart records={records} />
        <CommoditySummaryTable records={records} />
      </section>
    </main>
  );
}
