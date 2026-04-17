import type { Metadata } from "next";
import { Fraunces, Lora, Martian_Mono } from "next/font/google";
import { cookies } from "next/headers";
import { NextIntlClientProvider } from "next-intl";
import "./globals.css";
import { defaultLocale, type Locale, locales } from "../i18n-config";

const display = Fraunces({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-display",
  display: "swap",
});

const body = Lora({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-body",
  display: "swap",
});

const mono = Martian_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "KrishiCFO",
  description: "Season-wise commodity intelligence dashboard",
};

export default async function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const cookieStore = cookies();
  const rawLocale = cookieStore.get("locale")?.value ?? defaultLocale;
  const locale: Locale = locales.includes(rawLocale as Locale)
    ? (rawLocale as Locale)
    : defaultLocale;

  // Dynamic import so only the active locale bundle is loaded
  const messages = (await import(`../messages/${locale}.json`)).default;

  return (
    <html lang={locale}>
      <body className={`${display.variable} ${body.variable} ${mono.variable}`}>
        <NextIntlClientProvider locale={locale} messages={messages}>
          {children}
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
