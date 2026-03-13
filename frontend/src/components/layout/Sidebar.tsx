"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: "📊" },
  { href: "/stable", label: "Stall", icon: "🐴" },
  { href: "/races", label: "Lopp", icon: "🏁" },
  { href: "/market", label: "Marknad", icon: "🏪" },
  { href: "/drivers", label: "Kuskar", icon: "👤" },
  { href: "/breeding", label: "Avel", icon: "🐣" },
  { href: "/sponsors", label: "Sponsorer", icon: "🤝" },
  { href: "/finances", label: "Ekonomi", icon: "💰" },
  { href: "/leaderboard", label: "Topplista", icon: "🏆" },
  { href: "/horse-database", label: "Databas", icon: "📋" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 min-h-screen bg-trav-card border-r border-trav-border flex flex-col">
      <div className="p-5 border-b border-trav-border">
        <h1 className="text-xl font-bold text-trav-gold tracking-tight">TravManager</h1>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {NAV_ITEMS.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors",
              pathname.startsWith(item.href)
                ? "bg-trav-active text-trav-gold"
                : "text-gray-400 hover:text-gray-200 hover:bg-trav-hover"
            )}
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </Link>
        ))}
      </nav>
    </aside>
  );
}
