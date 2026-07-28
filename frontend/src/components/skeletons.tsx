// Loading placeholders, shaped like the thing they stand in for.
//
// Every one of these mirrors the real component's box model — same paddings,
// same grid, same heights — so streamed content lands without shifting the
// layout under the reader's eyes.

import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

/**
 * Wraps a skeleton region so assistive tech announces it once. The blocks
 * inside are `aria-hidden`, so this is the only thing that speaks.
 */
export function Loading({
  label,
  className,
  children,
}: {
  label: string;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div role="status" aria-live="polite" className={className}>
      <span className="sr-only">{label}</span>
      {children}
    </div>
  );
}

/** Matches layout/page-header.tsx. */
export function PageHeaderSkeleton() {
  return (
    <div className="mb-8">
      <Skeleton className="h-3 w-24" />
      <Skeleton className="mt-2 h-9 w-72 max-w-full" />
      <Skeleton className="mt-3 h-4 w-full max-w-2xl" />
    </div>
  );
}

/** Matches layout/stat.tsx. */
export function StatSkeleton() {
  return (
    <div className="rounded-2xl border bg-card p-5">
      <Skeleton className="h-3 w-16" />
      <Skeleton className="mt-3 h-7 w-20" />
      <Skeleton className="mt-2 h-3 w-24" />
    </div>
  );
}

export function StatGridSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {Array.from({ length: count }, (_, i) => (
        <StatSkeleton key={i} />
      ))}
    </div>
  );
}

/** A generic bordered card with a heading and a few text lines. */
export function CardSkeleton({
  lines = 3,
  className,
}: {
  lines?: number;
  className?: string;
}) {
  return (
    <div className={cn("rounded-2xl border bg-card p-6", className)}>
      <Skeleton className="h-5 w-40" />
      <div className="mt-4 space-y-2.5">
        {Array.from({ length: lines }, (_, i) => (
          <Skeleton
            key={i}
            className="h-3.5"
            style={{ width: `${100 - i * 12}%` }}
          />
        ))}
      </div>
    </div>
  );
}

/** The XP bar card used on the dashboard and the farm. */
export function ProgressCardSkeleton() {
  return (
    <div className="rounded-2xl border bg-card p-6">
      <div className="flex justify-between">
        <Skeleton className="h-3 w-20" />
        <Skeleton className="h-3 w-16" />
      </div>
      <Skeleton className="mt-2 h-1.5 w-full rounded-full" />
      <Skeleton className="mt-3 h-3 w-40" />
    </div>
  );
}

/** Matches farm-plot.tsx's plant cell: a 24-unit bed plus two label lines. */
export function PlantSkeleton() {
  return (
    <div className="flex flex-col items-center gap-2">
      <Skeleton className="h-24 w-full rounded-xl" />
      <Skeleton className="h-3.5 w-16" />
      <Skeleton className="h-2.5 w-10" />
    </div>
  );
}

export function PlotSkeleton({ count = 12 }: { count?: number }) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <Skeleton className="h-5 w-28" />
        <span className="h-px flex-1 bg-border" />
      </div>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
        {Array.from({ length: count }, (_, i) => (
          <PlantSkeleton key={i} />
        ))}
      </div>
    </div>
  );
}

/** The activity feed on the dashboard and farm. */
export function FeedSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <ol className="space-y-3">
      {Array.from({ length: rows }, (_, i) => (
        <li
          key={i}
          className="flex items-start justify-between gap-3 rounded-xl border bg-card px-4 py-3"
        >
          <div className="min-w-0 flex-1">
            <Skeleton className="h-3.5 w-2/3" />
            <Skeleton className="mt-2 h-2.5 w-20" />
          </div>
          <Skeleton className="h-3 w-8 shrink-0" />
        </li>
      ))}
    </ol>
  );
}

// --- Route bodies ---
//
// Each route's `loading.tsx` renders the header placeholder plus one of these.
// The page then reuses the same component as its inner Suspense fallback, so a
// soft navigation and a cold load show the identical shape.

export function DashboardSkeleton() {
  return (
    <Loading label="Loading your dashboard">
      <StatGridSkeleton />
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <div className="rounded-2xl border bg-card p-6">
            <Skeleton className="h-5 w-28" />
            <div className="mt-5 grid grid-cols-4 gap-3 sm:grid-cols-6">
              {Array.from({ length: 6 }, (_, i) => (
                <PlantSkeleton key={i} />
              ))}
            </div>
          </div>
          <CardSkeleton lines={5} />
        </div>
        <aside className="space-y-6">
          <ProgressCardSkeleton />
          <CardSkeleton lines={2} />
        </aside>
      </div>
    </Loading>
  );
}

