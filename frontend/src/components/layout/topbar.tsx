import { Flame, Search } from "lucide-react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Progress } from "@/components/ui/progress";
import type { Profile } from "@/types";

function initials(name: string) {
  return name
    .split(" ")
    .map((p) => p[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

export function Topbar({ profile }: { profile: Profile }) {
  const pct = Math.round((profile.xp / profile.xpForNext) * 100);

  return (
    <header className="sticky top-0 z-10 flex items-center gap-4 border-b bg-background/80 px-6 py-3 backdrop-blur">
      <div className="relative hidden max-w-xs flex-1 items-center md:flex">
        <Search className="pointer-events-none absolute left-3 h-4 w-4 text-muted-foreground" />
        <input
          type="search"
          placeholder="Search skills, jobs, questions…"
          className="h-9 w-full rounded-lg border bg-card pl-9 pr-3 text-sm outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/30"
        />
      </div>

      <div className="ml-auto flex items-center gap-5">
        <span
          className="flex items-center gap-1.5 font-mono text-sm text-muted-foreground"
          title={`${profile.streakDays}-day streak`}
        >
          <Flame className="h-4 w-4 text-[var(--harvest)]" />
          {profile.streakDays}d
        </span>

        <div className="hidden w-44 sm:block">
          <div className="flex justify-between font-mono text-[11px] text-muted-foreground">
            <span>
              Lv {profile.level} · {profile.levelTitle}
            </span>
            <span>
              {profile.xp}/{profile.xpForNext}
            </span>
          </div>
          <Progress value={pct} className="mt-1 h-1.5" />
        </div>

        <Avatar className="h-9 w-9">
          <AvatarFallback className="bg-primary/12 font-medium text-primary">
            {initials(profile.name)}
          </AvatarFallback>
        </Avatar>
      </div>
    </header>
  );
}
