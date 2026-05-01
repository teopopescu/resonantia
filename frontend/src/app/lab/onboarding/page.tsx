"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useUser } from "@clerk/nextjs";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutGrid,
  Eye,
  Dna,
  FlaskConical,
  FlaskRound,
  Microscope,
  Users,
  HelpCircle,
  Sparkles,
  ArrowRight,
  Check,
  Bot,
} from "lucide-react";
import { api } from "@/lib/api";
import { useOnboardingStore } from "@/stores/onboarding-store";

/* ── Types ── */
interface RoleOption {
  id: string;
  label: string;
  description: string;
  icon: React.ReactNode;
}

interface FocusOption {
  id: string;
  label: string;
  description: string;
  icon: React.ReactNode;
}

/* ── Static data ── */
const ROLES: RoleOption[] = [
  {
    id: "scientist",
    label: "Scientist",
    description: "I run experiments and analyze data at the bench",
    icon: <FlaskRound size={24} />,
  },
  {
    id: "lab_manager",
    label: "Lab Manager",
    description: "I oversee lab operations, inventory, and compliance",
    icon: <Users size={24} />,
  },
  {
    id: "bioinformatician",
    label: "Bioinformatician",
    description: "I analyze and process experimental data computationally",
    icon: <Dna size={24} />,
  },
  {
    id: "other",
    label: "Other",
    description: "Something else",
    icon: <HelpCircle size={24} />,
  },
];

const FOCUS_AREAS: FocusOption[] = [
  {
    id: "plate_assays",
    label: "Plate-based assays",
    description: "Dose-response, HTS, screening",
    icon: <LayoutGrid size={24} />,
  },
  {
    id: "microscopy",
    label: "Microscopy",
    description: "Fluorescence imaging, high-content screening",
    icon: <Eye size={24} />,
  },
  {
    id: "qpcr",
    label: "qPCR",
    description: "Gene expression, delta-delta Ct analysis",
    icon: <Dna size={24} />,
  },
  {
    id: "sample_management",
    label: "Sample management",
    description: "Reagent tracking, inventory, barcodes",
    icon: <FlaskConical size={24} />,
  },
];

const FEATURE_HINTS: Record<string, { title: string; description: string; icon: React.ReactNode }> = {
  plate_assays: {
    title: "Plate Mapping",
    description: "Design plate maps and generate Echo/Hamilton worklists in seconds",
    icon: <LayoutGrid size={20} className="text-amber" />,
  },
  microscopy: {
    title: "Microscopy Viewer",
    description: "Browse FOV images by plate, well, and channel with composite overlays",
    icon: <Microscope size={20} className="text-amber" />,
  },
  qpcr: {
    title: "qPCR Analysis",
    description: "Run delta-delta Ct analysis with automated fold-change calculation",
    icon: <Dna size={20} className="text-amber" />,
  },
  sample_management: {
    title: "Sample Tracking",
    description: "Track every reagent lot, storage location, and expiry date",
    icon: <FlaskConical size={20} className="text-amber" />,
  },
};

/* ── Animation variants ── */
const pageVariants = {
  enter: (direction: number) => ({ x: direction > 0 ? 300 : -300, opacity: 0 }),
  center: { x: 0, opacity: 1 },
  exit: (direction: number) => ({ x: direction > 0 ? -300 : 300, opacity: 0 }),
};

const pageTransition = { type: "spring" as const, stiffness: 300, damping: 30 };

