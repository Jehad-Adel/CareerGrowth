import {
  Brain,
  FileText,
  Home,
  Map,
  MessageCircle,
  Mic,
  Sprout,
  Target,
  ClipboardList,
  Video,
  Bell,
  type LucideIcon,
} from "lucide-react";

import type { ProtectedRoute } from "@/lib/routes";

export type NavItem = {
  /**
   * Constrained to `lib/routes.ts`, so a new sidebar entry that was never
   * added to the guard list fails the type check instead of quietly serving
   * its app shell to logged-out visitors.
   */
  href: ProtectedRoute;
  label: string;
  icon: LucideIcon;
};

/** Primary app navigation — mirrors the platform's feature modules. */
export const navItems: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: Home },
  { href: "/farm", label: "My Farm", icon: Sprout },
  { href: "/cv", label: "CV Studio", icon: FileText },
  { href: "/jobs", label: "Job Match", icon: Target },
  { href: "/applications", label: "Applications", icon: ClipboardList },
  { href: "/interview", label: "Interview Coach", icon: Mic },
  { href: "/roadmap", label: "Roadmap", icon: Map },
  { href: "/quiz", label: "Quiz", icon: Brain },
  { href: "/video", label: "Video", icon: Video },
  { href: "/offers", label: "Offer Evaluator", icon: Target },
  { href: "/notifications", label: "Alerts", icon: Bell },
  { href: "/chat", label: "Career Chat", icon: MessageCircle },
];
