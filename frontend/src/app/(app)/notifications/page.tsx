import { unstable_rethrow } from "next/navigation";
import { Suspense } from "react";

import { PageHeader } from "@/components/layout/page-header";
import { CardSkeleton } from "@/components/skeletons";
import { getAllNotifications } from "@/lib/services";

import { NotificationsBody } from "./notifications-body";

// The root layout applies `title.template: "%s · CareerGrowth"`, so repeating
// the suffix here renders it twice.
export const metadata = { title: "Notifications" };

/**
 * An empty list is a reasonable fallback for a feed that failed to load — the
 * page still renders and says there is nothing. It is not a reasonable
 * fallback for an expired session: `getAllNotifications` answers a 401 with
 * `redirect("/login")`, which signals by throwing, and a bare `.catch` caught
 * that too and showed "No notifications yet" instead of bouncing to login.
 */
async function loadNotifications() {
  try {
    return await getAllNotifications();
  } catch (error) {
    unstable_rethrow(error);
    return [];
  }
}

export default async function NotificationsPage() {
  const notifications = await loadNotifications();

  return (
    <div className="mx-auto max-w-2xl">
      <PageHeader
        eyebrow="Alerts"
        title="Notifications"
        subtitle="Deadlines, reminders, and anything that needs you before it lapses."
      />
      <Suspense fallback={<CardSkeleton />}>
        <NotificationsBody initialNotifications={notifications} />
      </Suspense>
    </div>
  );
}