/* ── Component ── */
export default function OnboardingPage() {
  const router = useRouter();
  const { user } = useUser();
  const setOnboardingCompleted = useOnboardingStore((s) => s.setOnboardingCompleted);
  const storeSetRole = useOnboardingStore((s) => s.setRole);
  const storeSetFocusAreas = useOnboardingStore((s) => s.setFocusAreas);

  const [step, setStep] = useState(0);
  const [direction, setDirection] = useState(1);
  const [selectedRole, setSelectedRole] = useState<string | null>(null);
  const [selectedFocus, setSelectedFocus] = useState<Set<string>>(new Set());
  const [submitting, setSubmitting] = useState(false);

  const totalSteps = 4;

  function goNext() {
    setDirection(1);
    setStep((s) => Math.min(s + 1, totalSteps - 1));
  }

  function goBack() {
    setDirection(-1);
    setStep((s) => Math.max(s - 1, 0));
  }

  function toggleFocus(id: string) {
    setSelectedFocus((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function handleComplete() {
    if (!user) return;
    setSubmitting(true);
    try {
      await api("/api/v1/onboarding/complete", {
        method: "POST",
        body: JSON.stringify({
          clerk_user_id: user.id,
          email: user.primaryEmailAddress?.emailAddress ?? null,
          name: user.fullName ?? user.firstName ?? null,
          role: selectedRole,
          focus_areas: Array.from(selectedFocus),
        }),
      });
      setOnboardingCompleted(true);
      storeSetRole(selectedRole!);
      storeSetFocusAreas(Array.from(selectedFocus));
      router.push("/lab");
    } catch (err) {
      console.error("Onboarding error:", err);
      // Still redirect - onboarding is not critical
      setOnboardingCompleted(true);
      router.push("/lab");
    }
  }

  /* ── Render steps ── */
  function renderStep() {
    switch (step) {
      case 0:
        return (
          <motion.div
            key="step-0"
            custom={direction}
            variants={pageVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={pageTransition}
            className="flex flex-col items-center text-center max-w-lg mx-auto"
          >
            {/* Logo mark */}
            <div className="w-16 h-16 rounded-2xl bg-charcoal flex items-center justify-center mb-8">
              <span className="text-amber font-serif text-2xl font-bold">R</span>
            </div>

            <h1 className="font-serif text-4xl text-charcoal mb-3">
              Welcome to Resonantia Lab
            </h1>
            <p className="text-muted text-lg mb-10 leading-relaxed">
              Let&apos;s set up your experience. This takes about 30 seconds.
            </p>

            <button
              onClick={goNext}
              className="group inline-flex items-center gap-2 px-8 py-3.5 bg-charcoal text-cream rounded-xl font-medium text-base hover:bg-charcoal-light transition-colors"
            >
              Get started
              <ArrowRight
                size={18}
                className="group-hover:translate-x-0.5 transition-transform"
              />
            </button>
          </motion.div>
        );

      case 1:
        return (
          <motion.div
            key="step-1"
            custom={direction}
            variants={pageVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={pageTransition}
            className="max-w-2xl mx-auto w-full"
          >
            <h2 className="font-serif text-3xl text-charcoal mb-2 text-center">
              What&apos;s your role?
            </h2>
            <p className="text-muted text-center mb-8">
              This helps us tailor your experience.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
              {ROLES.map((role) => {
                const selected = selectedRole === role.id;
                return (
                  <button
                    key={role.id}
                    onClick={() => setSelectedRole(role.id)}
                    className={`relative flex flex-col items-start p-5 rounded-xl border-2 text-left transition-all ${
                      selected
                        ? "border-amber bg-amber/5 shadow-sm"
                        : "border-border bg-surface hover:border-amber/40"
                    }`}
                  >
                    {selected && (
                      <div className="absolute top-3 right-3 w-5 h-5 rounded-full bg-amber flex items-center justify-center">
                        <Check size={12} className="text-white" />
                      </div>
                    )}
                    <div
                      className={`mb-3 ${selected ? "text-amber" : "text-muted"}`}
                    >
                      {role.icon}
                    </div>
                    <span className="font-medium text-charcoal text-base">
                      {role.label}
                    </span>
                    <span className="text-muted text-sm mt-1">
                      {role.description}
                    </span>
                  </button>
                );
              })}
            </div>

            <div className="flex justify-between">
              <button
                onClick={goBack}
                className="px-6 py-2.5 text-muted hover:text-charcoal transition-colors text-sm"
              >
                Back
              </button>
              <button
                onClick={goNext}
                disabled={!selectedRole}
                className="px-8 py-2.5 bg-charcoal text-cream rounded-xl font-medium text-sm disabled:opacity-30 disabled:cursor-not-allowed hover:bg-charcoal-light transition-colors"
              >
                Continue
              </button>
            </div>
          </motion.div>
        );

      case 2:
        return (
          <motion.div
            key="step-2"
            custom={direction}
            variants={pageVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={pageTransition}
            className="max-w-2xl mx-auto w-full"
          >
            <h2 className="font-serif text-3xl text-charcoal mb-2 text-center">
              What do you work with most?
            </h2>
            <p className="text-muted text-center mb-8">
              Select all that apply. You can change this later.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
              {FOCUS_AREAS.map((area) => {
                const selected = selectedFocus.has(area.id);
                return (
                  <button
                    key={area.id}
                    onClick={() => toggleFocus(area.id)}
                    className={`relative flex flex-col items-start p-5 rounded-xl border-2 text-left transition-all ${
                      selected
                        ? "border-amber bg-amber/5 shadow-sm"
                        : "border-border bg-surface hover:border-amber/40"
                    }`}
                  >
                    {selected && (
                      <div className="absolute top-3 right-3 w-5 h-5 rounded-full bg-amber flex items-center justify-center">
                        <Check size={12} className="text-white" />
                      </div>
                    )}
                    <div
                      className={`mb-3 ${selected ? "text-amber" : "text-muted"}`}
                    >
                      {area.icon}
                    </div>
                    <span className="font-medium text-charcoal text-base">
                      {area.label}
                    </span>
                    <span className="text-muted text-sm mt-1">
                      {area.description}
                    </span>
                  </button>
                );
              })}
            </div>

            <div className="flex justify-between">
              <button
                onClick={goBack}
                className="px-6 py-2.5 text-muted hover:text-charcoal transition-colors text-sm"
              >
                Back
              </button>
              <button
                onClick={goNext}
                disabled={selectedFocus.size === 0}
                className="px-8 py-2.5 bg-charcoal text-cream rounded-xl font-medium text-sm disabled:opacity-30 disabled:cursor-not-allowed hover:bg-charcoal-light transition-colors"
              >
                Continue
              </button>
            </div>
          </motion.div>
        );

      case 3: {
        // Build feature cards based on selection
        const featureCards = Array.from(selectedFocus)
          .filter((id) => FEATURE_HINTS[id])
          .map((id) => FEATURE_HINTS[id]);

        return (
          <motion.div
            key="step-3"
            custom={direction}
            variants={pageVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={pageTransition}
            className="max-w-2xl mx-auto w-full"
          >
            <h2 className="font-serif text-3xl text-charcoal mb-2 text-center">
              Here&apos;s what you can do
            </h2>
            <p className="text-muted text-center mb-8">
              Your workspace is ready with these capabilities.
            </p>

            <div className="space-y-3 mb-4">
              {featureCards.map((feat, i) => (
                <motion.div
                  key={feat.title}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="flex items-start gap-4 p-4 rounded-xl bg-surface border border-border"
                >
                  <div className="mt-0.5 shrink-0">{feat.icon}</div>
                  <div>
                    <p className="font-medium text-charcoal text-sm">
                      {feat.title}
                    </p>
                    <p className="text-muted text-sm mt-0.5">
                      {feat.description}
                    </p>
                  </div>
                </motion.div>
              ))}

              {/* Always show AI assistant */}
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: featureCards.length * 0.1 }}
                className="flex items-start gap-4 p-4 rounded-xl bg-surface border border-border"
              >
                <div className="mt-0.5 shrink-0">
                  <Bot size={20} className="text-amber" />
                </div>
                <div>
                  <p className="font-medium text-charcoal text-sm">
                    AI Assistant
                  </p>
                  <p className="text-muted text-sm mt-0.5">
                    Ask the AI assistant anything about your lab workflows
                  </p>
                </div>
              </motion.div>
            </div>

            <div className="flex justify-between mt-8">
              <button
                onClick={goBack}
                className="px-6 py-2.5 text-muted hover:text-charcoal transition-colors text-sm"
              >
                Back
              </button>
              <button
                onClick={handleComplete}
                disabled={submitting}
                className="group inline-flex items-center gap-2 px-8 py-3 bg-amber text-charcoal rounded-xl font-medium text-sm hover:bg-amber-light transition-colors disabled:opacity-50"
              >
                {submitting ? (
                  <>
                    <span className="w-4 h-4 border-2 border-charcoal/30 border-t-charcoal rounded-full animate-spin" />
                    Setting up...
                  </>
                ) : (
                  <>
                    Enter Resonantia Lab
                    <Sparkles
                      size={16}
                      className="group-hover:rotate-12 transition-transform"
                    />
                  </>
                )}
              </button>
            </div>
          </motion.div>
        );
      }

      default:
        return null;
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 py-12">
      {/* Progress dots */}
      <div className="flex items-center gap-2 mb-12">
        {Array.from({ length: totalSteps }).map((_, i) => (
          <div
            key={i}
            className={`h-1.5 rounded-full transition-all duration-300 ${
              i === step
                ? "w-8 bg-amber"
                : i < step
                  ? "w-3 bg-amber/40"
                  : "w-3 bg-border"
            }`}
          />
        ))}
      </div>

      {/* Step content */}
      <div className="w-full max-w-2xl relative" style={{ minHeight: 400 }}>
        <AnimatePresence mode="wait" custom={direction}>
          {renderStep()}
        </AnimatePresence>
      </div>
    </div>
  );
}
