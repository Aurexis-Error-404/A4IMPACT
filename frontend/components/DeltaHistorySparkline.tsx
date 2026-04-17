"use client";

type Props = {
  history: number[];  // decimal values, e.g. 0.12 = 12%
};

const W = 80;
const H = 32;
const PAD = 4;

export function DeltaHistorySparkline({ history }: Props) {
  if (!history || history.length < 2) return null;

  const min = Math.min(...history);
  const max = Math.max(...history);
  const range = max - min || 1;

  const xs = history.map((_, i) => PAD + (i / (history.length - 1)) * (W - PAD * 2));
  const ys = history.map((v) => H - PAD - ((v - min) / range) * (H - PAD * 2));

  const d = xs.map((x, i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${ys[i].toFixed(1)}`).join(" ");
  const last = history[history.length - 1];
  const colour = last > 0 ? "#c7d69d" : last < 0 ? "#f1b2b2" : "#aaa";

  return (
    <svg
      width={W}
      height={H}
      viewBox={`0 0 ${W} ${H}`}
      className="delta-sparkline"
      aria-label="Price vs MSP trend"
    >
      {/* zero line */}
      {min < 0 && max > 0 && (
        <line
          x1={PAD}
          x2={W - PAD}
          y1={H - PAD - ((0 - min) / range) * (H - PAD * 2)}
          y2={H - PAD - ((0 - min) / range) * (H - PAD * 2)}
          stroke="#555"
          strokeWidth="0.5"
          strokeDasharray="2,2"
        />
      )}
      <path d={d} fill="none" stroke={colour} strokeWidth="1.5" strokeLinejoin="round" />
      <circle
        cx={xs[xs.length - 1]}
        cy={ys[ys.length - 1]}
        r={2.5}
        fill={colour}
      />
    </svg>
  );
}