export function FarmSkeleton() {
  return (
    <Loading label="Loading your farm">
      <StatGridSkeleton />
      <div className="mb-8">
        <ProgressCardSkeleton />
      </div>
      <div className="grid gap-8 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <PlotSkeleton />
        </div>
        <aside>
          <Skeleton className="mb-3 h-5 w-32" />
          <FeedSkeleton />
        </aside>
      </div>
    </Loading>
  );
}

export function CvSkeleton() {
  return (
    <Loading label="Loading your CV analysis" className="grid gap-6 lg:grid-cols-3">
      <div className="space-y-6">
        <div className="rounded-2xl border bg-card p-6">
          <Skeleton className="h-[9.5rem] w-full rounded-xl" />
          <Skeleton className="mt-4 h-9 w-full" />
          <Skeleton className="mx-auto mt-3 h-3 w-32" />
        </div>
        <CardSkeleton lines={4} />
      </div>
      <div className="space-y-6 lg:col-span-2">
        <CardSkeleton lines={3} />
        <div className="grid gap-6 sm:grid-cols-2">
          <CardSkeleton lines={3} />
          <CardSkeleton lines={3} />
        </div>
      </div>
    </Loading>
  );
}

/** One column of results beside the form, which renders immediately. */
export function ResultsSkeleton({ label }: { label: string }) {
  return (
    <Loading label={label} className="space-y-6">
      <div className="rounded-2xl border bg-card p-6">
        <div className="flex flex-wrap items-center gap-4 sm:gap-6">
          <Skeleton className="h-20 w-20 shrink-0 rounded-full" />
          <div className="min-w-0 flex-1 space-y-2">
            <Skeleton className="h-5 w-40" />
            <Skeleton className="h-3.5 w-full" />
            <Skeleton className="h-3.5 w-3/4" />
          </div>
        </div>
      </div>
      <CardSkeleton lines={4} />
    </Loading>
  );
}

export function RoadmapSkeleton() {
  return (
    <Loading label="Loading your roadmap">
      <div className="mb-6 rounded-2xl border bg-card p-6">
        <Skeleton className="h-9 w-full max-w-sm" />
      </div>
      <div className="mb-6">
        <ProgressCardSkeleton />
      </div>
      <div className="space-y-4">
        {Array.from({ length: 3 }, (_, i) => (
          <CardSkeleton key={i} lines={3} />
        ))}
      </div>
    </Loading>
  );
}

export function InterviewSkeleton() {
  return (
    <Loading label="Loading your interview" className="grid gap-6 lg:grid-cols-3">
      <div className="space-y-6 lg:col-span-2">
        <CardSkeleton lines={1} />
        <CardSkeleton lines={4} />
        <CardSkeleton lines={4} />
      </div>
      <aside className="space-y-6">
        <CardSkeleton lines={4} />
      </aside>
    </Loading>
  );
}

export function ChatSkeleton() {
  return (
    <Loading label="Loading your conversation" className="space-y-4 p-6">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className={cn("flex gap-3", i % 2 === 1 && "flex-row-reverse")}
        >
          {i % 2 === 0 ? (
            <Skeleton className="h-8 w-8 shrink-0 rounded-full" />
          ) : null}
          <Skeleton
            className={cn("h-16 rounded-2xl", i % 2 === 0 ? "w-3/5" : "w-2/5")}
          />
        </div>
      ))}
    </Loading>
  );
}

/** Matches layout/topbar.tsx so the header does not jump when the profile lands. */
export function TopbarSkeleton() {
  return (
    <header className="sticky top-0 z-30 flex items-center gap-2 border-b bg-background/80 px-3 py-2.5 backdrop-blur sm:gap-4 sm:px-6 sm:py-3">
      {/* Mirrors the drawer trigger and wordmark the real topbar shows below
          `lg`; without them the header jumps sideways when the profile lands. */}
      <Skeleton className="h-11 w-11 rounded-lg lg:hidden" />
      <Skeleton className="h-6 w-32 lg:hidden" />
      <div className="ms-auto flex items-center gap-2 sm:gap-5">
        <Skeleton className="h-4 w-10" />
        <div className="hidden w-44 sm:block">
          <div className="flex justify-between">
            <Skeleton className="h-2.5 w-20" />
            <Skeleton className="h-2.5 w-10" />
          </div>
          <Skeleton className="mt-1.5 h-1.5 w-full rounded-full" />
        </div>
        <Skeleton className="h-9 w-9 rounded-full sm:h-10 sm:w-10" />
        <Skeleton className="h-10 w-10 rounded-xl" />
      </div>
    </header>
  );
}
