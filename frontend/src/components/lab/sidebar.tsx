"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { UserButton } from "@clerk/nextjs";
import { useLabStore } from "@/stores/lab-store";
import { cn } from "@/lib/utils";
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
  { icon: MessageSquare, label: "Console",    href: "/lab",            tool: "chat" },
  { icon: LayoutGrid,    label: "Plates",     href: "/lab/plates",     tool: "plates" },
  { icon: Eye,           label: "Microscopy", href: "/lab/microscopy", tool: "microscopy" },
  { icon: FlaskConical,  label: "Inventory",  href: "/lab/samples",    tool: "samples" },
  { icon: BookOpen,      label: "Notebook",   href: "/lab/eln",        tool: "eln" },
  { icon: ClipboardList, label: "Protocols",  href: "/lab/protocols",  tool: "protocols" },
  { icon: BarChart3,     label: "Processing", href: "/lab/processing", tool: "processing" },
];

/** 4-cell illuminated brand mark — same as marketing nav. */
function BrandMark({ size = 32 }: { size?: number }) {
  return (
    <span
      className="inline-grid grid-cols-2 grid-rows-2 gap-[3px] p-[5px] rounded-[5px] bg-surface border border-line-strong"
      style={{ width: size, height: size }}
      aria-hidden="true"
    >
      <span className="rounded-full bg-ink-subtle" />
      <span className="rounded-full bg-ink-subtle" />
      <span className="rounded-full bg-ink-subtle" />
      <span className="rounded-full bg-brand" />
    </span>
  );
}

export default function Sidebar() {
  const pathname = usePathname();
  const setActiveTool = useLabStore((s) => s.setActiveTool);
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);

  function isActive(href: string) {
    if (href === "/lab") return pathname === "/lab";
    return pathname.startsWith(href);
  }

  return (
    <aside className="flex flex-col items-center w-14 shrink-0 bg-bg border-r border-line py-4 relative z-50">
      {/* Brand mark / Home */}
      <Link
        href="/lab"
        className="mb-6 transition-opacity hover:opacity-80"
        title="Resonantia"
      >
        <BrandMark size={32} />
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
                className={cn(
                  "flex items-center justify-center w-10 h-10 rounded-md transition-colors duration-150",
                  active
                    ? "bg-brand-soft text-brand"
                    : "text-ink-muted hover:text-ink hover:bg-bg-sunk"
                )}
                style={
                  active
                    ? { boxShadow: "inset 0 0 0 1px rgba(31, 77, 58, 0.25)" }
                    : undefined
                }
              >
                <Icon size={18} strokeWidth={active ? 2 : 1.6} />
              </Link>

              {hoveredItem === item.tool && (
                <div className="absolute left-full ml-3 top-1/2 -translate-y-1/2 bg-ink text-bg text-xs font-medium px-2.5 py-1.5 rounded-[3px] whitespace-nowrap shadow-md pointer-events-none z-[100] font-mono tracking-[0.02em]">
                  {item.label}
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
            className="flex items-center justify-center w-10 h-10 rounded-md text-ink-muted hover:text-brand hover:bg-brand-soft transition-colors"
          >
            <UserPlus size={18} strokeWidth={1.6} />
          </Link>
          {hoveredItem === "invite" && (
            <div className="absolute left-full ml-3 top-1/2 -translate-y-1/2 bg-ink text-bg text-xs font-medium px-2.5 py-1.5 rounded-[3px] whitespace-nowrap shadow-md pointer-events-none z-[100] font-mono tracking-[0.02em]">
              Invite
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
            className="flex items-center justify-center w-10 h-10 rounded-md text-ink-muted hover:text-ink hover:bg-bg-sunk transition-colors"
          >
            <Settings size={18} strokeWidth={1.6} />
          </Link>
          {hoveredItem === "settings" && (
            <div className="absolute left-full ml-3 top-1/2 -translate-y-1/2 bg-ink text-bg text-xs font-medium px-2.5 py-1.5 rounded-[3px] whitespace-nowrap shadow-md pointer-events-none z-[100] font-mono tracking-[0.02em]">
              Settings
            </div>
          )}
        </div>

        <UserButton
          appearance={{
            elements: {
              avatarBox: "w-7 h-7 border border-line-strong",
            },
          }}
        />
      </div>
    </aside>
  );
}
