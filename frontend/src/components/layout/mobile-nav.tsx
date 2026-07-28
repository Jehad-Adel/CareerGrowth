"use client";

import { Menu, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

import { Logo } from "@/components/brand/logo";
import { navItems } from "@/lib/nav";
import { cn } from "@/lib/utils";

/**
 * Navigation drawer for phones and tablets.
 *
 * Below `lg` the sidebar is hidden entirely rather than collapsed to its icon
 * rail: the rail spent 64px of a 375px viewport on eight unlabelled icons,
 * which is both the widest thing on the screen doing the least and a
 * discoverability problem — an icon with no label does not say what it opens.
 * The drawer shows the same items with their labels.
 *
 * Deliberately not a `<dialog>` or a headless dialog dependency: this needs
 * one focus move, Escape, and a scroll lock, and all three are visible here.
 */
export function MobileNav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const panel = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;

    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
        trigger.current?.focus();
      }
    };
    document.addEventListener("keydown", onKey);

    // Scroll lock. Restoring the previous value rather than clearing it keeps
    // any other lock (a modal that opened underneath) intact.
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    // Move focus in, or a keyboard user tabs through the page behind.
    panel.current?.querySelector<HTMLElement>("a, button")?.focus();

    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = previous;
    };
  }, [open]);

  return (
    <>
      <button
        ref={trigger}
        type="button"
        onClick={() => setOpen(true)}
        aria-label="Open navigation"
        aria-expanded={open}
        aria-controls="mobile-nav"
        className="-ms-1 grid h-11 w-11 shrink-0 place-items-center rounded-lg text-muted-foreground outline-none transition-colors hover:bg-accent hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring lg:hidden"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Portalled to <body> on purpose. The topbar this button lives in has
          `backdrop-blur`, and any filter or backdrop-filter on an ancestor
          makes that ancestor the containing block for `position: fixed`
          descendants — so the drawer laid itself out inside the 56px header
          strip instead of over the viewport, which is what "the menu does not
          open" looked like. `open` only becomes true on a click, so this never
          runs during SSR. */}
      {open
        ? createPortal(
        <div className="fixed inset-0 z-50 lg:hidden">
          {/* 60% scrim: at the lighter end of the range the page behind still
              competes with the drawer's own surface in dark mode. */}
          <button
            type="button"
            aria-label="Close navigation"
            onClick={() => setOpen(false)}
            className="absolute inset-0 bg-black/60 backdrop-blur-[2px]"
          />

          <div
            ref={panel}
            id="mobile-nav"
            role="dialog"
            aria-modal="true"
            aria-label="Navigation"
            className="absolute inset-y-0 start-0 flex w-[min(18rem,82vw)] flex-col border-e border-sidebar-border bg-sidebar shadow-2xl"
          >
            <div className="flex items-center justify-between gap-2 px-4 py-4">
              <Link
                href="/dashboard"
                onClick={() => setOpen(false)}
                className="flex items-center gap-2.5"
              >
                <Logo />
                <span className="font-heading text-lg font-semibold text-sidebar-foreground">
                  CareerFarm
                </span>
              </Link>
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label="Close navigation"
                className="grid h-11 w-11 shrink-0 place-items-center rounded-lg text-muted-foreground outline-none transition-colors hover:bg-sidebar-accent/60 hover:text-sidebar-foreground focus-visible:ring-2 focus-visible:ring-ring"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Scrolls on short phones in landscape, where eight 48px rows do
                not fit; `overscroll-contain` keeps that scroll off the page. */}
            <nav className="flex flex-1 flex-col gap-1 overflow-y-auto overscroll-contain px-3 pb-[max(1rem,env(safe-area-inset-bottom))]">
              {navItems.map(({ href, label, icon: Icon }) => {
                const active =
                  pathname === href || pathname.startsWith(`${href}/`);
                return (
                  <Link
                    key={href}
                    href={href}
                    // Closed on click rather than in an effect watching the
                    // pathname: that effect sets state during the render pass
                    // that follows navigation, which React 19's lint flags as
                    // a cascading render.
                    onClick={() => setOpen(false)}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "flex min-h-12 items-center gap-3 rounded-lg px-3 text-sm outline-none transition-colors focus-visible:ring-2 focus-visible:ring-ring",
                      active
                        ? "bg-sidebar-accent font-medium text-sidebar-accent-foreground"
                        : "text-sidebar-foreground/80 hover:bg-sidebar-accent/60 hover:text-sidebar-foreground",
                    )}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    {label}
                  </Link>
                );
              })}
            </nav>
          </div>
        </div>,
            document.body,
          )
        : null}
    </>
  );
}
