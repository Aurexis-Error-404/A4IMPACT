"use client";

import { useMemo } from "react";
import { useRouter } from "next/navigation";
import { CommodityFilterBar } from "./CommodityFilterBar";
import { slugify } from "../lib/canned-data";

type Pair = { group: string; commodity: string; slug: string };

type Props = {
  currentGroup: string;
  currentCommodity: string;
  groups: string[];
  pairs: Pair[];
};

export function CommodityDetailNav({ currentGroup, currentCommodity, groups, pairs }: Props) {
  const router = useRouter();

  const commoditiesInGroup = useMemo(
    () => pairs.filter((p) => p.group === currentGroup).map((p) => p.commodity),
    [pairs, currentGroup],
  );

  return (
    <CommodityFilterBar
      groups={groups}
      selectedGroup={currentGroup}
      onGroupChange={(group) => {
        const first = pairs.find((p) => p.group === group);
        if (first) router.push(`/commodity/${first.slug}`);
      }}
      commodities={commoditiesInGroup}
      selectedCommodity={currentCommodity}
      onCommodityChange={(commodity) => {
        const match = pairs.find(
          (p) => p.group === currentGroup && p.commodity === commodity,
        );
        if (match) router.push(`/commodity/${match.slug}`);
      }}
    />
  );
}
