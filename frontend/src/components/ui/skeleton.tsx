import { cn } from "@/lib/utils";

/**
 * A pulsing placeholder block.
 *
 * `aria-hidden` on purpose: the surrounding region carries the announcement
 * (see the `role="status"` wrappers in components/skeletons.tsx), so a screen
 * reader hears "loading" once instead of once per grey box.
 */
function Skeleton({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="skeleton"
      aria-hidden
      className={cn("animate-pulse rounded-md bg-muted", className)}
      {...props}
    />
  );
}

export { Skeleton };
