import { Suspense } from "react";

import { CardSkeleton } from "@/components/skeletons";

import { NotificationsBody } from "./notifications-body";

export const metadata = { title: "Notifications — CareerFarm" };

export default function NotificationsPage() {
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
        <NotificationsBody />
      </Suspense>
    </div>
  );
}
