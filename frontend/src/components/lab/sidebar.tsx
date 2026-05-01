"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { UserButton } from "@clerk/nextjs";
import { useLabStore } from "@/stores/lab-store";
import {
  MessageSquare,
  LayoutGrid,
  Eye,
  FlaskConical,
  BarChart3,
  BookOpen,
  ClipboardList,
  Settings,
  UserPlus,
} from "lucide-react";

const navItems = [
  { icon: MessageSquare, label: "Chat", href: "/lab", tool: "chat" },
  { icon: LayoutGrid, label: "Plates", href: "/lab/plates", tool: "plates" },
  {
    icon: Eye,
    label: "Microscopy",
    href: "/lab/microscopy",
    tool: "microscopy",
  },
  {
    icon: FlaskConical,
    label: "Samples",
    href: "/lab/samples",
    tool: "samples",
  },
  {
    icon: BookOpen,
    label: "Notebook",
    href: "/lab/eln",
    tool: "eln",
  },
  {
    icon: ClipboardList,
    label: "Protocols",
    href: "/lab/protocols",
    tool: "protocols",
  },
  {
    icon: BarChart3,
    label: "Processing",
    href: "/lab/processing",
    tool: "processing",
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const setActiveTool = useLabStore((s) => s.setActiveTool);
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);

  function isActive(href: string) {
    if (href === "/lab") return pathname === "/lab";
    return pathname.startsWith(href);
  }

  return (
    <aside className="flex flex-col items-center w-14 shrink-0 bg-charcoal py-4 relative z-50">
      {/* Logo */}
      <Link
        href="/lab"
        className="flex items-center justify-center w-9 h-9 rounded-lg bg-amber text-charcoal font-serif font-bold text-lg mb-6 hover:bg-amber-light transition-colors"
      >
        R
      </Link>

      {/* Navigation */}
      <nav className="flex flex-col items-center gap-1 flex-1">
        {navItems.map((item) => {
          const active = isActive(item.href);
          const Icon = item.icon;
          return (
            <div
              key={item.tool}
              className="relative"
              onMouseEnter={() => setHoveredItem(item.tool)}
              onMouseLeave={() => setHoveredItem(null)}
            >
              <Link
                href={item.href}
                onClick={() => setActiveTool(item.tool)}
                className={`flex items-center justify-center w-10 h-10 rounded-lg transition-all duration-150 ${
                  active
                    ? "bg-amber/20 text-amber"
                    : "text-white/50 hover:text-white/80 hover:bg-white/5"
                }`}
              >
                <Icon size={20} strokeWidth={active ? 2 : 1.5} />
              </Link>

              {/* Tooltip */}
              {hoveredItem === item.tool && (
                <div className="absolute left-full ml-3 top-1/2 -translate-y-1/2 bg-charcoal-light text-white text-xs font-medium px-2.5 py-1.5 rounded-md whitespace-nowrap shadow-lg pointer-events-none z-[100]">
                  {item.label}
                  <div className="absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent border-r-charcoal-light" />
                </div>
              )}
            </div>
          );
        })}
      </nav>

      {/* Bottom: Invite + Settings + Avatar */}
      <div className="flex flex-col items-center gap-2">
        <div
          className="relative"
          onMouseEnter={() => setHoveredItem("invite")}
          onMouseLeave={() => setHoveredItem(null)}
        >
          <Link
            href="/invite"
            className="flex items-center justify-center w-10 h-10 rounded-lg text-white/50 hover:text-amber hover:bg-amber/10 transition-all duration-150"
          >
            <UserPlus size={20} strokeWidth={1.5} />
          </Link>
          {hoveredItem === "invite" && (
            <div className="absolute left-full ml-3 top-1/2 -translate-y-1/2 bg-charcoal-light text-white text-xs font-medium px-2.5 py-1.5 rounded-md whitespace-nowrap shadow-lg pointer-events-none z-[100]">
              Invite
              <div className="absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent border-r-charcoal-light" />
            </div>
          )}
        </div>

        <div
          className="relative"
          onMouseEnter={() => setHoveredItem("settings")}
          onMouseLeave={() => setHoveredItem(null)}
        >
          <Link
            href="/lab/settings"
            className="flex items-center justify-center w-10 h-10 rounded-lg text-white/50 hover:text-white/80 hover:bg-white/5 transition-all duration-150"
          >
            <Settings size={20} strokeWidth={1.5} />
          </Link>
          {hoveredItem === "settings" && (
            <div className="absolute left-full ml-3 top-1/2 -translate-y-1/2 bg-charcoal-light text-white text-xs font-medium px-2.5 py-1.5 rounded-md whitespace-nowrap shadow-lg pointer-events-none z-[100]">
              Settings
              <div className="absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent border-r-charcoal-light" />
            </div>
          )}
        </div>

        <UserButton
          appearance={{
            elements: {
              avatarBox: "w-8 h-8 border-2 border-amber/50",
            },
          }}
        />
      </div>
    </aside>
  );
}
