import Link from "next/link";

export default function HomePage() {
  return (
    <main className="hero-shell">
      <section className="hero-panel">
        <p className="eyebrow">KrishiCFO MVP</p>
        <h1>Season-wise crop intelligence, grounded in the data we actually have.</h1>
        <p className="hero-copy">
          This version focuses on commodity groups, multi-season price movement,
          MSP comparison, and Kharif/Rabi arrivals across the checked-in crop
          reports.
        </p>
        <div className="hero-actions">
          <Link className="primary-button" href="/dashboard">
            Open dashboard
          </Link>
        </div>
      </section>
    </main>
  );
}
