import Link from "next/link";
import { notFound } from "next/navigation";
import { AlertSeverityStack } from "../../../components/AlertSeverityStack";
import { HeroCanvas } from "../../../components/HeroCanvas";
import { MSPComparisonRail } from "../../../components/MSPComparisonCard";
import { RecommendationCard } from "../../../components/RecommendationCard";
import { RiskPanel } from "../../../components/RiskPanel";
import { SeasonArrivalChart } from "../../../components/SeasonArrivalChart";
import { SeasonAvailabilityBand } from "../../../components/SeasonAvailabilityBand";
import { SeasonPriceChart } from "../../../components/SeasonPriceChart";
import { SeasonalComparisonPanel } from "../../../components/SeasonalComparisonPanel";
import { CommoditySummaryTable } from "../../../components/CommoditySummaryTable";
import { TopNav } from "../../../components/TopNav";
import { CommodityDetailNav } from "../../../components/CommodityDetailNav";
import { fetchCommoditySlugs } from "../../../lib/api";
import { getCommodityDetailModel } from "../../../lib/canned-data";

type Params = {
  slug: string;
};

export async function generateStaticParams() {
  return fetchCommoditySlugs();
}

export default function CommodityDetailPage({
  params,
}: {
  params: Params;
}) {
  const detail = getCommodityDetailModel(params.slug);
  if (!detail) {
    notFound();
  }

  return (
    <main className="page-shell detail-page">
      <TopNav activeCommodityLabel={detail.commodity} />

      <CommodityDetailNav 
        currentGroup={detail.group} 
        currentCommodity={detail.commodity} 
      />

      <div className="detail-backlink">
        <Link href="/dashboard">Back to dashboard</Link>
      </div>

      <HeroCanvas
        insights={detail.insights}
        group={detail.group}
        lastUpdated={`Season ${detail.insights.latestSeason}`}
      />

      <MSPComparisonRail insights={detail.insights} />

      <section className="dashboard-grid">
        <div className="chart-stack">
          <SeasonPriceChart records={detail.records} />
          <SeasonArrivalChart records={detail.records} />
        </div>
        <div className="side-stack">
          <RecommendationCard insights={detail.insights} />
          <RiskPanel insights={detail.insights} />
        </div>
      </section>

      <section className="dashboard-grid lower">
        <SeasonalComparisonPanel
          records={detail.records}
          insights={detail.insights}
        />
        <div className="side-stack">
          <div className="card feature">
            <span className="card-label">Season mode</span>
            <h3>Availability band</h3>
            <p className="card-copy">
              This view stays honest about whether the commodity is represented in
              Kharif, Rabi, or both.
            </p>
            <SeasonAvailabilityBand availability={detail.insights.seasonAvailability} />
          </div>
          <article className="card">
            <span className="card-label">Alerts</span>
            <h3>Commodity-specific signals</h3>
            <p className="card-copy">
              These alerts are filtered to the selected commodity only.
            </p>
            <AlertSeverityStack alerts={detail.alerts} />
          </article>
        </div>
      </section>

      <CommoditySummaryTable records={detail.records} />
    </main>
  );
}
