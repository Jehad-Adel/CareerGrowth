import { cookies } from "next/headers";
import { Suspense } from "react";

import { SIDEBAR_COOKIE, Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";
import { TopbarSkeleton } from "@/components/skeletons";
import { getProfile } from "@/lib/services";

/** Split out so the profile round trip suspends the header, not the page. */
async function TopbarSlot() {
  const profile = await getProfile();
  return <Topbar profile={profile} />;
}

export default async function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Read server-side rather than from localStorage in an effect: the sidebar
  // renders at its final width on the first paint instead of snapping shut
  // after hydration.
  const collapsed = (await cookies()).get(SIDEBAR_COOKIE)?.value === "1";

  return (
    <div className="flex min-h-screen">
      <Sidebar defaultCollapsed={collapsed} />
      <div className="flex min-w-0 flex-1 flex-col">
        <Suspense fallback={<TopbarSkeleton />}>
          <TopbarSlot />
        </Suspense>
        <main className="flex-1 px-6 py-8 lg:px-10">{children}</main>
      </div>
    </div>
  );
}
