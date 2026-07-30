import * as React from "react"

import { cn } from "@/lib/utils"

function Select({ className, children, defaultValue, value, onValueChange, name, ...props }: {
  className?: string;
  children: React.ReactNode;
  defaultValue?: string;
  value?: string;
  onValueChange?: (value: string) => void;
  name?: string;
}) {
  return (
    <div data-slot="select" className={cn("relative", className)} {...props}>
      <select
        name={name}
        defaultValue={defaultValue}
        value={value}
        onChange={onValueChange ? (e) => onValueChange(e.target.value) : undefined}
        className="flex h-11 w-full rounded-lg border border-input bg-transparent px-3 py-2 text-sm transition-colors outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50 aria-invalid:border-destructive dark:bg-input/30"
      >
        {children}
      </select>
    </div>
  )
}

function SelectTrigger({ className, children, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="select-trigger"
      className={cn(
        "flex h-11 w-full items-center justify-between rounded-lg border border-input bg-transparent px-3 py-2 text-sm transition-colors outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

function SelectValue({ className, placeholder, ...props }: { className?: string; placeholder?: string }) {
  return (
    <span
      data-slot="select-value"
      className={cn("text-muted-foreground", className)}
      {...props}
    >
      {placeholder || "Select..."}
    </span>
  )
}

function SelectContent({ className, children, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="select-content"
      className={cn(
        "absolute z-50 mt-1 w-full rounded-lg border bg-popover p-1 shadow-md",
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

function SelectItem({ className, children, value, ...props }: { className?: string; children: React.ReactNode; value: string } & React.ComponentProps<"option">) {
  return (
    <option
      value={value}
      className={cn(
        "relative flex w-full cursor-default items-center rounded-md px-2 py-1.5 text-sm outline-none hover:bg-muted focus:bg-muted",
        className
      )}
      {...props}
    >
      {children}
    </option>
  )
}

export { Select, SelectTrigger, SelectValue, SelectContent, SelectItem }
