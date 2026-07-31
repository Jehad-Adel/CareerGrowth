"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { markAllRead, markRead } from "./actions";

type NotificationItem = {
  id: string;
  type: string;
  title: string;
  body: string;
  data: Record<string, unknown>;
  read: boolean;
  created_at: string;
};

export function NotificationsBody({
  initialNotifications = [],
}: {
  initialNotifications?: NotificationItem[];
}) {
  const [notifications, setNotifications] = useState<NotificationItem[]>(initialNotifications);

  async function handleMarkRead(id: string) {
    await markRead(id);
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
  }

  async function handleMarkAllRead() {
    await markAllRead();
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  }

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <div className="space-y-4">
      {notifications.length === 0 && (
        <div className="rounded-2xl border bg-card p-6 text-center">
          <p className="text-muted-foreground">No notifications yet.</p>
        </div>
      )}

      {unreadCount > 0 && (
        <div className="flex justify-end">
          <Button variant="ghost" size="sm" onClick={handleMarkAllRead}>
            Mark all read ({unreadCount})
          </Button>
        </div>
      )}

      {notifications.map((n) => (
        <div
          key={n.id}
          className={`rounded-2xl border p-5 transition-colors ${
            !n.read ? "border-primary/30 bg-primary/[0.02]" : "bg-card"
          }`}
        >
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                {!n.read && <span className="h-2 w-2 rounded-full bg-primary shrink-0" />}
                <h3 className="text-sm font-medium truncate">{n.title}</h3>
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                {new Date(n.created_at).toLocaleDateString()} &middot; {n.type.replace(/_/g, " ")}
              </p>
            </div>
            {!n.read && (
              <Button variant="ghost" size="sm" onClick={() => handleMarkRead(n.id)}>
                Dismiss
              </Button>
            )}
          </div>
          {n.body && <p className="text-sm text-muted-foreground mt-2">{n.body}</p>}
        </div>
      ))}
    </div>
  );
}
