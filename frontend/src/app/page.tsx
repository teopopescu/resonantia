"use client";

import { Navbar } from "@/components/navbar";
import { Hero } from "@/components/hero";
import { ConsolePreview } from "@/components/console-preview";
import { Features } from "@/components/features";
import { Testimonials } from "@/components/testimonials";
import { CtaSection } from "@/components/cta-section";
import { Footer } from "@/components/footer";

export default function Home() {
  return (
    <>
      <Navbar />
      {/* Spacer matching the fixed-nav height */}
      <div className="h-16" />
      <main>
        <Hero />
        <ConsolePreview />
        <Features />
        <Testimonials />
        <CtaSection />
      </main>
      <Footer />
    </>
  );
}
