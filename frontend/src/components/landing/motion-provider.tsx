"use client";

import { domAnimation, LazyMotion } from "motion/react";

/**
 * Loads only the DOM animation feature set (not the full motion bundle) and
 * enforces `m` components via `strict`. Cuts the landing's initial JS.
 */
export function MotionProvider({ children }: { children: React.ReactNode }) {
  return (
    <LazyMotion features={domAnimation} strict>
      {children}
    </LazyMotion>
  );
}
