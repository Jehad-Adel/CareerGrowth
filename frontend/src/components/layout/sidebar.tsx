"use client";

import Link, { useLinkStatus } from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Loader2, PanelLeftClose } from "lucide-react";

import { Logo } from "@/components/brand/logo";
import { navItems } from "@/lib/nav";
import { cn } from "@/lib/utils";

/** Shared with the app layout, which reads the preference server-side. */
export const SIDEBAR_COOKIE = "cf-sidebar-collapsed";

/**
 * Inline navigation hint. Always rendered at a fixed size and toggled by
 * opacity — an element that appears on click would shift the label sideways.
 * Stays invisible when the route was prefetched, which is the common case.
 */
function NavPending() {
  const { pending } = useLinkStatus();
  return (
    <Loader2
      aria-hidden
      className={cn(
        "ml-auto h-3.5 w-3.5 shrink-0 animate-spin transition-opacity",
        pending ? "opacity-100" : "opacity-0",
      )}
    />
  );
}

export function Sidebar({ defaultCollapsed }: { defaultCollapsed: boolean }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(defaultCollapsed);
  const [isSmallScreen, setIsSmallScreen] = useState(false);

  useEffect(() => {
    const mql = window.matchMedia("(max-width: 1023px)");
    const check = () => setIsSmallScreen(mql.matches);
    check();
    mql.addEventListener("change", check);
    return () => mql.removeEventListener("change", check);
  }, []);

  const isCollapsed = isSmallScreen || collapsed;

  const toggle = () =>
    setCollapsed((c) => {
      const next = !c;
      // A cookie, not localStorage: the server needs it to render the right
      // width before hydration.
      document.cookie = `${SIDEBAR_COOKIE}=${next ? "1" : "0"}; path=/; max-age=31536000; samesite=lax`;
      return next;
    });

  return (
    <aside
      className={cn(
        "sticky top-0 flex h-screen shrink-0 flex-col border-r border-sidebar-border bg-sidebar transition-[width] duration-200",
        isCollapsed ? "w-16" : "w-60",
      )}
    >
      <Link
        href="/dashboard"
        className={cn(
          "flex items-center py-5",
          isCollapsed ? "justify-center px-0" : "gap-2.5 px-5",
        )}
      >
        <Logo />
        {!isCollapsed ? (
          <span className="leading-none">
            <span className="block font-heading text-lg font-semibold text-sidebar-foreground">
              CareerFarm
            </span>
            <span className="mt-0.5 block font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              Grow your career
            </span>
          </span>
        ) : null}
      </Link>

      <nav className="flex flex-1 flex-col gap-0.5 overflow-y-auto px-3">
        {navItems.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(`${href}/`);
          return (
            <Link
              key={href}
              href={href}
              aria-current={active ? "page" : undefined}
              title={isCollapsed ? label : undefined}
              className={cn(
                "flex items-center gap-3 rounded-lg py-2.5 text-sm outline-none transition-colors focus-visible:ring-2 focus-visible:ring-ring",
                isCollapsed ? "justify-center px-0" : "px-3",
                active
                  ? "bg-sidebar-accent font-medium text-sidebar-accent-foreground"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent/60 hover:text-sidebar-foreground",
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {!isCollapsed ? (
                <>
                  {label}
                  <NavPending />
                </>
              ) : null}
            </Link>
          );
        })}
      </nav>

      {!isCollapsed ? (
        <div className="m-3 rounded-xl border border-sidebar-border bg-background/40 p-3">
          <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            Today
          </p>
          <p className="mt-1 text-sm text-sidebar-foreground">
            Tend one plant. Small, daily growth compounds.
          </p>
        </div>
      ) : null}

      {!isSmallScreen ? (
        <button
          type="button"
          onClick={toggle}
          aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          className={cn(
            "m-3 flex items-center gap-2 rounded-lg border border-sidebar-border py-2 text-sm text-muted-foreground outline-none transition-colors hover:bg-sidebar-accent/60 hover:text-sidebar-foreground focus-visible:ring-2 focus-visible:ring-ring",
            isCollapsed ? "justify-center px-0" : "px-3",
          )}
        >
          <PanelLeftClose
            className={cn("h-4 w-4 shrink-0 transition-transform", isCollapsed && "rotate-180")}
          />
          {!isCollapsed ? "Collapse" : null}
        </button>
      ) : null}
    </aside>
  );
}
