"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";
import { useMemo } from "react";
import { LanguageSwitcher } from "./LanguageSwitcher";

type Props = {
  activeCommodityLabel?: string;
};

export function TopNav({ activeCommodityLabel }: Props) {
  const pathname = usePathname();
  const t = useTranslations("nav");

  const links = useMemo(
    () => [
      { href: "/", label: t("home") },
      { href: "/dashboard", label: t("dashboard") },
    ],
    [t],
  );

  return (
    <header className="topnav">
      <Link className="brand" href="/">
        <span className="brand-mark" />
        <span>KrishiCFO</span>
      </Link>
      <nav>
        {links.map((link) => {
          const isActive =
            pathname === link.href ||
            (link.href === "/dashboard" && pathname.startsWith("/commodity/"));
          return (
            <Link
              key={link.href}
              href={link.href}
              className={isActive ? "active" : ""}
            >
              {link.label}
            </Link>
          );
        })}
      </nav>
      <div className="topnav-meta">
        {activeCommodityLabel ? (
          <span className="mono">{t("detail")}: {activeCommodityLabel}</span>
        ) : (
          <span className="mono">{t("seasonalMode")}</span>
        )}
        <LanguageSwitcher />
      </div>
    </header>
  );
}
