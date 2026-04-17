"use client";

import { CommodityGroupSelector } from "./CommodityGroupSelector";
import { CommoditySelector } from "./CommoditySelector";

type Props = {
  groups: string[];
  selectedGroup: string;
  onGroupChange: (value: string) => void;
  commodities: string[];
  selectedCommodity: string;
  onCommodityChange: (value: string) => void;
};

export function CommodityFilterBar({
  groups,
  selectedGroup,
  onGroupChange,
  commodities,
  selectedCommodity,
  onCommodityChange,
}: Props) {
  return (
    <section className="filter-row">
      <CommodityGroupSelector
        groups={groups}
        selectedGroup={selectedGroup}
        onChange={onGroupChange}
      />
      <CommoditySelector
        commodities={commodities}
        selectedCommodity={selectedCommodity}
        onChange={onCommodityChange}
      />
    </section>
  );
}
