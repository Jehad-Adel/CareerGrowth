"use client";

import { AlertCircle, BellOff } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/utils";

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
  const [notifications, setNotifications] =
    useState<NotificationItem[]>(initialNotifications);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState<string | null>(null);

  async function handleMarkRead(id: string) {
    const before = notifications;
    setError(null);
    setPending(id);
    // Optimistic, then rolled back if the write fails — the previous version
    // applied it unconditionally and left the UI lying about the database.
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n)),
    );
    try {
      const res = await markRead(id);
      if (!res.ok) {
        setNotifications(before);
        setError(res.error ?? "Could not dismiss that notification.");
      }
    } finally {
      setPending(null);
    }
  }

  async function handleMarkAllRead() {
    const before = notifications;
    setError(null);
    setPending("all");
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    try {
      const res = await markAllRead();
      if (!res.ok) {
        setNotifications(before);
        setError(res.error ?? "Could not mark everything read.");
      }
    } finally {
      setPending(null);
    }
  }

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <div className="space-y-4">
      {error ? (
        <div
          role="alert"
          className="flex items-start gap-2.5 rounded-lg bg-destructive/10 px-3.5 py-2.5 text-xs text-destructive"
        >
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      ) : null}

      {notifications.length === 0 ? (
        <div className="rounded-2xl border bg-card p-8 text-center">
          <BellOff
            className="mx-auto mb-3 h-8 w-8 text-muted-foreground"
            aria-hidden
          />
          <p className="font-medium">No notifications yet</p>
          <p className="mt-1 text-sm text-muted-foreground">
            You&apos;ll hear from us when a roadmap step is due or a streak is
            about to lapse.
          </p>
        </div>
      ) : null}

      {unreadCount > 0 ? (
        <div className="flex justify-end">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleMarkAllRead}
            disabled={pending !== null}
          >
            Mark all read ({unreadCount})
          </Button>
        </div>
      ) : null}

      <ul className="space-y-4">
        {notifications.map((n) => (
          <li
            key={n.id}
            className={`rounded-2xl border p-4 transition-colors sm:p-5 ${
              !n.read ? "border-primary/30 bg-primary/[0.02]" : "bg-card"
            }`}
          >
            <div className="flex items-start justify-between gap-3 sm:gap-4">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  {!n.read ? (
                    <span
                      className="h-2 w-2 shrink-0 rounded-full bg-primary"
                      aria-hidden
                    />
                  ) : null}
                  <h3 className="truncate text-sm font-medium">
                    {!n.read ? <span className="sr-only">Unread. </span> : null}
                    {n.title}
                  </h3>
                </div>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  <time dateTime={n.created_at}>
                    {formatDate(n.created_at)}
                  </time>{" "}
                  &middot; {n.type.replace(/_/g, " ")}
                </p>
              </div>
              {!n.read ? (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleMarkRead(n.id)}
                  disabled={pending !== null}
                  aria-label={`Dismiss notification: ${n.title}`}
                >
                  Dismiss
                </Button>
              ) : null}
            </div>
            {n.body ? (
              <p className="mt-2 text-sm text-muted-foreground">{n.body}</p>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
