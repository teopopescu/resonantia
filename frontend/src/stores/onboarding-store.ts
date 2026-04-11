import { create } from "zustand";
import { persist } from "zustand/middleware";

interface OnboardingState {
  onboardingCompleted: boolean;
  role: string | null;
  focusAreas: string[];
  setOnboardingCompleted: (completed: boolean) => void;
  setRole: (role: string) => void;
  setFocusAreas: (areas: string[]) => void;
  reset: () => void;
}

export const useOnboardingStore = create<OnboardingState>()(
  persist(
    (set) => ({
      onboardingCompleted: false,
      role: null,
      focusAreas: [],
      setOnboardingCompleted: (completed) => set({ onboardingCompleted: completed }),
      setRole: (role) => set({ role }),
      setFocusAreas: (areas) => set({ focusAreas: areas }),
      reset: () => set({ onboardingCompleted: false, role: null, focusAreas: [] }),
    }),
    {
      name: "resonantia-onboarding",
    }
  )
);
