"use client";

import { useEffect, useState } from "react";
import { TrendDirection } from "../lib/canned-data";

type Props = {
  direction: TrendDirection;
  changePct: number;
};

export function TrendArrowBadge({ direction, changePct }: Props) {
  const [displayPct, setDisplayPct] = useState(0);

  useEffect(() => {
    const target = changePct * 100;
    let raf = 0;
    const start = performance.now();
    const duration = 520;
    const step = (time: number) => {
      const progress = Math.min(1, (time - start) / duration);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayPct(target * eased);
      if (progress < 1) {
        raf = requestAnimationFrame(step);
      }
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [changePct]);

  const arrow = direction === "up" ? "^" : direction === "down" ? "v" : "-";
  const label =
    direction === "up" ? "Firming" : direction === "down" ? "Softening" : "Steady";

  return (
    <span className={`trend-badge ${direction}`}>
      <span className="arrow">{arrow}</span>
      <span>{label}</span>
      <span className="mono">
        {displayPct >= 0 ? "+" : ""}
        {displayPct.toFixed(1)}%
      </span>
    </span>
  );
}
