"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type Props = {
  activeCommodityLabel?: string;
};

const LINKS = [
  { href: "/", label: "Home" },
  { href: "/dashboard", label: "Dashboard" },
];

export function TopNav({ activeCommodityLabel }: Props) {
  const pathname = usePathname();

  return (
    <header className="topnav">
      <Link className="brand" href="/">
        <span className="brand-mark" />
        <span>KrishiCFO</span>
      </Link>
      <nav>
        {LINKS.map((link) => {
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
          <span className="mono">Detail: {activeCommodityLabel}</span>
        ) : (
          <span className="mono">Seasonal commodity mode</span>
        )}
      </div>
    </header>
  );
}
