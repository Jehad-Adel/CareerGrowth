"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { PanelLeftClose } from "lucide-react";

import { Logo } from "@/components/brand/logo";
import { navItems } from "@/lib/nav";
import { cn } from "@/lib/utils";

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    const pref = localStorage.getItem("cf-sidebar-collapsed") === "1";
    const id = requestAnimationFrame(() => setCollapsed(pref));
    return () => cancelAnimationFrame(id);
  }, []);

  const toggle = () =>
    setCollapsed((c) => {
      const next = !c;
      localStorage.setItem("cf-sidebar-collapsed", next ? "1" : "0");
      return next;
    });

  return (
    <aside
      className={cn(
        "sticky top-0 flex h-screen shrink-0 flex-col border-r border-sidebar-border bg-sidebar transition-[width] duration-200",
        collapsed ? "w-16" : "w-60",
      )}
    >
      <Link
        href="/dashboard"
        className={cn(
          "flex items-center py-5",
          collapsed ? "justify-center px-0" : "gap-2.5 px-5",
        )}
      >
        <Logo />
        {!collapsed && (
          <span className="leading-none">
            <span className="block font-heading text-lg font-semibold text-sidebar-foreground">
              CareerFarm
            </span>
            <span className="mt-0.5 block font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              Grow your career
            </span>
          </span>
        )}
      </Link>

      <nav className="flex flex-1 flex-col gap-0.5 overflow-y-auto px-3">
        {navItems.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(`${href}/`);
          return (
            <Link
              key={href}
              href={href}
              aria-current={active ? "page" : undefined}
              title={collapsed ? label : undefined}
              className={cn(
                "flex items-center gap-3 rounded-lg py-2 text-sm outline-none transition-colors focus-visible:ring-2 focus-visible:ring-ring",
                collapsed ? "justify-center px-0" : "px-3",
                active
                  ? "bg-sidebar-accent font-medium text-sidebar-accent-foreground"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent/60 hover:text-sidebar-foreground",
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {!collapsed && label}
            </Link>
          );
        })}
      </nav>

      {!collapsed && (
        <div className="m-3 rounded-xl border border-sidebar-border bg-background/40 p-3">
          <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            Today
          </p>
          <p className="mt-1 text-sm text-sidebar-foreground">
            Tend one plant. Small, daily growth compounds.
          </p>
        </div>
      )}

      <button
        type="button"
        onClick={toggle}
        aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        className={cn(
          "m-3 flex items-center gap-2 rounded-lg border border-sidebar-border py-2 text-sm text-muted-foreground outline-none transition-colors hover:bg-sidebar-accent/60 hover:text-sidebar-foreground focus-visible:ring-2 focus-visible:ring-ring",
          collapsed ? "justify-center px-0" : "px-3",
        )}
      >
        <PanelLeftClose
          className={cn("h-4 w-4 shrink-0 transition-transform", collapsed && "rotate-180")}
        />
        {!collapsed && "Collapse"}
      </button>
    </aside>
  );
}
