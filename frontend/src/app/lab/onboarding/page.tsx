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
import { cn } from "@/lib/utils";

interface Option {
  id: string;
  label: string;
  description: string;
  icon: React.ReactNode;
}

const ROLES: Option[] = [
  {
    id: "scientist",
    label: "Scientist",
    description: "I run experiments and analyze data at the bench.",
    icon: <FlaskRound size={22} />,
  },
  {
    id: "lab_manager",
    label: "Lab manager",
    description: "I oversee operations, inventory, and compliance.",
    icon: <Users size={22} />,
  },
  {
    id: "bioinformatician",
    label: "Bioinformatician",
    description: "I process experimental data computationally.",
    icon: <Dna size={22} />,
  },
  {
    id: "other",
    label: "Other",
    description: "Something else.",
    icon: <HelpCircle size={22} />,
  },
];

const FOCUS_AREAS: Option[] = [
  {
    id: "plate_assays",
    label: "Plate-based assays",
    description: "Dose-response, HTS, screening.",
    icon: <LayoutGrid size={22} />,
  },
  {
    id: "microscopy",
    label: "Microscopy",
    description: "Fluorescence imaging, high-content screening.",
    icon: <Eye size={22} />,
  },
  {
    id: "qpcr",
    label: "qPCR",
    description: "Gene expression, ΔΔCt analysis.",
    icon: <Dna size={22} />,
  },
  {
    id: "sample_management",
    label: "Sample management",
    description: "Reagent tracking, inventory, barcodes.",
    icon: <FlaskConical size={22} />,
  },
];

const FEATURE_HINTS: Record<
  string,
  { code: string; title: string; description: string; icon: React.ReactNode }
> = {
  plate_assays: {
    code: "PLT/01",
    title: "Plate Mapping",
    description:
      "Source-destination layouts. Echo, Hamilton, OT-2 worklists in one click.",
    icon: <LayoutGrid size={18} />,
  },
  microscopy: {
    code: "MIC/02",
    title: "Microscopy Browser",
    description:
      "Browse FOVs by plate, well, and channel. DAPI · GFP · mCherry overlays.",
    icon: <Microscope size={18} />,
  },
  qpcr: {
    code: "DAT/03",
    title: "qPCR Analysis",
    description: "ΔΔCt with reference gene and control sample.",
    icon: <Dna size={18} />,
  },
  sample_management: {
    code: "INV/04",
    title: "Sample Tracking",
    description:
      "Every lot, every aliquot, every freeze-thaw. Barcode-first.",
    icon: <FlaskConical size={18} />,
  },
};

const pageVariants = {
  enter: (direction: number) => ({ x: direction > 0 ? 200 : -200, opacity: 0 }),
  center: { x: 0, opacity: 1 },
  exit: (direction: number) => ({ x: direction > 0 ? -200 : 200, opacity: 0 }),
};

const pageTransition = { type: "spring" as const, stiffness: 300, damping: 30 };

function BrandMark({ size = 44 }: { size?: number }) {
  return (
    <span
      className="inline-grid grid-cols-2 grid-rows-2 gap-[3px] p-[6px] rounded-[5px] bg-surface border border-line-strong"
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

function PrimaryButton({
  children,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className={cn(
        "inline-flex items-center gap-2 px-5 py-2.5 bg-brand text-white text-[13.5px] font-medium rounded-[3px] hover:bg-brand-strong transition-colors disabled:opacity-40 disabled:cursor-not-allowed",
        props.className
      )}
      style={{
        boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.06)",
        ...props.style,
      }}
    >
      {children}
    </button>
  );
}

function GhostButton({
  children,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className={cn(
        "px-3 py-2.5 text-[13px] text-ink-muted hover:text-ink transition-colors",
        props.className
      )}
    >
      {children}
    </button>
  );
}

function OptionCard({
  option,
  selected,
  onClick,
}: {
  option: Option;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "relative flex flex-col items-start p-5 rounded-[5px] border text-left transition-colors",
        selected
          ? "border-brand bg-brand-soft/40"
          : "border-line bg-surface hover:border-line-strong"
      )}
    >
      {selected && (
        <div className="absolute top-3 right-3 w-5 h-5 rounded-[2px] bg-brand flex items-center justify-center">
          <Check size={11} className="text-white" />
        </div>
      )}
      <div
        className={cn(
          "mb-3 transition-colors",
          selected ? "text-brand" : "text-ink-muted"
        )}
      >
        {option.icon}
      </div>
      <span className="font-medium text-ink text-[14.5px]">
        {option.label}
      </span>
      <span className="text-ink-muted text-[12.5px] leading-relaxed mt-1">
        {option.description}
      </span>
    </button>
  );
}

