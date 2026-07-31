import * as React from "react"
import { ChevronDown } from "lucide-react"

import { cn } from "@/lib/utils"

/**
 * A native `<select>` in the project's field styling.
 *
 * Props land on the `<select>` itself, not the positioning wrapper. They used
 * to spread onto the wrapper `<div>`, so `id` never reached the control and a
 * `<Label htmlFor>` pointed at a div — no label association, and clicking the
 * label did nothing.
 *
 * The `SelectTrigger` / `SelectValue` / `SelectContent` scaffolding that used
 * to sit here mirrored Radix's compound API over a native select that cannot
 * use it. Nothing imported those, so they are gone rather than left as a trap.
 */
function Select({
  className,
  children,
  onValueChange,
  onChange,
  ...props
}: Omit<React.ComponentProps<"select">, "onChange"> & {
  onValueChange?: (value: string) => void
  onChange?: React.ChangeEventHandler<HTMLSelectElement>
}) {
  return (
    <div data-slot="select" className={cn("relative", className)}>
      <select
        data-slot="select-control"
        onChange={(event) => {
          onChange?.(event)
          onValueChange?.(event.target.value)
        }}
        // Padding matches `ui/input.tsx` deliberately. `py-2` against the
        // `md:h-8` height leaves a 16px content box for a 20px line-height,
        // which clips the selected option's descenders — the control looks
        // like it is cut in half. `pr-9` leaves room for the chevron below.
        // No `flex`: a native <select> is a replaced element and does not lay
        // its own text out as flex children.
        className="h-11 w-full appearance-none rounded-lg border border-input bg-transparent py-1 pl-2.5 pr-9 text-base transition-colors outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50 aria-invalid:border-destructive md:h-8 md:text-sm dark:bg-input/30"
        {...props}
      >
        {children}
      </select>
      {/* Replaces the native arrow that `appearance-none` removes. */}
      <ChevronDown
        aria-hidden
        className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
      />
    </div>
  )
}

function SelectItem({
  className,
  children,
  ...props
}: React.ComponentProps<"option">) {
  return (
    <option className={cn("bg-popover text-popover-foreground", className)} {...props}>
      {children}
    </option>
  )
}

export { Select, SelectItem }
