import Link from "next/link";
import { TopNav } from "../components/TopNav";
import { fetchDashboardSummary } from "../lib/api";
import { formatCurrency } from "../lib/canned-data";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const summary = await fetchDashboardSummary();
  const spotlight = summary.spotlight;

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
          <span className="card-label">What changes here</span>
          <h3>Not just prettier, actually structured.</h3>
          <p className="card-copy">
            The new UI is split into real pages: Home, Dashboard, and Commodity
            Detail. Each screen has a clear job instead of forcing the whole app
            into a single scroll stack.
          </p>
        </article>
        <article className="card">
          <span className="card-label">Visual direction</span>
          <h3>Photo-led, darker, calmer.</h3>
          <p className="card-copy">
            Premium field-inspired backgrounds, selective glass, restrained motion,
            and stronger page hierarchy replace the old flat green-heavy shell.
          </p>
        </article>
        <article className="card">
          <span className="card-label">Data honesty</span>
          <h3>Seasonal intelligence, not fake streaming.</h3>
          <p className="card-copy">
            Recommendations, alerts, and pulse events are all grounded in the
            checked-in seasonal commodity dataset and stay explicit about their
            heuristic nature.
          </p>
        </article>
      </section>
    </main>
  );
}
