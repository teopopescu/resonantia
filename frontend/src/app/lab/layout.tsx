"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useUser, useOrganization } from "@clerk/nextjs";
import Sidebar from "@/components/lab/sidebar";
import TaskPanel from "@/components/lab/task-panel";
import { useLabStore } from "@/stores/lab-store";
import { useOnboardingStore } from "@/stores/onboarding-store";
import { api, setActiveOrgId } from "@/lib/api";
import { ChevronRight } from "lucide-react";

export default function LabLayout({ children }: { children: React.ReactNode }) {
  const sidebarCollapsed = useLabStore((s) => s.sidebarCollapsed);
  const toggleSidebar = useLabStore((s) => s.toggleSidebar);
  const fetchConversations = useLabStore((s) => s.fetchConversations);
  const onboardingCompleted = useOnboardingStore((s) => s.onboardingCompleted);
  const setOnboardingCompleted = useOnboardingStore((s) => s.setOnboardingCompleted);

  const { user, isLoaded } = useUser();
  const { organization, isLoaded: orgLoaded } = useOrganization();
  const router = useRouter();
  const pathname = usePathname();
  const [checking, setChecking] = useState(true);

  const isOnboardingRoute = pathname.startsWith("/lab/onboarding");

  // Set active org from Clerk
  useEffect(() => {
    if (organization?.id) {
      setActiveOrgId(organization.id);
    }
  }, [organization]);

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
      <div className="flex h-screen w-screen items-center justify-center bg-cream">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-charcoal flex items-center justify-center">
            <span className="text-amber font-serif text-lg font-bold">R</span>
          </div>
          <div className="w-5 h-5 border-2 border-amber/30 border-t-amber rounded-full animate-spin" />
        </div>
      </div>
    );
  }

  // No organization — user has no access
  if (!organization && orgLoaded && isLoaded) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-cream">
        <div className="flex flex-col items-center gap-4 max-w-md text-center px-6">
          <div className="w-16 h-16 rounded-2xl bg-charcoal flex items-center justify-center mb-2">
            <span className="text-amber font-serif text-2xl font-bold">R</span>
          </div>
          <h1 className="font-serif text-2xl font-semibold text-charcoal">
            No access
          </h1>
          <p className="text-muted leading-relaxed">
            You need to be part of an organization to access Resonantia Lab.
            Ask your administrator for an invitation, or contact us at{" "}
            <a href="mailto:hello@resonantia.io" className="text-amber hover:underline">
              hello@resonantia.io
            </a>
          </p>
          <a
            href="/"
            className="mt-4 px-6 py-2.5 bg-charcoal text-cream text-sm font-medium rounded-xl hover:bg-charcoal-light transition-colors"
          >
            Back to home
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-cream">
      {/* Icon sidebar */}
      <Sidebar />

      {/* Task panel */}
      <TaskPanel />

      {/* Collapse toggle (visible when panel is collapsed) */}
      {sidebarCollapsed && (
        <button
          onClick={toggleSidebar}
          className="shrink-0 flex items-center justify-center w-5 bg-surface border-r border-border text-muted hover:text-charcoal transition-colors"
        >
          <ChevronRight size={14} />
        </button>
      )}

      {/* Main content area */}
      <main className="flex-1 flex flex-col min-w-0 bg-surface">{children}</main>
    </div>
  );
}
