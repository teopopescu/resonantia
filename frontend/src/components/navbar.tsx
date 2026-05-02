"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X } from "lucide-react";
import { cn } from "@/lib/utils";

const navLinks = [
  { label: "About", href: "/about" },
  { label: "Features", href: "/features" },
  { label: "Use cases", href: "/use-cases" },
  { label: "Pricing", href: "/pricing" },
  { label: "Blog", href: "/blog" },
];

/**
 * Brand mark — 4-cell illuminated well.
 * Plate-as-identity, works at every size from 16px favicon up.
 */
function BrandMark({ className = "" }: { className?: string }) {
  return (
    <span
      className={cn(
        "inline-grid grid-cols-2 grid-rows-2 gap-[3px] p-[4px] rounded-[4px] bg-surface border border-line-strong",
        className
      )}
      style={{ width: 26, height: 26 }}
      aria-hidden="true"
    >
      <span className="rounded-full bg-ink-subtle" />
      <span className="rounded-full bg-ink-subtle" />
      <span className="rounded-full bg-ink-subtle" />
      <span className="rounded-full bg-brand" />
    </span>
  );
}

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <motion.header
      initial={{ y: -10, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
        scrolled
          ? "bg-bg/85 backdrop-blur-md border-b border-line"
          : "bg-bg border-b border-transparent"
      )}
    >
      <nav className="max-w-7xl mx-auto px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-3 group">
          <BrandMark />
          <span className="text-[17px] font-semibold tracking-[-0.02em] text-ink">
            Resonantia
          </span>
        </Link>

        {/* Desktop links */}
        <div className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <a
              key={link.label}
              href={link.href}
              className="text-[13.5px] text-ink-muted hover:text-ink transition-colors duration-200"
            >
              {link.label}
            </a>
          ))}
        </div>

        {/* Auth + CTA */}
        <div className="hidden md:flex items-center gap-2">
          <Link
            href="/lab"
            className="text-[13.5px] px-3 py-2 text-ink-muted hover:text-ink transition-colors"
          >
            Sign in
          </Link>
          <a
            href="mailto:hello@resonantia.io?subject=Resonantia · contact"
            className="inline-flex items-center gap-2 px-4 py-2 bg-brand text-white text-[13.5px] font-medium rounded-[3px] hover:bg-brand-strong transition-colors duration-200"
            style={{ boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.06)" }}
          >
            Contact us
            <span className="font-mono text-[13px] leading-none">→</span>
          </a>
        </div>

        {/* Mobile menu button */}
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="md:hidden p-2 text-ink"
          aria-label="Toggle menu"
        >
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </nav>

      {/* Mobile menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25 }}
            className="md:hidden bg-bg/95 backdrop-blur-md border-b border-line overflow-hidden"
          >
            <div className="px-6 py-6 flex flex-col gap-4">
              {navLinks.map((link) => (
                <a
                  key={link.label}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                  className="text-base text-ink-muted hover:text-ink transition-colors"
                >
                  {link.label}
                </a>
              ))}
              <Link
                href="/lab"
                onClick={() => setMobileOpen(false)}
                className="text-base text-ink-muted hover:text-ink transition-colors"
              >
                Sign in
              </Link>
              <a
                href="mailto:hello@resonantia.io?subject=Resonantia · contact"
                onClick={() => setMobileOpen(false)}
                className="inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-brand text-white text-sm font-medium rounded-[3px] mt-2"
              >
                Contact us →
              </a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  );
}
