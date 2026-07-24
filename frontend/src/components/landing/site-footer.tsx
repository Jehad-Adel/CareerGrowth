import Link from "next/link";

const COLS = [
  {
    title: "Product",
    links: [
      { label: "Dashboard", href: "/dashboard" },
      { label: "Career Farm", href: "/farm" },
      { label: "CV Studio", href: "/cv" },
      { label: "Roadmap", href: "/roadmap" },
    ],
  },
  {
    title: "Prepare",
    links: [
      { label: "Job Match", href: "/jobs" },
      { label: "Interview Coach", href: "/interview" },
      { label: "Career Chat", href: "/chat" },
    ],
  },
  {
    title: "Account",
    links: [
      { label: "Log in", href: "/login" },
      { label: "Get started", href: "/signup" },
    ],
  },
];

export function SiteFooter() {
  return (
    <footer className="border-t bg-card/40">
      <div className="mx-auto grid max-w-6xl gap-10 px-6 py-14 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <span className="flex items-center gap-2">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-primary/12 text-xl">
              🌱
            </span>
            <span className="font-heading text-lg font-semibold">CareerFarm</span>
          </span>
          <p className="mt-3 max-w-xs text-sm text-muted-foreground">
            Grow your career like a farm.
          </p>
        </div>
        {COLS.map((c) => (
          <div key={c.title}>
            <p className="font-mono text-xs uppercase tracking-widest text-muted-foreground">
              {c.title}
            </p>
            <ul className="mt-4 space-y-2.5">
              {c.links.map((l) => (
                <li key={l.label}>
                  <Link
                    href={l.href}
                    className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                  >
                    {l.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="border-t">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-6 py-6 text-sm text-muted-foreground">
          <span>© {new Date().getFullYear()} CareerFarm</span>
          <span className="font-mono text-xs">Grow your career like a farm.</span>
        </div>
      </div>
    </footer>
  );
}