export default function OnboardingPage() {
  const router = useRouter();
  const { user } = useUser();
  const setOnboardingCompleted = useOnboardingStore(
    (s) => s.setOnboardingCompleted
  );
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
      setOnboardingCompleted(true);
      router.push("/lab");
    }
  }

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
            <div className="mb-8">
              <BrandMark size={48} />
            </div>
            <div className="font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle mb-3">
              <span className="text-brand">›</span> setup · ~30 seconds
            </div>
            <h1 className="text-[42px] font-bold tracking-[-0.035em] leading-[1.05] text-ink mb-3">
              Welcome to <span className="text-brand">Resonantia.</span>
            </h1>
            <p className="text-ink-muted text-[16px] leading-relaxed mb-10">
              Let&apos;s set up your workspace. Two questions, one summary.
            </p>
            <PrimaryButton onClick={goNext}>
              Get started
              <ArrowRight size={15} />
            </PrimaryButton>
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
            <div className="text-center mb-8">
              <div className="font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle mb-3">
                <span className="text-brand">›</span> 01 / 03 · role
              </div>
              <h2 className="text-[32px] font-bold tracking-[-0.025em] leading-[1.1] text-ink mb-2">
                What&apos;s your role?
              </h2>
              <p className="text-ink-muted text-[14.5px]">
                This helps us tailor what shows up first.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-8">
              {ROLES.map((role) => (
                <OptionCard
                  key={role.id}
                  option={role}
                  selected={selectedRole === role.id}
                  onClick={() => setSelectedRole(role.id)}
                />
              ))}
            </div>

            <div className="flex justify-between">
              <GhostButton onClick={goBack}>← Back</GhostButton>
              <PrimaryButton onClick={goNext} disabled={!selectedRole}>
                Continue
                <ArrowRight size={14} />
              </PrimaryButton>
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
            <div className="text-center mb-8">
              <div className="font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle mb-3">
                <span className="text-brand">›</span> 02 / 03 · focus areas
              </div>
              <h2 className="text-[32px] font-bold tracking-[-0.025em] leading-[1.1] text-ink mb-2">
                What do you work with most?
              </h2>
              <p className="text-ink-muted text-[14.5px]">
                Select all that apply. You can change this later.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-8">
              {FOCUS_AREAS.map((area) => (
                <OptionCard
                  key={area.id}
                  option={area}
                  selected={selectedFocus.has(area.id)}
                  onClick={() => toggleFocus(area.id)}
                />
              ))}
            </div>

            <div className="flex justify-between">
              <GhostButton onClick={goBack}>← Back</GhostButton>
              <PrimaryButton
                onClick={goNext}
                disabled={selectedFocus.size === 0}
              >
                Continue
                <ArrowRight size={14} />
              </PrimaryButton>
            </div>
          </motion.div>
        );

      case 3: {
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
            <div className="text-center mb-8">
              <div className="font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle mb-3">
                <span className="text-brand">›</span> 03 / 03 · ready
              </div>
              <h2 className="text-[32px] font-bold tracking-[-0.025em] leading-[1.1] text-ink mb-2">
                Your workspace is <span className="text-brand">ready.</span>
              </h2>
              <p className="text-ink-muted text-[14.5px]">
                These modules are wired and waiting on the rail.
              </p>
            </div>

            <div className="space-y-2 mb-4">
              {featureCards.map((feat, i) => (
                <motion.div
                  key={feat.code}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.08 }}
                  className="flex items-start gap-3 px-4 py-3 rounded-[5px] bg-surface border border-line"
                >
                  <span className="font-mono text-[10px] tracking-[0.04em] uppercase text-brand bg-brand-soft border border-brand/40 rounded-[2px] px-1.5 py-0.5 mt-0.5">
                    {feat.code}
                  </span>
                  <div className="text-brand mt-0.5 shrink-0">{feat.icon}</div>
                  <div className="min-w-0">
                    <p className="font-medium text-ink text-[13.5px]">
                      {feat.title}
                    </p>
                    <p className="font-mono text-[11px] text-ink-muted mt-1 leading-relaxed">
                      {feat.description}
                    </p>
                  </div>
                </motion.div>
              ))}

              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: featureCards.length * 0.08 }}
                className="flex items-start gap-3 px-4 py-3 rounded-[5px] bg-surface border border-line"
              >
                <span className="font-mono text-[10px] tracking-[0.04em] uppercase text-brand bg-brand-soft border border-brand/40 rounded-[2px] px-1.5 py-0.5 mt-0.5">
                  AGT/05
                </span>
                <div className="text-brand mt-0.5 shrink-0">
                  <Bot size={18} />
                </div>
                <div className="min-w-0">
                  <p className="font-medium text-ink text-[13.5px]">
                    Agent Console
                  </p>
                  <p className="font-mono text-[11px] text-ink-muted mt-1 leading-relaxed">
                    Natural-language access to all 32 tools. Cited traces for
                    every action.
                  </p>
                </div>
              </motion.div>
            </div>

            <div className="flex justify-between mt-8">
              <GhostButton onClick={goBack}>← Back</GhostButton>
              <PrimaryButton onClick={handleComplete} disabled={submitting}>
                {submitting ? (
                  <>
                    <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Setting up…
                  </>
                ) : (
                  <>
                    Open the lab
                    <Sparkles size={14} />
                  </>
                )}
              </PrimaryButton>
            </div>
          </motion.div>
        );
      }

      default:
        return null;
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 py-12 bg-bg">
      {/* Progress dots */}
      <div className="flex items-center gap-2 mb-12">
        {Array.from({ length: totalSteps }).map((_, i) => (
          <div
            key={i}
            className={cn(
              "h-1 rounded-full transition-all duration-300",
              i === step
                ? "w-8 bg-brand"
                : i < step
                ? "w-3 bg-brand/40"
                : "w-3 bg-line-strong"
            )}
          />
        ))}
      </div>

      <div
        className="w-full max-w-2xl relative"
        style={{ minHeight: 440 }}
      >
        <AnimatePresence mode="wait" custom={direction}>
          {renderStep()}
        </AnimatePresence>
      </div>
    </div>
  );
}
