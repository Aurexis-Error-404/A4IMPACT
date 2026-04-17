"use client";

type Props = {
  kharifShare: number;
  rabiShare: number;
};

export function SeasonSplitBar({ kharifShare, rabiShare }: Props) {
  const total = kharifShare + rabiShare || 1;
  const k = (kharifShare / total) * 100;
  const r = (rabiShare / total) * 100;

  return (
    <div>
      <div className="season-split">
        <div className="k" style={{ flexBasis: `${k}%` }} />
        <div className="r" style={{ flexBasis: `${r}%` }} />
      </div>
      <div className="season-split-legend">
        <span>Kharif {k.toFixed(0)}%</span>
        <span>Rabi {r.toFixed(0)}%</span>
      </div>
    </div>
  );
}
