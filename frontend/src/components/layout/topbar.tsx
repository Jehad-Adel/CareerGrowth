import { Flame, LogOut } from "lucide-react";

import { signOut } from "@/app/(auth)/actions";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import type { Profile } from "@/types";

function initials(name: string) {
  const clean = name.trim();
  if (!clean) return "CF";
  return clean
    .split(/\s+/)
    .map((p) => p[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

export function Topbar({ profile }: { profile: Profile }) {
  const pct = Math.round((profile.xp / profile.xpForNext) * 100);

  return (
    <header className="sticky top-0 z-10 flex items-center gap-4 border-b bg-background/80 px-4 py-3 backdrop-blur sm:px-6">
      <div className="ms-auto flex items-center gap-5">
        <span
          className="flex items-center gap-1.5 font-mono text-sm text-muted-foreground"
          title={`${profile.streakDays}-day streak`}
        >
          <Flame className="h-4 w-4 text-[var(--harvest)]" />
          {profile.streakDays}d
        </span>

        <div
          className="hidden w-44 sm:block"
          role="status"
          aria-label={`Level ${profile.level}, ${profile.levelTitle}: ${profile.xp} of ${profile.xpForNext} XP`}
        >
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

        <Avatar className="h-10 w-10">
          <AvatarFallback className="bg-primary/12 font-medium text-primary">
            {initials(profile.name)}
          </AvatarFallback>
        </Avatar>

        {/* A server action, so logging out works with JavaScript disabled and
            needs no client-side Supabase call. */}
        <form action={signOut}>
          <Button
            type="submit"
            variant="ghost"
            size="icon"
            className="focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
            aria-label="Log out"
            title="Log out"
          >
            <LogOut className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </header>
  );
}
