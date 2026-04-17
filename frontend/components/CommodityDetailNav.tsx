"use client";

import { useMemo } from "react";
import { useRouter } from "next/navigation";
import { CommodityFilterBar } from "./CommodityFilterBar";
import {
  getCommodityGroups,
  getCommoditiesForGroup,
  getAllCommodityCards,
} from "../lib/canned-data";

export function CommodityDetailNav({
  currentGroup,
  currentCommodity,
}: {
  currentGroup: string;
  currentCommodity: string;
}) {
  const router = useRouter();
  const groups = useMemo(() => getCommodityGroups(), []);
  const allCards = useMemo(() => getAllCommodityCards(), []);

  const commoditiesInGroup = useMemo(
    () => getCommoditiesForGroup(currentGroup),
    [currentGroup]
  );

  return (
    <CommodityFilterBar
      groups={groups}
      selectedGroup={currentGroup}
      onGroupChange={(group) => {
        // Navigate to the first commodity inside the new group
        const groupCards = allCards.filter((c) => c.group === group);
        if (groupCards.length > 0) {
          router.push(`/commodity/${groupCards[0].slug}`);
        }
      }}
      commodities={commoditiesInGroup}
      selectedCommodity={currentCommodity}
      onCommodityChange={(commodity) => {
        const card = allCards.find((c) => c.commodity === commodity);
        if (card) {
          router.push(`/commodity/${card.slug}`);
        }
      }}
    />
  );
}
