"use client";

import { useState, useEffect, useCallback } from "react";

const STORAGE_KEY = "krishicfo_favourites";

export function useFavourites() {
  const [favourites, setFavourites] = useState<string[]>([]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) setFavourites(JSON.parse(stored));
    } catch {}
  }, []);

  const toggle = useCallback((slug: string) => {
    setFavourites((prev) => {
      const next = prev.includes(slug)
        ? prev.filter((s) => s !== slug)
        : [...prev, slug];
      if (typeof window !== "undefined") {
        try { localStorage.setItem(STORAGE_KEY, JSON.stringify(next)); } catch {}
      }
      return next;
    });
  }, []);

  const isFavourite = useCallback((slug: string) => favourites.includes(slug), [favourites]);

  return { favourites, toggle, isFavourite };
}
