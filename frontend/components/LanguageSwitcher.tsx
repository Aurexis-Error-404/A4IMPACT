"use client";

import { useLocale } from "next-intl";
import { useRouter } from "next/navigation";
import { localeLabels, locales, type Locale } from "../i18n-config";

export function LanguageSwitcher() {
  const router = useRouter();
  const current = useLocale();
  const activeIndex = locales.indexOf(current as Locale);
  const activeOffset = activeIndex === -1 ? 0 : activeIndex * 100;

  function switchLocale(locale: Locale) {
    document.cookie = `locale=${locale};path=/;max-age=31536000`;
    router.refresh();
  }

  return (
    <div className="glass-segmented-control" aria-label="Select language">
      <div className="segmented-track">
        <div
          className="active-pill-bg"
          style={{ transform: `translateX(${activeOffset}%)` }}
        />
        {locales.map((loc) => (
          <button
            key={loc}
            onClick={() => switchLocale(loc)}
            className={`segment-btn${current === loc ? " active" : ""}`}
            aria-pressed={current === loc}
          >
            {localeLabels[loc]}
          </button>
        ))}
      </div>
    </div>
  );
}
