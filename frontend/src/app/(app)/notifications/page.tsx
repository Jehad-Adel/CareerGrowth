import { Suspense } from "react";

import { CardSkeleton } from "@/components/skeletons";
import { getAllNotifications } from "@/lib/services";

import { NotificationsBody } from "./notifications-body";

// The root layout applies `title.template: "%s · CareerFarm"`, so repeating
// the suffix here renders it twice.
export const metadata = { title: "Notifications" };

export default async function NotificationsPage() {
  const notifications = await getAllNotifications().catch(() => []);
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Notifications</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Alerts for deadlines, updates, and reminders.
          </p>
        </div>
      </div>
      <Suspense fallback={<CardSkeleton />}>
        <NotificationsBody initialNotifications={notifications} />
      </Suspense>
    </div>
  );
}
