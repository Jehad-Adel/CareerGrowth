import {
  FileText,
  Home,
  Map,
  MessageCircle,
  Mic,
  Sprout,
  Target,
  type LucideIcon,
} from "lucide-react";

export type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
};

/** Primary app navigation — mirrors the platform's feature modules. */
export const navItems: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: Home },
  { href: "/farm", label: "My Farm", icon: Sprout },
  { href: "/cv", label: "CV Studio", icon: FileText },
  { href: "/jobs", label: "Job Match", icon: Target },
  { href: "/interview", label: "Interview Coach", icon: Mic },
  { href: "/roadmap", label: "Roadmap", icon: Map },
  { href: "/chat", label: "Career Chat", icon: MessageCircle },
];
