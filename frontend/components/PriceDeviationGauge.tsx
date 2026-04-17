"use client";

type Props = {
  deltaPct: number;
};

export function PriceDeviationGauge({ deltaPct }: Props) {
  const clamped = Math.max(-0.3, Math.min(0.3, deltaPct));
  const pos = ((clamped + 0.3) / 0.6) * 100;

  return (
    <div>
      <div className="gauge-track">
        <div className="gauge-marker" style={{ left: `${pos}%` }} />
      </div>
      <div className="gauge-scale">
        <span>−30% vs MSP</span>
        <span>At MSP</span>
        <span>+30%</span>
      </div>
    </div>
  );
}
