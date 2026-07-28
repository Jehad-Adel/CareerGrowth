"use client";

import { useEffect } from "react";

/**
 * Inertial wheel scrolling for the landing page.
 *
 * Landing only, on purpose. Lenis drives the *real* window scroll position
 * every frame rather than transforming a wrapper, so `position: sticky`, hash
 * links, the scrollbar and `scrollY` all keep working — but it still owns a
 * requestAnimationFrame loop and intercepts wheel events. That is a fair trade
 * for a marketing page and a bad one for `/chat` or `/interview`, where the
 * cost lands while somebody is typing and every inner scroll pane would need
 * an opt-out marker. Those routes stay on native scrolling.
 *
 * Renders nothing; it exists for its effect.
 */
export function SmoothScroll() {
  useEffect(() => {
    // Smoothing is motion. Somebody who asked the OS for less of it gets the
    // browser's own scrolling, and Lenis is never even downloaded.
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    let lenis: { destroy: () => void } | null = null;
    let cancelled = false;

    // Imported inside the effect so the library stays out of the initial
    // bundle: the hero is interactive before this ever starts fetching.
    void import("lenis").then(({ default: Lenis }) => {
      if (cancelled) return;
      const instance = new Lenis({
        // Wheel only. Touch scrolling is already inertial natively, and
        // `syncTouch` replaces that with a worse imitation.
        smoothWheel: true,
        syncTouch: false,
        // Lower lerp = longer glide. 0.12 lands just past the browser's own
        // feel without the drifting that makes a page hard to aim.
        lerp: 0.12,
        wheelMultiplier: 1,
        // Lenis animates hash links itself; CSS `scroll-behavior: smooth`
        // would otherwise fight it for the same scroll position. The
        // `html.lenis` rule in globals.css disables the CSS one.
        anchors: { offset: -80 },
        autoRaf: true,
      });
      lenis = instance;
    });

    return () => {
      cancelled = true;
      lenis?.destroy();
    };
  }, []);

  return null;
}
