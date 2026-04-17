import Link from "next/link";
import { notFound } from "next/navigation";
import { AlertSeverityStack } from "../../../components/AlertSeverityStack";
import { AIRecommendationSection } from "../../../components/AIRecommendationSection";
import { HeroCanvas } from "../../../components/HeroCanvas";
import { MSPComparisonRail } from "../../../components/MSPComparisonCard";
import { RiskPanel } from "../../../components/RiskPanel";
import { SeasonArrivalChart } from "../../../components/SeasonArrivalChart";
import { SeasonAvailabilityBand } from "../../../components/SeasonAvailabilityBand";
import { SeasonPriceChart } from "../../../components/SeasonPriceChart";
import { SeasonalComparisonPanel } from "../../../components/SeasonalComparisonPanel";
import { CommoditySummaryTable } from "../../../components/CommoditySummaryTable";
import { TopNav } from "../../../components/TopNav";
import { CommodityDetailNav } from "../../../components/CommodityDetailNav";
import { ProfitEstimatePanel } from "../../../components/ProfitEstimatePanel";
import { PriceRangeBand } from "../../../components/PriceRangeBand";
import {
  fetchAllCommodityPairs,
  fetchCommodityInsights,
  fetchCommoditySeries,
  fetchAlerts,
} from "../../../lib/api";

export const dynamic = "force-dynamic";

type Params = { slug: string };

export default async function CommodityDetailPage({ params }: { params: Params }) {
  const pairs = await fetchAllCommodityPairs();
  const match = pairs.find((p) => p.slug === params.slug);
  if (!match) notFound();

  const { group, commodity } = match;

  const [records, insights, allAlerts] = await Promise.all([
    fetchCommoditySeries(group, commodity),
    fetchCommodityInsights(group, commodity),
    fetchAlerts(30),
  ]);

  const relatedAlerts = allAlerts.filter(
    (a) => a.group === group && a.commodity === commodity,
  );

  const groups = Array.from(new Set(pairs.map((p) => p.group)));

  return (
    <main className="page-shell detail-page">
      <TopNav activeCommodityLabel={commodity} />

      <CommodityDetailNav
        currentGroup={group}
        currentCommodity={commodity}
        groups={groups}
        pairs={pairs}
      />

      <div className="detail-backlink">
        <Link href="/dashboard">Back to dashboard</Link>
      </div>

      <HeroCanvas
        insights={insights}
        group={group}
        lastUpdated={`Season ${insights.latestSeason}`}
      />

      <MSPComparisonRail insights={insights} />

      <section className="dashboard-grid">
        <div className="chart-stack">
          <SeasonPriceChart records={records} />
          <SeasonArrivalChart records={records} />
        </div>
        <div className="side-stack">
          {/* AI recommendation loads independently with a spinner */}
          <AIRecommendationSection commodity={commodity} basicInsights={insights} />
          <RiskPanel insights={insights} />
          {insights.expectedPriceRange && (
            <PriceRangeBand
              floor={insights.expectedPriceRange.floor}
              ceiling={insights.expectedPriceRange.ceiling}
              current={insights.latestReferencePrice}
              basis={insights.expectedPriceRange.basis}
            />
          )}
          <ProfitEstimatePanel commodity={commodity} />
        </div>
      </section>

      <section className="dashboard-grid lower">
        <SeasonalComparisonPanel records={records} insights={insights} />
        <div className="side-stack">
          <div className="card feature">
            <span className="card-label">Season mode</span>
            <h3>Availability band</h3>
            <p className="card-copy">
              This view stays honest about whether the commodity is represented in
              Kharif, Rabi, or both.
            </p>
            <SeasonAvailabilityBand availability={insights.seasonAvailability} />
          </div>
          <article className="card">
            <span className="card-label">Alerts</span>
            <h3>Commodity-specific signals</h3>
            <p className="card-copy">
              These alerts are filtered to the selected commodity only.
            </p>
            <AlertSeverityStack alerts={relatedAlerts} />
          </article>
        </div>
      </section>

      <CommoditySummaryTable records={records} />
    </main>
  );
}
