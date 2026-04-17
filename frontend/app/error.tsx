"use client";

import { useEffect } from "react";

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("[KrishiCFO error boundary]", error);
  }, [error]);

  return (
    <main className="page-shell">
      <section className="hero-stage">
        <div className="hero-copy-block">
          <span className="section-kicker">Something went wrong</span>
          <h1 className="page-title">An unexpected error occurred.</h1>
          <p className="lede">
            {error.message || "The page could not render. Please try again."}
          </p>
          <div className="action-row">
            <button className="primary-button" onClick={reset}>
              Try again
            </button>
          </div>
        </div>
      </section>
    </main>
  );
}
