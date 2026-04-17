export const locales = ["en", "hi", "te"] as const;
export type Locale = (typeof locales)[number];
export const defaultLocale: Locale = "en";

export const localeLabels: Record<Locale, string> = {
  en: "EN",
  hi: "हि",
  te: "తె",
};
