import Link from "next/link";
import { TopNav } from "../components/TopNav";
import { fetchDashboardSummary } from "../lib/api";
import { formatCurrency } from "../lib/canned-data";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const summary = await fetchDashboardSummary();
  const spotlight = summary.spotlight;

  const topMover = summary.movers[0] ?? null;

  const redAlerts = summary.alerts.filter((a) => a.severity === "red").length;
  const amberAlerts = summary.alerts.filter((a) => a.severity === "amber").length;

  const seasonCounts = summary.pulseEvents.reduce(
    (acc, e) => {
      if (e.season === "Kharif") acc.kharif++;
      else if (e.season === "Rabi") acc.rabi++;
      else acc.both++;
      return acc;
    },
    { kharif: 0, rabi: 0, both: 0 },
  );

  return (
    <main className="page-shell home-page">
      <TopNav />
      <section className="hero-stage">
        <div className="hero-copy-block">
          <span className="section-kicker">KrishiCFO seasonal intelligence</span>
          <h1 className="page-title">
            A premium agritech read on price floors, seasonal flow, and crop risk.
          </h1>
          <p className="lede">
            Built around the crop reports you actually have. The experience is
            route-driven, commodity-led, and designed to feel like a real product
            rather than one long analytics screen.
          </p>
          <div className="action-row">
            <Link className="primary-button" href="/dashboard">
              Open dashboard
            </Link>
            {spotlight ? (
              <Link className="secondary-button" href={`/commodity/${spotlight.slug}`}>
                View spotlight commodity
              </Link>
            ) : null}
          </div>
        </div>
        <div className="glass-hero-card">
          <span className="card-label">System snapshot</span>
          <h2>{spotlight?.commodity ?? "Seasonal commodity mode"}</h2>
          <p className="card-copy">
            The current app tracks crop performance across seasons, compares
            reference prices to MSP, and surfaces risk without pretending we have
            daily mandi-level data.
          </p>
          <div className="metric-grid">
            <div className="metric-card">
              <span className="metric-label">Tracked commodities</span>
              <strong>{summary.totalCommodities}</strong>
            </div>
            <div className="metric-card">
              <span className="metric-label">Commodity groups</span>
              <strong>{summary.totalGroups}</strong>
            </div>
            <div className="metric-card">
              <span className="metric-label">Spotlight price</span>
              <strong>{formatCurrency(spotlight?.latestReferencePrice ?? null)}</strong>
            </div>
            <div className="metric-card">
              <span className="metric-label">Risk posture</span>
              <strong>{spotlight?.riskLevel ?? "Watch"}</strong>
            </div>
          </div>
        </div>
      </section>

      <section className="home-preview-grid">
        <article className="card feature">
          <span className="card-label">Top mover</span>
          {topMover ? (
            <>
              <h3>{topMover.commodity}</h3>
              <p className="card-copy">
                {topMover.group} · {topMover.seasonAvailability}
              </p>
              <div className="metric-grid compact">
                <div className="metric-card">
                  <span className="metric-label">Reference price</span>
                  <strong>{formatCurrency(topMover.latestReferencePrice)}</strong>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Season delta</span>
                  <strong
                    style={{ color: topMover.latestDeltaPct >= 0 ? "var(--gold)" : "var(--red)" }}
                  >
                    {topMover.latestDeltaPct >= 0 ? "+" : ""}
                    {(topMover.latestDeltaPct * 100).toFixed(1)}%
                  </strong>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Risk level</span>
                  <strong>{topMover.riskLevel}</strong>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Season</span>
                  <strong>{topMover.latestSeason}</strong>
                </div>
              </div>
            </>
          ) : (
            <p className="card-copy">No mover data available.</p>
          )}
        </article>

        <article className="card">
          <span className="card-label">Live alerts</span>
          <h3>
            {redAlerts + amberAlerts > 0
              ? `${redAlerts + amberAlerts} active signal${redAlerts + amberAlerts !== 1 ? "s" : ""}`
              : "No active alerts"}
          </h3>
          <p className="card-copy">
            {redAlerts > 0 && `${redAlerts} high-pressure alert${redAlerts !== 1 ? "s" : ""}. `}
            {amberAlerts > 0 && `${amberAlerts} watch-level signal${amberAlerts !== 1 ? "s" : ""}. `}
            {redAlerts === 0 && amberAlerts === 0
              ? "All commodities within normal seasonal range."
              : "Review the dashboard for full context."}
          </p>
          <div className="metric-grid compact">
            <div className="metric-card">
              <span className="metric-label">High pressure</span>
              <strong style={{ color: redAlerts > 0 ? "var(--red)" : undefined }}>
                {redAlerts}
              </strong>
            </div>
            <div className="metric-card">
              <span className="metric-label">Watch signals</span>
              <strong style={{ color: amberAlerts > 0 ? "var(--gold)" : undefined }}>
                {amberAlerts}
              </strong>
            </div>
          </div>
        </article>

        <article className="card">
          <span className="card-label">Season coverage</span>
          <h3>Kharif, Rabi &amp; year-round</h3>
          <p className="card-copy">
            Commodity pulse events across tracked seasonal windows.
          </p>
          <div className="metric-grid compact">
            <div className="metric-card">
              <span className="metric-label">Kharif events</span>
              <strong>{seasonCounts.kharif}</strong>
            </div>
            <div className="metric-card">
              <span className="metric-label">Rabi events</span>
              <strong>{seasonCounts.rabi}</strong>
            </div>
            <div className="metric-card">
              <span className="metric-label">Both seasons</span>
              <strong>{seasonCounts.both}</strong>
            </div>
            <div className="metric-card">
              <span className="metric-label">Total events</span>
              <strong>{summary.pulseEvents.length}</strong>
            </div>
          </div>
        </article>
      </section>
    </main>
  );
}
