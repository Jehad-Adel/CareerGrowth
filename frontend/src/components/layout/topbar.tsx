import { Flame, LogOut } from "lucide-react";
import Link from "next/link";

import { signOut } from "@/app/(auth)/actions";
import { Logo } from "@/components/brand/logo";
import { MobileNav } from "@/components/layout/mobile-nav";
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
    <header className="sticky top-0 z-30 flex items-center gap-2 border-b bg-background/80 px-3 py-2.5 backdrop-blur sm:gap-4 sm:px-6 sm:py-3">
      {/* Below `lg` the sidebar is gone, so the drawer trigger and the wordmark
          are the only things anchoring the page. Both disappear at `lg`, where
          the rail carries them. */}
      <MobileNav />
      <Link href="/dashboard" className="flex items-center gap-2 lg:hidden">
        <Logo />
        <span className="font-heading text-base font-semibold">CareerFarm</span>
      </Link>

      <div className="ms-auto flex min-w-0 items-center gap-2 sm:gap-5">
        <span
          className="flex shrink-0 items-center gap-1.5 font-mono text-sm text-muted-foreground"
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

        <Avatar className="h-9 w-9 shrink-0 sm:h-10 sm:w-10">
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
