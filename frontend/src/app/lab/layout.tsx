"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth, useUser, useOrganization } from "@clerk/nextjs";
import Sidebar from "@/components/lab/sidebar";
import TaskPanel from "@/components/lab/task-panel";
import DemoBanner from "@/components/lab/demo-banner";
import { useLabStore } from "@/stores/lab-store";
import { useOnboardingStore } from "@/stores/onboarding-store";
import { api, setActiveOrgId, setAuthToken } from "@/lib/api";
import { isDemoMode, initDemoMode } from "@/lib/demo-mode";
import { ChevronRight } from "lucide-react";

export default function LabLayout({ children }: { children: React.ReactNode }) {
  const sidebarCollapsed = useLabStore((s) => s.sidebarCollapsed);
  const toggleSidebar = useLabStore((s) => s.toggleSidebar);
  const fetchConversations = useLabStore((s) => s.fetchConversations);
  const onboardingCompleted = useOnboardingStore((s) => s.onboardingCompleted);
  const setOnboardingCompleted = useOnboardingStore((s) => s.setOnboardingCompleted);

  const { user, isLoaded } = useUser();
  const { getToken } = useAuth();
  const { organization, isLoaded: orgLoaded } = useOrganization();
  const router = useRouter();
  const pathname = usePathname();
  const [checking, setChecking] = useState(true);
  const [demoActive, setDemoActive] = useState(false);
  const [toasts, setToasts] = useState<string[]>([]);

  const isOnboardingRoute = pathname.startsWith("/lab/onboarding");

  useEffect(() => {
    initDemoMode().then(() => setDemoActive(isDemoMode()));
  }, []);

  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail;
      if (detail?.message) {
        setToasts((prev) => [...prev.slice(-4), detail.message]);
        setTimeout(() => setToasts((prev) => prev.slice(1)), 5000);
      }
    };
    window.addEventListener("resonantia:toast", handler);
    return () => window.removeEventListener("resonantia:toast", handler);
  }, []);

  // Set active org from Clerk
  useEffect(() => {
    if (organization?.id) {
      setActiveOrgId(organization.id);
    }
  }, [organization]);

  useEffect(() => {
    let cancelled = false;
    getToken().then((token) => {
      if (!cancelled) setAuthToken(token);
    });
    return () => {
      cancelled = true;
    };
  }, [getToken, user?.id, organization?.id]);

  // Fetch conversations once org context is ready
  useEffect(() => {
    if (!isOnboardingRoute && !checking && user?.id) {
      fetchConversations(user.id);
    }
  }, [isOnboardingRoute, checking, user, fetchConversations]);

  useEffect(() => {
    // Skip the check if we're already on the onboarding page
    if (isOnboardingRoute) {
      setChecking(false);
      return;
    }

    // If the local store already says completed, trust it
    if (onboardingCompleted) {
      setChecking(false);
      return;
    }

    // Wait for Clerk to load
    if (!isLoaded || !user) return;

    let cancelled = false;

    async function checkOnboarding() {
      try {
        const res = await api<{ onboarding_completed: boolean }>(
          `/api/v1/onboarding/check/${user!.id}`
        );
        if (cancelled) return;
        if (res.onboarding_completed) {
          setOnboardingCompleted(true);
          setChecking(false);
        } else {
          router.replace("/lab/onboarding");
        }
      } catch {
        // On error, allow through rather than blocking
        setChecking(false);
      }
    }

    checkOnboarding();
    return () => {
      cancelled = true;
    };
  }, [isLoaded, user, onboardingCompleted, isOnboardingRoute, router, setOnboardingCompleted]);

  // If on the onboarding route, render only the children (onboarding layout handles its own wrapper)
  if (isOnboardingRoute) {
    return <>{children}</>;
  }

  // Loading state while checking
  if (checking || !isLoaded || !orgLoaded) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-bg">
        <div className="flex flex-col items-center gap-5">
          <span
            className="inline-grid grid-cols-2 grid-rows-2 gap-[3px] p-[5px] rounded-[5px] bg-surface border border-line-strong"
            style={{ width: 36, height: 36 }}
            aria-hidden="true"
          >
            <span className="rounded-full bg-ink-subtle" />
            <span className="rounded-full bg-ink-subtle" />
            <span className="rounded-full bg-ink-subtle" />
            <span className="rounded-full bg-brand" />
          </span>
          <div className="w-4 h-4 border-2 border-line border-t-brand rounded-full animate-spin" />
        </div>
      </div>
    );
  }

  // No organization — user has no access
  if (!organization && orgLoaded && isLoaded) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-bg">
        <div className="flex flex-col items-center gap-5 max-w-md text-center px-6">
          <span
            className="inline-grid grid-cols-2 grid-rows-2 gap-[3px] p-[6px] rounded-[5px] bg-surface border border-line-strong"
            style={{ width: 44, height: 44 }}
            aria-hidden="true"
          >
            <span className="rounded-full bg-ink-subtle" />
            <span className="rounded-full bg-ink-subtle" />
            <span className="rounded-full bg-ink-subtle" />
            <span className="rounded-full bg-brand" />
          </span>
          <h1 className="text-2xl font-semibold tracking-[-0.02em] text-ink">
            No access
          </h1>
          <p className="text-ink-muted leading-relaxed text-[15px]">
            You need to be part of an organization to access Resonantia Lab.
            Ask your administrator for an invitation, or contact us at{" "}
            <a
              href="mailto:hello@resonantia.io"
              className="text-brand hover:underline underline-offset-2"
            >
              hello@resonantia.io
            </a>
            .
          </p>
          <a
            href="/"
            className="mt-2 inline-flex items-center gap-2 px-5 py-2.5 bg-brand text-white text-sm font-medium rounded-[3px] hover:bg-brand-strong transition-colors"
            style={{ boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.06)" }}
          >
            Back to home
            <span className="font-mono text-[14px] leading-none">→</span>
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-bg">
      {/* Icon sidebar */}
      <Sidebar />

      {/* Task panel */}
      <TaskPanel />

      {/* Collapse toggle (visible when panel is collapsed) */}
      {sidebarCollapsed && (
        <button
          onClick={toggleSidebar}
          className="shrink-0 flex items-center justify-center w-5 bg-bg border-r border-line text-ink-muted hover:text-ink transition-colors"
        >
          <ChevronRight size={14} />
        </button>
      )}

      {/* Main content area */}
      <main className="flex-1 flex flex-col min-w-0 bg-surface">
        {demoActive && (
          <DemoBanner />
        )}
        {children}
      </main>

      {/* Error toasts */}
      {toasts.length > 0 && (
        <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
          {toasts.map((msg, i) => (
            <div
              key={i}
              className="bg-red-50 border border-red-200 text-red-800 text-sm px-4 py-3 rounded-md shadow-md max-w-sm animate-in fade-in slide-in-from-bottom-2"
            >
              {msg}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
