"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { navItems } from "@/lib/nav";
import { cn } from "@/lib/utils";

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex w-60 shrink-0 flex-col border-r border-sidebar-border bg-sidebar">
      <Link href="/dashboard" className="flex items-center gap-2.5 px-5 py-5">
        <span className="grid h-9 w-9 place-items-center rounded-xl bg-primary/12 text-xl">
          🌱
        </span>
        <span className="leading-none">
          <span className="block font-heading text-lg font-semibold text-sidebar-foreground">
            CareerFarm
          </span>
          <span className="mt-0.5 block font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            Grow your career
          </span>
        </span>
      </Link>

      <nav className="flex flex-1 flex-col gap-0.5 px-3">
        {navItems.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(`${href}/`);
          return (
            <Link
              key={href}
              href={href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                active
                  ? "bg-sidebar-accent font-medium text-sidebar-accent-foreground"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent/60 hover:text-sidebar-foreground",
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="m-3 rounded-xl border border-sidebar-border bg-background/40 p-3">
        <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
          Today
        </p>
        <p className="mt-1 text-sm text-sidebar-foreground">
          Tend one plant. Small, daily growth compounds.
        </p>
      </div>
    </aside>
  );
}
