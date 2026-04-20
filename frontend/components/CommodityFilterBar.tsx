"use client";

import { CommodityGroupSelector } from "./CommodityGroupSelector";
import { CommoditySelector } from "./CommoditySelector";

type Pair = { group: string; commodity: string; slug: string };

type Props = {
  groups: string[];
  selectedGroup: string;
  onGroupChange: (value: string) => void;
  commodities: string[];
  selectedCommodity: string;
  onCommodityChange: (value: string) => void;
  allPairs?: Pair[];
  onCropSelect?: (group: string, commodity: string) => void;
};

export function CommodityFilterBar({
  groups,
  selectedGroup,
  onGroupChange,
  commodities,
  selectedCommodity,
  onCommodityChange,
  allPairs,
  onCropSelect,
}: Props) {
  if (allPairs && allPairs.length > 0 && onCropSelect) {
    const groupedPairs = groups.map((g) => ({
      group: g,
      crops: allPairs.filter((p) => p.group === g),
    }));

    const currentValue = `${selectedGroup}||${selectedCommodity}`;

    return (
      <section className="filter-row">
        <div className="filter-card">
          <label htmlFor="crop-picker">Select your crop</label>
          <select
            id="crop-picker"
            value={currentValue}
            onChange={(e) => {
              const [group, commodity] = e.target.value.split("||");
              onCropSelect(group, commodity);
            }}
          >
            {groupedPairs.map(({ group, crops }) => (
              <optgroup key={group} label={group}>
                {crops.map((p) => (
                  <option key={p.slug} value={`${p.group}||${p.commodity}`}>
                    {p.commodity}
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
        </div>
      </section>
    );
  }

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
