import Link from "next/link";
import { TopNav } from "../components/TopNav";

export default function NotFoundPage() {
  return (
    <main className="page-shell home-page">
      <TopNav />
      <section className="hero-stage">
        <div className="hero-copy-block">
          <span className="section-kicker">Not found</span>
          <h1 className="page-title">That commodity page does not exist yet.</h1>
          <p className="lede">
            The route may be outdated, or the slug does not map to a commodity in
            the current seasonal dataset.
          </p>
          <div className="action-row">
            <Link className="primary-button" href="/dashboard">
              Return to dashboard
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
