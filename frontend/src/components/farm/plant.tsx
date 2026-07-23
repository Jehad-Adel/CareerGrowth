import type { GrowthStage } from "@/types";
import { cn } from "@/lib/utils";

const bed = (
  <path d="M8 50 Q24 44 40 50 L40 52 Q24 47 8 52 Z" fill="var(--soil)" opacity="0.35" />
);

function Seed() {
  return (
    <>
      {bed}
      <circle cx="24" cy="46" r="2.6" fill="var(--harvest)" />
    </>
  );
}

function Sprout() {
  return (
    <>
      {bed}
      <path
        d="M24 48 C24 42 24 40 24 34"
        stroke="var(--sprout)"
        strokeWidth="2"
        fill="none"
        strokeLinecap="round"
      />
      <path d="M24 39 C20 37 17 38 16 33 C21 32 24 34 24 39 Z" fill="var(--sprout)" />
      <path d="M24 39 C28 37 31 38 32 33 C27 32 24 34 24 39 Z" fill="var(--sprout)" />
    </>
  );
}

function Growing() {
  return (
    <>
      {bed}
      <path
        d="M24 48 L24 26"
        stroke="var(--soil)"
        strokeWidth="2.4"
        fill="none"
        strokeLinecap="round"
      />
      <circle cx="24" cy="23" r="9" fill="var(--sprout)" />
      <circle cx="16" cy="28" r="6" fill="var(--sprout)" opacity="0.92" />
      <circle cx="32" cy="28" r="6" fill="var(--sprout)" opacity="0.92" />
    </>
  );
}

function Tree() {
  return (
    <>
      {bed}
      <rect x="22" y="30" width="4" height="19" rx="2" fill="var(--soil)" />
      <circle cx="24" cy="22" r="13" fill="var(--sprout)" />
      <circle cx="14" cy="26" r="8" fill="var(--sprout)" />
      <circle cx="34" cy="26" r="8" fill="var(--sprout)" />
      <circle cx="24" cy="15" r="9" fill="var(--sprout)" />
      <circle cx="20" cy="20" r="2.4" fill="var(--harvest)" />
      <circle cx="29" cy="24" r="2.4" fill="var(--harvest)" />
    </>
  );
}

const shapes: Record<GrowthStage, () => React.ReactElement> = {
  seed: Seed,
  sprout: Sprout,
  growing: Growing,
  tree: Tree,
};

export function Plant({
  stage,
  className,
}: {
  stage: GrowthStage;
  className?: string;
}) {
  const Shape = shapes[stage];
  return (
    <svg
      viewBox="0 0 48 56"
      className={cn("h-full w-full", className)}
      role="img"
      aria-label={`${stage} plant`}
    >
      <Shape />
    </svg>
  );
}
