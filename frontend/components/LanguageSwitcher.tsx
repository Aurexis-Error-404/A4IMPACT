"use client";

import { useRouter } from "next/navigation";
import { localeLabels, locales, type Locale } from "../i18n-config";

export function LanguageSwitcher({ current }: { current?: string }) {
  const router = useRouter();

  function switchLocale(locale: Locale) {
    document.cookie = `locale=${locale};path=/;max-age=31536000`;
    router.refresh();
  }

  return (
    <div className="lang-switcher" aria-label="Select language">
      {locales.map((loc) => (
        <button
          key={loc}
          onClick={() => switchLocale(loc)}
          className={`lang-btn${current === loc ? " active" : ""}`}
          aria-pressed={current === loc}
        >
          {localeLabels[loc]}
        </button>
      ))}
    </div>
  );
}
