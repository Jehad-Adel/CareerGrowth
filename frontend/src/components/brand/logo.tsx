import { cn } from "@/lib/utils";

/** Custom sprout mark — two leaves rising from a seed. Themes via currentColor. */
export function LogoMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden>
      <path
        d="M12 21.5V12"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <path
        d="M11.8 12.4C11.8 8.7 9.1 6 5 6c-.4 4.1 2.4 6.4 6.8 6.4Z"
        fill="currentColor"
      />
      <path
        d="M12.3 11.6c0-3.2 2.4-5.6 6-5.2.3 3.6-2.3 5.6-6 5.2Z"
        fill="currentColor"
        opacity="0.82"
      />
      <circle cx="12" cy="21.2" r="1.3" fill="currentColor" />
    </svg>
  );
}

/** Brand mark inside the standard rounded tile. */
export function Logo({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-primary/12",
        className,
      )}
    >
      <LogoMark className="h-5 w-5 text-primary" />
    </span>
  );
}
